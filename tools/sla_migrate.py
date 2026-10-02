#!/usr/bin/env python3
"""Offline SLA v4 symbol/template migration into owned FSL, with refusals.

No Sleigh runtime or source grammar is used. The admitted semantic registry is
BUILD of a pure register export followed by a handle-based INT_ADD. This is a
bounded migration slice, not a full SLA interpreter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

from fsl_migrate import MigrationError, SNAPSHOT, evidence, provenance, quote
from sla_probe import SlaError, inspect

# Wire-format identifiers are facts from versioned Ghidra slaformat.cc.
REGISTRY = {"format_version": 4, "opcodes": {"19": "integer_add_wrap", "60": "build_operand_export"},
            "opcode_scope": "Sleigh ConstructTpl only; opcode 60 is BUILD directive here, not an executable phi operation",
            "supported_template_atoms": ["real", "spaceid", "handle(space,offset,size)"],
            "refused_effects": ["context", "commit", "sections", "delay", "labels", "memory", "branch", "userop", "dynamic_handle", "constant_export"]}
INT_TYPES = {"unsigned", "signed-positive", "signed-negative"}


def shape(n, ident, required, optional=(), children=None):
    if n["id"] != ident:
        raise MigrationError(f"expected element {ident}, got {n['id']}")
    attrs = {}
    for item in n["attrs"]:
        if item["id"] in attrs or item["id"] not in set(required) | set(optional):
            raise MigrationError(f"duplicate/unknown attribute {item['id']} in element {ident}")
        attrs[item["id"]] = item["value"]
    if set(required) - attrs.keys():
        raise MigrationError(f"missing attributes in element {ident}: {sorted(set(required)-attrs.keys())}")
    typed = dict(required)
    if isinstance(optional, dict):
        typed.update({key:kind for key,kind in optional.items() if key in attrs})
    for key, kind in typed.items():
        item = next(a for a in n["attrs"] if a["id"] == key)
        if (kind == "int" and item["type"] not in INT_TYPES) or (kind != "int" and item["type"] != kind):
            raise MigrationError(f"wrong attribute type {key} in element {ident}")
    if children is not None and any(c["id"] not in children for c in n["children"]):
        raise MigrationError(f"unknown child in element {ident}")
    return attrs


def one(n, ident):
    nodes = [c for c in n["children"] if c["id"] == ident]
    if len(nodes) != 1:
        raise MigrationError(f"expected one child {ident}, got {len(nodes)}")
    return nodes[0]


def merge_pattern(a, b):
    if (a[1] ^ b[1]) & a[0] & b[0]:
        raise MigrationError("contradictory instruction constraints")
    return a[0] | b[0], a[1] | b[1]


def instruction_pattern(n, length=8):
    shape(n, 18, {}, children={7})
    block = one(n, 7)
    a = shape(block, 7, {6: "int", 10: "int"}, children={6})
    offset, nonzero = a[6], a[10]
    if not 0 <= offset <= length or not 0 <= nonzero <= length-offset:
        raise MigrationError("pattern range/always-false sentinel unsupported")
    if len(block['children']) != (nonzero+3)//4:
        raise MigrationError("pattern word sequence does not match declared extent")
    masks, values = bytearray(length), bytearray(length)
    for i, word in enumerate(block["children"]):
        w = shape(word, 6, {8: "unsigned", 2: "unsigned"}, children=set())
        if not 0 <= w[2] <= 0xffffffff or not 0 <= w[8] <= 0xffffffff or w[2] & ~w[8]:
            raise MigrationError("invalid pattern word mask/value")
        for j in range(4):
            index = offset+i*4+j
            m, v = (w[8] >> (24-8*j)) & 255, (w[2] >> (24-8*j)) & 255
            if index >= offset+nonzero:
                if m or v:
                    raise MigrationError("pattern word exceeds declared nonzero extent")
            else:
                masks[index], values[index] = m, v
    if any(masks[offset+len(block["children"])*4:offset+nonzero]):
        raise MigrationError("incomplete pattern word sequence")
    # Packed pattern words are instruction-byte-order bit streams, not host
    # or guest integer words. The admitted instruction profile is little endian.
    return int.from_bytes(masks, "little"), int.from_bytes(values, "little")


def decision_pairs(n, inherited=(0, 0)):
    a = shape(n, 16, {20: "int", 21: "boolean", 14: "int", 15: "int"}, children={9, 16})
    if a[21] or not 0 <= a[15] <= 8 or not 0 <= a[14] <= 64-a[15]:
        raise MigrationError("context decision or out-of-range decision bits")
    pairs = [c for c in n["children"] if c["id"] == 9]
    branches = [c for c in n["children"] if c["id"] == 16]
    if a[15] == 0:
        if branches:
            raise MigrationError("zero-bit decision has branches")
        for pair in pairs:
            p = shape(pair, 9, {3: "int"}, children={18})
            pattern = instruction_pattern(one(pair, 18))
            if not (inherited[1] ^ pattern[1]) & inherited[0] & pattern[0]:
                yield p[3], merge_pattern(inherited, pattern)
    else:
        if pairs or len(branches) != 1 << a[15]:
            raise MigrationError("decision branches/pairs do not match bit extent")
        for index, child in enumerate(branches):
            m, v = 0, 0
            for bit in range(a[15]):
                stream_bit = a[14]+bit
                shift = (stream_bit//8)*8 + 7-stream_bit%8
                m |= 1 << shift
                v |= ((index >> (a[15]-1-bit)) & 1) << shift
            if not (inherited[1] ^ v) & inherited[0] & m:
                yield from decision_pairs(child, merge_pattern(inherited, (m, v)))


class SlaSlice:
    def __init__(self, tree):
        self.tree = tree
        root = shape(tree, 33, {34: "int", 35: "boolean", 36: "int", 37: "unsigned"}, optional={38:"int",39:"unsigned",40:"int"}, children={35,34,38})
        if root[34] != 4 or root[36] != 1 or any(a["value"] for a in tree["attrs"] if a["id"] in {38,40}):
            raise MigrationError("only v4 byte-aligned/no-delay/no-section SLA roots admitted")
        self.big = root[35]
        self.source_files={}
        files=one(tree,35); shape(files,35,{},children={36})
        for n in files['children']:
            f=shape(n,36,{12:'string',9:'int'},children=set())
            if f[9]<0 or f[9] in self.source_files:
                raise MigrationError('invalid/duplicate source file ID')
            self.source_files[f[9]]=f[12]
        self.symbols = one(tree, 38)
        symbol_counts=shape(self.symbols, 38, {45: "int",46: "int"})
        self.heads, self.bodies = {}, {}
        for n in self.symbols["children"]:
            attrs = {a["id"]:a["value"] for a in n["attrs"]}
            if 12 in attrs:
                h = shape(n, n["id"], {12:"string",3:"unsigned",13:"unsigned"}, children=set())
                if h[3] in self.heads:
                    raise MigrationError("duplicate symbol header identity")
                self.heads[h[3]] = (h[12], h[13], n["id"])
            elif n["id"] != 22:
                if 3 not in attrs or attrs[3] in self.bodies:
                    raise MigrationError("missing/duplicate symbol body identity")
                self.bodies[attrs[3]] = n
        if len(self.heads)!=symbol_counts[46] or sum(n['id']==22 for n in self.symbols['children'])!=symbol_counts[45]:
            raise MigrationError("symbol/scope header count mismatch")
        spaces_node = one(tree, 34)
        self.default_space = shape(spaces_node,34,{41:"string"},children={37,45,46})[41]
        self.spaces, self.internal_spaces = {}, []
        seen_space_ids, seen_space_names=set(),set()
        for n in spaces_node["children"]:
            s = shape(n,n["id"],{12:"string",9:"int",35:"boolean",42:"int",15:"int",44:"boolean"},optional={43:"int"},children=set())
            if s[9] in seen_space_ids or s[12] in seen_space_names or s[9]<0 or not 1 <= s[15] <= 8 or s.get(43,1) != 1:
                raise MigrationError("duplicate space or unsupported address unit/width")
            seen_space_ids.add(s[9]); seen_space_names.add(s[12])
            if n["id"] != 37:
                self.internal_spaces.append(s)
                continue
            if not s[44] or (s[12] == "register" and s[42] != 0) or (s[12] != "register" and s[42] != 1):
                raise MigrationError("unsupported ordinary space role/delay")
            self.spaces[s[9]] = {"name":s[12],"kind":"register" if s[12]=="register" else "memory",
                                  "address_bytes":s[15],"byte_order":"big" if s[35] else "little"}
        if not any(s['name']==self.default_space and s['kind']=='memory' for s in self.spaces.values()):
            raise MigrationError("default memory space cannot be resolved")
        self.registers = {}
        for ident,n in self.bodies.items():
            if n["id"] != 23:
                continue
            a = shape(n,23,{3:"unsigned",4:"address-space",6:"unsigned",15:"int"},children=set())
            name,scope,head_type = self.heads.get(ident,(None,None,None))
            space = self.spaces.get(a[4])
            if head_type != 24 or scope != 0 or not space or space["kind"] != "register" or not 1 <= a[15] <= 512 or a[6]+a[15] > 1 << (space["address_bytes"]*8):
                raise MigrationError("unresolved or unsupported named register symbol")
            self.registers[ident] = {"name":name,"space":space["name"],"offset":a[6],"size_bytes":a[15]}
        if len({r['name'] for r in self.registers.values()}) != len(self.registers) or not self.registers:
            raise MigrationError("missing/duplicate register names")
        self.tables = {i:n for i,n in self.bodies.items() if n['id']==71}
        self.root_id = next((i for i,h in self.heads.items() if h==( "instruction",0,72)),None)
        if self.root_id not in self.tables:
            raise MigrationError("missing instruction subtable")

    def constructors(self, table):
        n = self.tables[table]
        a = shape(n,71,{3:"unsigned",53:"int"},children={20,16})
        constructors = [c for c in n['children'] if c['id']==20]
        if len(constructors) != a[53]:
            raise MigrationError("constructor count mismatch")
        return constructors

    def operand(self, table, constructor, index):
        ctor = self.constructors(table)[constructor]
        shape(ctor,20,{22:"unsigned",27:"int",26:"int",25:"int",24:"int"},children={15,8,17,21})
        refs = [shape(c,15,{3:"unsigned"},children=set())[3] for c in ctor['children'] if c['id']==15]
        if not 0 <= index < len(refs):
            raise MigrationError("handle index outside constructor")
        n = self.bodies[refs[index]]
        a = shape(n,13,{3:"unsigned",23:"unsigned",6:"int",19:"int",18:"int",9:"int"},children={12})
        exp = shape(one(n,12),12,{9:"int",16:"unsigned",17:"unsigned"},children=set())
        if (a[6],a[19],a[18],a[9]) != (0,-1,8,index) or (exp[9],exp[16],exp[17]) != (index,table,constructor):
            raise MigrationError("relative/dynamic/foreign operand binding")
        return a[23]

    def field(self, symbol):
        n = self.bodies[symbol]
        if self.heads[symbol][1:]!=(0,77):
            raise MigrationError("selector symbol is not a global varlist")
        shape(n,76,{3:"unsigned"},children={27,28,11})
        t = shape(one(n,27),27,{35:"boolean",31:"boolean",14:"int",30:"int",33:"int",32:"int",29:"int"},children=set())
        start,end=t[14],t[30]
        if self.big or t[35] or t[31] or not 0 <= start <= end < 64 or end-start+1 > 8 or (t[33],t[32],t[29]) != (start//8,end//8,start%8):
            raise MigrationError("signed/big-endian/transformed selector unsupported")
        entries=[c for c in n['children'] if c['id']!=27]
        if len(entries) != 1 << (end-start+1):
            raise MigrationError("selector table extent mismatch")
        holes,views=[],[]
        for slot,c in enumerate(entries):
            if c['id']==11:
                shape(c,11,{},children=set()); holes.append(slot)
            else:
                ident=shape(c,28,{3:"unsigned"},children=set())[3]
                r=self.registers.get(ident)
                if not r or r['size_bytes']!=8 or r['offset']!=slot*8:
                    raise MigrationError("selector-to-slot map requires a new generic mapping primitive")
                views.append(r)
        if not views or len({r['space'] for r in views})!=1:
            raise MigrationError("empty/mixed selector register bank")
        return {"offset":start,"bits":end-start+1,"exclude":holes,"registers":views}

    @staticmethod
    def handle(n):
        shape(n,2,{},children={4})
        if len(n['children'])!=3:
            raise MigrationError("varnode handle must have space/offset/size")
        atoms=[shape(c,4,{2:"int",5:"int"},children=set()) for c in n['children']]
        if [a[5] for a in atoms]!=[0,1,2] or len({a[2] for a in atoms})!=1 or atoms[0][2]<0:
            raise MigrationError("dynamic/mixed handle atom unsupported")
        return atoms[0][2]

    @staticmethod
    def real(n):
        return shape(n,1,{2:"unsigned"},children=set())[2]

    def export_field(self, table, slot):
        ctor=self.constructors(table)[slot]
        ca=shape(ctor,20,{22:"unsigned",27:"int",26:"int",25:"int",24:"int"},children={15,8,17,21})
        if ca[22]!=table or ca[26]!=8:
            raise MigrationError('foreign/variable-length export constructor')
        tpl=one(ctor,21); shape(tpl,21,{},children={30})
        hand=one(tpl,30); shape(hand,30,{},children={4,1,3})
        parts=hand['children']
        if len(parts)!=7:
            raise MigrationError("invalid export handle extent")
        if any(parts[i]['id']!=4 for i in [0,1,3]):
            raise MigrationError("constant/dynamic export unsupported")
        atoms=[shape(parts[i],4,{2:"int",5:"int"},children=set()) for i in [0,1,3]]
        if [a[5] for a in atoms]!=[0,2,1] or len({a[2] for a in atoms})!=1 or any(self.real(parts[i]) for i in [2,4,5,6]):
            raise MigrationError("constant/dynamic export unsupported")
        return self.field(self.operand(table,slot,atoms[0][2]))

    def lower(self, slot):
        if self.big:
            raise MigrationError("semantic slice admits little-endian instruction profiles only")
        ctor=self.constructors(self.root_id)[slot]
        ca=shape(ctor,20,{22:"unsigned",27:"int",26:"int",25:"int",24:"int"},children={15,8,17,21})
        if ca[22]!=self.root_id or ca[26]!=8:
            raise MigrationError("foreign/variable-length constructor")
        tpl=one(ctor,21); shape(tpl,21,{},children={11,5})
        if len(tpl['children'])!=3 or tpl['children'][0]['id']!=11:
            raise MigrationError("root semantic body requires BUILD then INT_ADD and no export")
        shape(tpl['children'][0],11,{},children=set())
        build,add=tpl['children'][1:]
        if shape(build,5,{7:"int"},children={11,2})[7]!=60 or shape(add,5,{7:"int"},children={2})[7]!=19:
            raise MigrationError("unregistered ordered opcode body (requires BUILD, INT_ADD)")
        if len(build['children'])!=2 or build['children'][0]['id']!=11:
            raise MigrationError("invalid BUILD output/arity")
        shape(build['children'][0],11,{},children=set())
        constant=build['children'][1]; shape(constant,2,{},children={3,1})
        if len(constant['children'])!=3 or shape(constant['children'][0],3,{4:"address-space"},children=set())[4]!=0 or self.real(constant['children'][2])!=4:
            raise MigrationError("BUILD operand must be a 4-byte constant")
        build_index=self.real(constant['children'][1])
        if len(add['children'])!=3:
            raise MigrationError("INT_ADD arity mismatch")
        output,left,right=[self.handle(n) for n in add['children']]
        if output!=left or right!=build_index or output==right:
            raise MigrationError("first add slice requires destination plus built source")
        destination=self.field(self.operand(self.root_id,slot,output))
        child_table=self.operand(self.root_id,slot,build_index)
        if child_table not in self.tables:
            raise MigrationError("BUILD operand does not reference a subtable")
        root_patterns=[p for ident,p in decision_pairs(one(self.tables[self.root_id],16)) if ident==slot]
        child_patterns=list(decision_pairs(one(self.tables[child_table],16)))
        variants,refusals=[],[]
        for child_slot,p in child_patterns:
            try:
                source=self.export_field(child_table,child_slot)
                if source['registers']!=destination['registers']:
                    raise MigrationError("operand banks disagree")
                for parent in root_patterns:
                    mask,value=merge_pattern(parent,p)
                    variants.append({"constructor":slot,"child_table":child_table,"child_constructor":child_slot,
                                     "mask":mask,"value":value,"destination":destination,"source":source,
                                     "source_id":ca[25],"source_line":ca[24]})
            except MigrationError as exc:
                refusals.append({"child_table":child_table,"child_constructor":child_slot,"reason":str(exc)})
        if not root_patterns or not variants:
            raise MigrationError("no supported bound register variant")
        return variants,refusals


def prove_selection(parsed,v):
    """Prove first-match ownership of this bounded variant, retaining shadows."""
    root_pairs=list(decision_pairs(one(parsed.tables[parsed.root_id],16)))
    owner_positions=[i for i,(ident,p) in enumerate(root_pairs) if ident==v['constructor'] and not ((v['value']^p[1]) & v['mask'] & p[0])]
    if len(owner_positions)!=1:
        raise MigrationError("converted variant must have one owning root leaf pair")
    owner=owner_positions[0]
    shadowed=[]
    for i,(other,p) in enumerate(root_pairs):
        if other!=v['constructor'] and not ((v['value']^p[1]) & v['mask'] & p[0]):
            if i<owner:
                raise MigrationError(f"earlier root pair shadows converted constructor: {other}")
            shadowed.append({"pair_position":i,"constructor":other,"mask":p[0],"value":p[1]})
    return {"owning_root_pair_position":owner,"later_overlapping_root_pairs":shadowed,"rule":"first matching pair within the selected instruction decision leaf"}


def migrate(root, sla):
    observed=inspect(sla,True)
    parsed=SlaSlice(observed['tree'])
    relative,digest=provenance(sla,root)
    layout_name='ebpf.le.sla.registers'
    layout=[f'layout {layout_name} {{', '    '+evidence(relative,digest,"SLA v4 ordinary spaces and named varnode symbols; byte offsets/widths retained. Internal unique/OTHER spaces are evidence only."),
            f'    default_space {quote(parsed.default_space)};']
    for s in parsed.spaces.values():
        layout.append(f'    space {quote(s["name"])} {s["kind"]} {s["address_bytes"]} byte {s["byte_order"]};')
    for r in sorted(parsed.registers.values(),key=lambda r:(r['space'],r['offset'],r['size_bytes'],r['name'])):
        layout.append(f'    register {quote(r["name"])} {quote(r["space"])} {r["offset"]} {r["size_bytes"]};')
    layout.append('}')
    variants,rows=[],[]
    for table in parsed.tables:
        for slot,ctor in enumerate(parsed.constructors(table)):
            attrs={a['id']:a['value'] for a in ctor['attrs']}
            row={"table":table,"table_name":parsed.heads[table][0],"constructor":slot,"source_id":attrs.get(25),"source_file":parsed.source_files.get(attrs.get(25)),"source_line":attrs.get(24),
                 "opcodes":[a['value'] for tpl in ctor['children'] if tpl['id']==21 for op in tpl['children'] if op['id']==5 for a in op['attrs'] if a['id']==7]}
            try:
                if table!=parsed.root_id:
                    raise MigrationError("non-root template outside consumed dependencies; no standalone profile emitted")
                admitted,refused=parsed.lower(slot)
                variants.extend(admitted); row.update(status='partial-converted',variants=len(admitted),branch_refusals=refused)
            except MigrationError as exc:
                row.update(status='unsupported',reason=str(exc))
            rows.append(row)
    if len(variants)!=1:
        raise MigrationError(f"first semantic gate requires one unambiguous variant, found {len(variants)}")
    v=variants[0]
    consumed={(variant['child_table'],variant['child_constructor']) for variant in variants}
    for row in rows:
        if (row['table'],row['constructor']) in consumed:
            row.update(status='dependency-consumed',reason='Pure register export consumed by a bound root template; not an independent instruction')
    # SLA leaf pairs have first-match priority. Different decision paths already
    # have disjoint inherited constraints. Refuse a competing earlier pair;
    # retain later overlaps as evidence rather than inventing unambiguous SLA.
    selection=prove_selection(parsed,v)
    lines=['language ebpf.le.sla.add64.register {','    byte_order little;','    address_unit byte;',
           f'    instruction table{parsed.root_id}_constructor{v["constructor"]}_register {{',f'        encoding 64 mask {v["mask"]:#x} value {v["value"]:#x} {{']
    for name in ['destination','source']:
        f=v[name]; exclusions=', '.join(str(i) for i in f['exclude'])
        lines.append(f'            field {name} offset {f["offset"]} bits {f["bits"]}'+(f' exclude {exclusions}' if exclusions else '')+';')
    ctor=parsed.constructors(parsed.root_id)[v['constructor']]
    mnemonic=''
    for n in ctor['children']:
        if n['id']==17: break
        if n['id']==8: mnemonic+=shape(n,8,{11:'string'},children=set())[11]
    lines += ['        }',f'        mnemonic {quote(mnemonic.strip())};',
              '        '+evidence(relative,digest,f'SLA v4 table {parsed.root_id} constructor {v["constructor"]}, child table {v["child_table"]} constructor {v["child_constructor"]}: instruction constraints, selector tables and BUILD/export/INT_ADD atoms lowered. Source line is metadata only; no Sleigh source is read.'),
              '        semantics {','            %lhs: u64 = register.read destination;','            %rhs: u64 = register.read source;',
              '            %sum: u64 = u64.add.wrap %lhs, %rhs;','            register.write destination, %sum;','        }','    }','}']
    report={"format":"fission-sla-semantic-migration-v1","source_snapshot":SNAPSHOT,"source":relative,"sha256":digest,
            "format_reference_sha256":hashlib.sha256((pathlib.Path(__file__).resolve().parents[1]/'data/sla-v4-format.lock.toml').read_bytes()).hexdigest(),
            "registry":REGISTRY,"registers":list(parsed.registers.values()),"spaces":list(parsed.spaces.values()),
            "source_files":parsed.source_files,
            "internal_spaces_not_emitted":parsed.internal_spaces,"variants":variants,"constructors":rows,
            "selection_proof":selection,
            "constructor_count":len(rows),"root_constructor_count":len(parsed.constructors(parsed.root_id)),"converted_instruction_variants":len(variants),
            "scope":"One little-endian bound ADD64 register variant from SLA; no general context, variable-length, memory or control-flow migration"}
    return '\n'.join(lines)+'\n','\n'.join(layout)+'\n',report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fission-root',type=pathlib.Path,required=True)
    parser.add_argument('--output-dir',type=pathlib.Path,required=True)
    args=parser.parse_args()
    try:
        commit=subprocess.run(['git','-C',str(args.fission_root),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
        if commit!=SNAPSHOT: raise MigrationError('SLA migration requires pinned snapshot '+SNAPSHOT)
        fsl,layout,report=migrate(args.fission_root,args.fission_root/'utils/sleigh-specs/compiled/eBPF/eBPF_le.sla')
        artifacts={'ebpf-sla-add64-register.fsl':fsl,'ebpf.le.sla.registers.fslregs':layout}
        report['outputs']={n:hashlib.sha256(t.encode()).hexdigest() for n,t in artifacts.items()}
        report['license']={"upstream":"Ghidra Apache-2.0","files":{n:hashlib.sha256((args.fission_root/n).read_bytes()).hexdigest() for n in ['LICENSE','NOTICE','THIRD_PARTY.md']}}
        args.output_dir.mkdir(parents=True,exist_ok=True)
        for n,t in artifacts.items(): (args.output_dir/n).write_text(t)
        (args.output_dir/'sla-migration.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'SLA symbols={len(report["registers"])} constructors={report["constructor_count"]}; converted instruction variants=1')
        return 0
    except (OSError,ValueError,MigrationError,SlaError,subprocess.CalledProcessError,KeyError,IndexError) as exc:
        print('sla_migrate: '+str(exc),file=sys.stderr); return 2


if __name__=='__main__': raise SystemExit(main())

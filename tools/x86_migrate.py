#!/usr/bin/env python3
"""Offline x86 declaration migration and authored FIR templates.

This does not translate all SLEIGH constructors. Inventory retains every asset
hash and an explicit status; scalar semantics are authored against the source
and Intel SDM, including AF which the source leaves unimplemented.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def layout(text: str, long_mode: bool, evidence: str) -> str:
    text = text[:text.index("define token")]
    active, stack, macros, lines = True, [], {}, []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line == "@ifdef IA64":
            stack.append((active, long_mode))
            active = active and long_mode
        elif line == "@else":
            parent, condition = stack[-1]
            active = parent and not condition
        elif line == "@endif":
            active, _ = stack.pop()
        elif line.startswith("@define"):
            if active:
                match = re.fullmatch(r'@define\s+(\w+)\s+"([^"]+)"', line)
                if not match:
                    raise ValueError("unsupported prefix macro")
                macros[match[1]] = match[2]
        elif active:
            if line.startswith("@"):
                raise ValueError("unsupported layout directive " + line)
            lines.append(line)
    if stack:
        raise ValueError("unclosed prefix conditional")
    text = "\n".join(lines)
    for name, value in macros.items():
        text = text.replace("$(" + name + ")", value)
    if "$" in text:
        raise ValueError("unresolved layout macro")
    # Prefix includes context/bitrange declarations after register declarations.
    # Only register/space statements are migrated; remaining statements are
    # catalogued as context work, never interpreted as register metadata.
    spaces = list(re.finditer(r"define space (\w+) type=(ram_space|register_space) size=(\d+)( default)?;", text))
    text = re.sub(r"(define register offset=(?:0x[0-9a-fA-F]+|\d+) size=\d+)\s+(\w+)\s*;", r"\1 [ \2 ];", text)
    registers = list(re.finditer(r"define register offset=(0x[0-9a-fA-F]+|\d+) size=(\d+)\s*\[(.*?)\]\s*;", text, re.S))
    remaining = re.sub(r"define space .*?;|define register .*?;", "", text, flags=re.S)
    if "define register" in remaining or "define space" in remaining:
        raise ValueError("unparsed register or space declaration")
    name = "x86.64.registers" if long_mode else "x86.legacy.registers"
    out = [f"layout {name} {{", "    " + evidence, '    default_space "ram";']
    for m in spaces:
        kind = "memory" if m[2] == "ram_space" else "register"
        out.append(f'    space "{m[1]}" {kind} {m[3]} byte little;')
    names = set()
    for m in registers:
        offset, size = int(m[1], 0), int(m[2])
        for i, reg in enumerate(m[3].split()):
            if reg == "_":
                continue
            if reg in names or not re.fullmatch(r"\w+", reg):
                raise ValueError("duplicate/invalid register " + reg)
            names.add(reg)
            out.append(f'    register "{reg}" "register" {offset + i * size} {size};')
    return "\n".join(out + ["}", ""])


def bodies(evidence: str, memory_sources: bool = False, memory_writes: bool = False, memory_immediates: bool = False) -> str:
    records = []
    body_ops = {}

    def add(name: str, ops: list[str], extra_evidence: str = "", split: bool = False) -> None:
        body_ops[name] = ops
        index = len(records) + 1
        fields = [('destination', 0, 5), ('source', 5, 5), ('base', 10, 5), ('index', 15, 5), ('immediate', 20, 64), ('scale', 84, 2)]
        if split:
            fields = [('destination', 0, 5), ('source', 5, 5), ('base', 10, 5), ('index', 15, 5), ('displacement', 20, 64), ('scale', 84, 2), ('literal', 86, 32)]
        mask = ((1 << 10) - 1) << 118 if split else 0xffff << 112
        value = index << (118 if split else 112)
        encoding = f"        encoding 128 mask 0x{mask:032x} value 0x{value:032x} {{" if split else f"        encoding 128 mask 0xffff0000000000000000000000000000 value 0x{index:x}0000000000000000000000000000 {{"
        records.append("\n".join([
            f"    instruction {name} {{",
            encoding,
            *[f"            field {n} offset {o} bits {b};" for n, o, b in fields],
            "        }", f'        mnemonic "{name}";', "        " + evidence,
            *(["        " + extra_evidence] if extra_evidence else []),
            "        semantics {", *["            " + op for op in ops], "        }", "    }",
        ]))

    def write_result(ops: list[str], bits: int, result: str = "result") -> None:
        if bits == 16:
            ops += ["%old: u64 = register.read destination;", "%keep: u64 = int.const 0xffffffffffff0000;",
                    "%high: u64 = u64.and %old, %keep;", f"%low: u64 = int.zext %{result};",
                    "%merged: u64 = u64.or %high, %low;", "register.write destination, %merged;"]
        else:
            # Logical u64 slot assignment explicitly clears upper bits for u32.
            ops.append(f"register.write destination, %{result};")

    for bits in [16, 32, 64]:
        ty = f"u{bits}"
        for operation in ["mov", "add", "sub", "cmp", "and", "or", "xor", "test"]:
            for form in ["reg", "imm"]:
                ops = [f"%lhs: {ty} = register.read destination;"]
                if form == "reg":
                    ops += [f"%rhs: {ty} = register.read source;"]
                else:
                    ops += ["%imm64: u64 = field.read immediate;"]
                    ops += [f"%rhs: {ty} = int.trunc %imm64;"] if bits < 64 else ["%rhs: u64 = field.read immediate;"]
                if operation == "mov":
                    write_result(ops, bits, "rhs")
                    add(f"mov{bits}_{form}", ops)
                    continue
                kind = {"add": "add.wrap", "cmp": "sub", "test": "and"}.get(operation, operation)
                ops += [f"%result: {ty} = {ty}.{kind} %lhs, %rhs;", f"%zero: {ty} = int.const 0;",
                        "%off: u1 = int.const 0;", "%on: u1 = int.const 1;",
                        "%zf: u1 = int.eq %result, %zero;",
                        f"%sign: {ty} = int.const {1 << (bits - 1)};",
                        f"%signbit: {ty} = {ty}.and %result, %sign;",
                        "%sf: u1 = int.eq %signbit, %sign;"]
                # PF is even parity of the low byte. No separate semantic owner.
                for i in range(8):
                    ops += [f"%p_mask{i}: {ty} = int.const {1 << i};",
                            f"%p_bit{i}: {ty} = {ty}.and %result, %p_mask{i};",
                            f"%p{i}: u1 = int.eq %p_bit{i}, %p_mask{i};"]
                parity = "p0"
                for i in range(1, 8):
                    ops += [f"%parity{i}: u1 = u1.xor %{parity}, %p{i};"]
                    parity = f"parity{i}"
                ops += [f"%pf: u1 = int.eq %{parity}, %off;"]
                if operation in ["add", "sub", "cmp"]:
                    ops += ["%cf: u1 = int.add.carry %lhs, %rhs;" if operation == "add" else "%cf: u1 = int.ult %lhs, %rhs;",
                            f"%lr: {ty} = {ty}.xor %lhs, %rhs;", f"%lo: {ty} = {ty}.xor %lhs, %result;"]
                    if operation == "add":
                        ops += [f"%all: {ty} = int.const {(1 << bits) - 1};", f"%notlr: {ty} = {ty}.xor %lr, %all;", f"%ov: {ty} = {ty}.and %notlr, %lo;"]
                    else:
                        ops += [f"%ov: {ty} = {ty}.and %lr, %lo;"]
                    ops += [f"%ovsign: {ty} = {ty}.and %ov, %sign;", "%of: u1 = int.eq %ovsign, %sign;",
                            f"%afmix: {ty} = {ty}.xor %lr, %result;", f"%afmask: {ty} = int.const 16;",
                            f"%afbit: {ty} = {ty}.and %afmix, %afmask;", "%af: u1 = int.eq %afbit, %afmask;",
                            "flag.write 0, %cf;", "flag.write 4, %of;", "flag.write 5, %af;", "flag.write 11, %on;"]
                else:
                    ops += ["flag.write 0, %off;", "flag.write 4, %off;", "flag.write 11, %off;"]
                ops += ["flag.write 1, %pf;", "flag.write 2, %zf;", "flag.write 3, %sf;",
                        *[f"flag.write {i}, %on;" for i in range(6, 11)]]
                if operation not in ["cmp", "test"]:
                    write_result(ops, bits)
                add(f"{operation}{bits}_{form}", ops)
        for address_bits in [16, 32, 64]:
            at = f"u{address_bits}"
            ops = [f"%base: {at} = register.read base;", f"%index: {at} = register.read index;",
                   "%scale: u64 = field.read scale;", "%s0: u64 = int.const 0;", "%s1: u64 = int.const 1;", "%s2: u64 = int.const 2;",
                   "%c0: u1 = int.eq %scale, %s0;", "%c1: u1 = int.eq %scale, %s1;", "%c2: u1 = int.eq %scale, %s2;",
                   # Acyclic, explicit block arguments for scaled index.
                   "block entry() {", "branch.if %c0, one(), choose();", "}"]
            # Definitions must belong to a block: move prefix into entry.
            ops = ["block entry() {", *ops[:-3], "branch.if %c0, one(%base, %index), choose(%base, %index, %c1, %c2);", "}",
                   f"block one(%b1: {at}, %i1: {at}) {{", "branch sum(%b1, %i1);", "}",
                   f"block choose(%bc: {at}, %ic: {at}, %c_one: u1, %c_two: u1) {{", f"%doubled: {at} = {at}.add.wrap %ic, %ic;", "branch.if %c_one, two(%bc, %doubled), more(%bc, %doubled, %c_two);", "}",
                   f"block two(%b2: {at}, %i2: {at}) {{", "branch sum(%b2, %i2);", "}",
                   f"block more(%bm: {at}, %im: {at}, %cm: u1) {{", f"%quad: {at} = {at}.add.wrap %im, %im;", "branch.if %cm, four(%bm, %quad), eight(%bm, %quad);", "}",
                   f"block four(%b4: {at}, %i4: {at}) {{", "branch sum(%b4, %i4);", "}",
                   f"block eight(%b8: {at}, %i8: {at}) {{", f"%oct: {at} = {at}.add.wrap %i8, %i8;", "branch sum(%b8, %oct);", "}",
                   f"block sum(%bs: {at}, %ix: {at}) {{", "%displacement64: u64 = field.read immediate;"]
            ops += [f"%disp: {at} = int.trunc %displacement64;"] if address_bits < 64 else ["%disp: u64 = field.read immediate;"]
            ops += [f"%sum: {at} = {at}.add.wrap %bs, %ix;", f"%addr: {at} = {at}.add.wrap %sum, %disp;"]
            ops += [f"%result: {ty} = int.trunc %addr;"] if bits < address_bits else ([f"%result: {ty} = int.zext %addr;"] if bits > address_bits else [])
            write_result(ops, bits, "addr" if bits == address_bits else "result")
            ops += ["return;", "}"]
            add(f"lea{bits}_a{address_bits}", ops)
        ops = [f"%sp: {ty} = register.read destination;"]
        ops += ["%address: u64 = int.zext %sp;"] if bits < 64 else ["%address: u64 = register.read destination;"]
        ops += [f"%target: {ty} = memory.load.le %address;", f"%step: {ty} = int.const {bits // 8};", f"%after: {ty} = {ty}.add.wrap %sp, %step;"]
        write_result(ops, bits, "after")
        ops += ["%exit: u64 = int.zext %target;"] if bits < 64 else []
        ops += ["guest.next_pc.write %exit;" if bits < 64 else "guest.next_pc.write %target;"]
        add(f"ret{bits}", ops)
    add("direct", ["%target: u64 = field.read immediate;", "guest.next_pc.write %target;"])
    for name, take in [("je", 1), ("jne", 0)]:
        add(name, ["block entry() {", "%zf: u1 = flag.read 2;", f"%take: u1 = int.const {take};", "%match: u1 = int.eq %zf, %take;",
                   "branch.if %match, taken(), fallthrough();", "}", "block taken() {", "%target: u64 = field.read immediate;", "guest.next_pc.write %target;", "return;", "}", "block fallthrough() {", "return;", "}"])
    if memory_sources:
        for bits in [16, 32, 64]:
            for address_bits in [16, 32, 64]:
                address = body_ops[f"lea{bits}_a{address_bits}"]
                end = next(i for i, line in enumerate(address) if line.startswith("%addr:")) + 1
                prefix = address[:end]
                if address_bits < 64:
                    prefix = prefix + ["%memory_address: u64 = int.zext %addr;"]
                pointer = "memory_address" if address_bits < 64 else "addr"
                for op in ["mov", "add", "sub", "cmp", "and", "or", "xor"]:
                    scalar = [line for line in body_ops[f"{op}{bits}_reg"] if "= register.read source;" not in line]
                    add(f"{op}{bits}_load_a{address_bits}", prefix +
                        [f"%rhs: u{bits} = memory.load.le %{pointer};"] + scalar + ["return;", "}"])
    if memory_writes:
        stack_evidence = (
            'evidence "intel-modern-stack" '
            '"https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf" '
            '"sha256:036ae35aec4da9dd54ba3b683547f09963f69609a3b98eae15586a692c4cd3d2" '
            '"PUSH/POP sections: modern IA-32/Intel64 ordering, not 8086 PUSH SP; '
            'unprefixed stack-address-width equals selected mode, flat SS base zero. '
            'Descriptor B flag, faults, privilege and concurrency are outside this contract.";'
        )
        for bits in [16, 32, 64]:
            for address_bits in [16, 32, 64]:
                address = body_ops[f"lea{bits}_a{address_bits}"]
                end = next(i for i, line in enumerate(address) if line.startswith("%addr:")) + 1
                prefix = address[:end]
                if address_bits < 64:
                    prefix = prefix + ["%memory_address: u64 = int.zext %addr;"]
                pointer = "memory_address" if address_bits < 64 else "addr"
                add(f"mov{bits}_store_a{address_bits}", prefix +
                    [f"%value: u{bits} = register.read source;", f"memory.store.le %{pointer}, %value;", "return;", "}"])
            ty = f"u{bits}"
            def stack_write(ops, value):
                extra = []
                write_result(extra, bits, value)
                ops.extend(line.replace("destination", "base").replace("%old", "%sp_old").replace("%keep", "%sp_keep").replace("%high", "%sp_high").replace("%low", "%sp_low").replace("%merged", "%sp_merged") for line in extra)
            ops = [f"%value: {ty} = register.read destination;", f"%sp: {ty} = register.read base;",
                   f"%step: {ty} = int.const {bits//8};", f"%after: {ty} = {ty}.sub %sp, %step;"]
            ops += ["%pointer: u64 = int.zext %after;"] if bits < 64 else []
            ops += [f"memory.store.le %{'pointer' if bits < 64 else 'after'}, %value;"]
            stack_write(ops, "after")
            add(f"push{bits}", ops, stack_evidence)
            ops = [f"%sp: {ty} = register.read base;"]
            ops += ["%pointer: u64 = int.zext %sp;"] if bits < 64 else ["%pointer: u64 = register.read base;"]
            ops += [f"%value: {ty} = memory.load.le %pointer;", f"%step: {ty} = int.const {bits//8};", f"%after: {ty} = {ty}.add.wrap %sp, %step;"]
            stack_write(ops, "after")
            write_result(ops, bits, "value")
            add(f"pop{bits}", ops, stack_evidence)
    if memory_immediates:
        mov_evidence = (
            'evidence "intel-mov-immediate" '
            '"https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf" '
            '"sha256:036ae35aec4da9dd54ba3b683547f09963f69609a3b98eae15586a692c4cd3d2" '
            '"MOV C7 /0: imm16/imm32 store; REX.W sign extends imm32 to 64 bits; flags unaffected. Flat bounded memory; no faults, segments or concurrency.";'
        )
        for bits in [16, 32, 64]:
            for address_bits in [16, 32, 64]:
                address = body_ops[f"lea{bits}_a{address_bits}"]
                end = next(i for i, line in enumerate(address) if line.startswith("%addr:")) + 1
                prefix = [line.replace("field.read immediate", "field.read displacement") for line in address[:end]]
                if address_bits < 64:
                    prefix += ["%memory_address: u64 = int.zext %addr;"]
                pointer = "memory_address" if address_bits < 64 else "addr"
                value = ["%literal64: u64 = field.read literal;"]
                if bits < 64:
                    value += [f"%value: u{bits} = int.trunc %literal64;"]
                else:
                    # (x xor signbit) - signbit extends the imm32 bit pattern.
                    value += ["%sign32: u64 = int.const 0x80000000;", "%biased: u64 = u64.xor %literal64, %sign32;", "%value: u64 = u64.sub %biased, %sign32;"]
                add(f"mov{bits}_imm_store_a{address_bits}", prefix + value + [f"memory.store.le %{pointer}, %value;", "return;", "}"], extra_evidence=mov_evidence, split=True)
    return "\n".join(["# Normalized operand tokens are not machine encodings.", "language x86.scalar.bodies {", "    byte_order little;", "    address_unit byte;", *records, "}", ""])


def rules(stack: bool = False, memory_immediates: bool = False) -> str:
    lines = ['frontend x86.scalar {', 'decoder owned-x86-v2;' if memory_immediates else 'decoder owned-x86-v1;']
    def rule(name: str, opcode: str, form: str, body: str, ext: str = "-", mask: str = "ff") -> None:
        lines.append(f"rule {name} {opcode} {mask} {ext} {form} {body};")
    for op, rm, reg, acc, ext in [("mov", "89", "8b", None, None), ("add", "01", "03", "05", "0"),
                                  ("sub", "29", "2b", "2d", "5"), ("cmp", "39", "3b", "3d", "7"),
                                  ("and", "21", "23", "25", "4"), ("or", "09", "0b", "0d", "1"),
                                  ("xor", "31", "33", "35", "6"), ("test", "85", None, "a9", None)]:
        rule(op + "_rm_reg", rm, "rm_reg", op + "{width}_reg")
        if reg:
            rule(op + "_reg_rm", reg, "reg_rm", op + "{width}_reg")
        if acc:
            rule(op + "_acc_imm", acc, "acc_imm", op + "{width}_imm")
        if ext:
            rule(op + "_rm_imm", "81", "rm_imm", op + "{width}_imm", ext)
            rule(op + "_rm_simm8", "83", "rm_simm8", op + "{width}_imm", ext)
    rule("mov_opreg_imm", "b8", "opreg_imm", "mov{width}_imm", mask="f8")
    rule("mov_rm_imm", "c7", "rm_imm", "mov{width}_imm", "0")
    rule("test_rm_imm", "f7", "rm_imm", "test{width}_imm", "0")
    rule("lea", "8d", "lea", "lea{width}")
    rule("ret", "c3", "ret", "ret{width}")
    rule("nop", "90", "nop", "direct")
    for name, short, near in [("jmp", "eb", "e9"), ("je", "74", "0f84"), ("jne", "75", "0f85")]:
        body = "direct" if name == "jmp" else name
        rule(name + "_short", short, "branch8", body)
        rule(name + "_near", near, "branch", body)
    if stack:
        rule("push_reg", "50", "push_reg", "push{width}", mask="f8")
        rule("pop_reg", "58", "pop_reg", "pop{width}", mask="f8")
    return "\n".join(lines + ["}", ""])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fission-root", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--memory-sources", action="store_true", help="append authored scalar memory-source bodies")
    ap.add_argument("--memory-writes", action="store_true", help="append MOV stores and unprefixed register PUSH/POP")
    ap.add_argument("--memory-immediates", action="store_true", help="v2 split displacement/literal binding and C7 memory MOV")
    a = ap.parse_args()
    if a.memory_immediates:
        a.memory_writes = True
    root = a.fission_root.resolve()
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    folder = root / "utils/sleigh-specs/languages/x86"
    source = folder / "ia.sinc"
    digest = sha(source.read_bytes())
    claim = "Authored scalar FIR uses source encoding/defined effects as reference; AF is supplied from Intel SDM. Not complete SLEIGH translation."
    evidence = f'evidence "x86-migration" "https://github.com/fission-systems/Fission/blob/{revision}/utils/sleigh-specs/languages/x86/ia.sinc" "sha256:{digest}" "{claim}";'
    a.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {"scalar-bodies.fsl": bodies(evidence, a.memory_sources or a.memory_writes, a.memory_writes, a.memory_immediates), "scalar.fslx": rules(a.memory_writes, a.memory_immediates)}
    for mode in [32, 64]:
        layout_evidence = evidence.replace(claim, "Register and space declarations migrated from the ia.sinc prefix; offsets and overlapping views preserved; context and calling ABI not migrated.")
        outputs[f"x86-{mode}.fslregs"] = layout(source.read_text(), mode == 64, layout_evidence)
    for name, text in outputs.items():
        (a.output_dir / name).write_text(text)
    assets = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        status = "register-prefix-migrated" if path == source else "inventoried-not-migrated"
        constructors = len(re.findall(r"^:[^\n]*\bis\b", path.read_text(errors="replace"), re.M)) if path.suffix in [".sinc", ".slaspec"] else 0
        assets.append({"path": path.relative_to(root).as_posix(), "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size, "status": status, "constructor_records": constructors})
    report = {"format": "fission-x86-migration-v1", "source_commit": revision, "assets": assets,
              "outputs": {n: sha(t.encode()) for n, t in outputs.items()},
              "scope": "legacy/long-mode register declarations plus authored scalar FIR and owned opcode/prefix/ModRM/SIB decode rules; cspec/pspec/context/SIMD/privileged semantics inventoried, not translated; no external decoder library"}
    (a.output_dir / "migration.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"x86 assets={len(assets)} own outputs={len(outputs)}")


if __name__ == "__main__":
    main()

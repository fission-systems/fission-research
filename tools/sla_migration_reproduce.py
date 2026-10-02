#!/usr/bin/env python3
"""Rebuild SLA-derived artifacts; validate refusal mutations and native gates."""
import argparse
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import tomllib

from register_layout_reproduce import checked
from sla_migrate import MigrationError, SlaSlice, inspect, one, prove_selection


def refusal_checks(path):
    tree=inspect(path,True)['tree']
    checks=[]
    for kind in ['unknown_opcode','context_effect','extra_operation','handle_offset_plus','invalid_build_operand',
                 'selector_hole_corruption','export_effect','earlier_competing_pair']:
        parsed=SlaSlice(copy.deepcopy(tree))
        ctor=parsed.constructors(0)[4]
        tpl=one(ctor,21)
        if kind=='unknown_opcode': tpl['children'][2]['attrs'][0]['value']=999
        elif kind=='context_effect': ctor['children'].append({'id':32,'attrs':[],'children':[]})
        elif kind=='extra_operation': tpl['children'].append(copy.deepcopy(tpl['children'][2]))
        elif kind=='handle_offset_plus': tpl['children'][2]['children'][0]['children'][1]['attrs'][1]['value']=3
        elif kind=='invalid_build_operand': tpl['children'][1]['children'][1]['children'][1]['attrs'][0]['value']=99
        elif kind=='selector_hole_corruption': parsed.bodies[20]['children'][2]['attrs'][0]['value']=999
        elif kind=='export_effect': one(parsed.constructors(28)[0],21)['children'].append(copy.deepcopy(tpl['children'][2]))
        else:
            stack=[one(parsed.tables[0],16)]
            changed=False
            while stack:
                n=stack.pop()
                pair_positions=[i for i,c in enumerate(n['children']) if c['id']==9]
                identities={next(a['value'] for a in n['children'][i]['attrs'] if a['id']==3):i for i in pair_positions}
                if 4 in identities and 91 in identities:
                    a,b=identities[4],identities[91]
                    n['children'][a],n['children'][b]=n['children'][b],n['children'][a]
                    changed=True
                    break
                stack.extend(c for c in n['children'] if c['id']==16)
            if not changed: raise ValueError('missing priority mutation target')
        try:
            variants,_=parsed.lower(4)
            prove_selection(parsed,variants[0])
        except MigrationError as exc:
            checks.append({'mutation':kind,'status':'refused','reason':str(exc)})
        else: raise ValueError('migration accepted unsupported mutation: '+kind)
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fission-root',type=pathlib.Path,default=pathlib.Path('Fission'))
    parser.add_argument('--fslc',type=pathlib.Path)
    parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path('artifacts/sla-migration.json'))
    args=parser.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]
    golden=root/'experiments/migration/sla-first-slice'
    report={'format':'fission-sla-migration-reproduction-v1','status':'failed','artifact_hashes':{},'native_checks':[]}
    try:
        with tempfile.TemporaryDirectory(prefix='fsl-sla-migration-') as directory:
            rebuilt=pathlib.Path(directory)
            checked([sys.executable,root/'tools/sla_migrate.py','--fission-root',args.fission_root.resolve(),'--output-dir',rebuilt])
            for name in ['ebpf-sla-add64-register.fsl','ebpf.le.sla.registers.fslregs','sla-migration.json']:
                data=(rebuilt/name).read_bytes()
                if data!=(golden/name).read_bytes(): raise ValueError('SLA artifact mismatch: '+name)
                report['artifact_hashes'][name]=hashlib.sha256(data).hexdigest()
            report['refusal_checks']=refusal_checks(args.fission_root/'utils/sleigh-specs/compiled/eBPF/eBPF_le.sla')
            if args.fslc:
                fslc=args.fslc.resolve()
                report['fslc_sha256']=hashlib.sha256(fslc.read_bytes()).hexdigest()
                source=rebuilt/'ebpf-sla-add64-register.fsl'
                layout=rebuilt/'ebpf.le.sla.registers.fslregs'
                abi=root/'experiments/migration/first-slice/ebpf.fslabi'
                for command,paths in [('check',[source]),('check-layout',[layout]),('link-abi',[abi,layout])]:
                    result=checked([fslc,command,*paths])
                    report['native_checks'].append({'gate':command,'stdout':result.stdout.strip()})
                package=rebuilt/'ebpf.fslc'
                checked([fslc,'compile',source,package])
                report['package_sha256']=hashlib.sha256(package.read_bytes()).hexdigest()
                lock=tomllib.loads((golden/'source.lock.toml').read_text())
                if report['package_sha256']!=lock['package_sha256']: raise ValueError('SLA-derived package hash mismatch')
                result=checked([fslc,'execute-layout',layout,abi,package,'ebpf.le.sla.add64.register','0f12000000000000',
                                'R0,R1,R2','0,1,0xffffffffffffffff'],expected_text='status=Success registers=[0, 1, 0]')
                report['native_checks'].append({'gate':'execute-layout','stdout':result.stdout.strip()})
            report['status']='passed'
    except (OSError,ValueError,MigrationError,KeyError,IndexError) as exc:
        report['error']=str(exc); print('sla_migration_reproduce: '+str(exc),file=sys.stderr)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    if report['status']=='passed':
        print(f'SLA migration reproduction: 3 artifacts match; refusals={len(report["refusal_checks"])} native gates={len(report["native_checks"])}')
        return 0
    return 2


if __name__=='__main__': raise SystemExit(main())

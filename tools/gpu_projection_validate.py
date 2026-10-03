#!/usr/bin/env python3
"""Validate one FIR's CUDA/PTX projections; scalar reference is not GPU proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import struct
import subprocess
import tempfile
import tomllib

from ptx_reference import Program

ROOT = pathlib.Path(__file__).resolve().parents[1]
BODIES = {
    'add': '%a: TYPE = stack.pop; %b: TYPE = stack.pop; %s: TYPE = TYPE.add.wrap %a, %b; stack.push %s;',
    'duplicate': '%a: TYPE = stack.pop; stack.push %a; stack.push %a;',
    'ordered': '%a: TYPE = stack.pop; stack.push %a; %b: TYPE = stack.pop; %s: TYPE = TYPE.add.wrap %a, %b; stack.push %s; stack.push %a;',
    'pop': '%a: TYPE = stack.pop;',
}


def checked(args):
    result = subprocess.run([str(x) for x in args], text=True, capture_output=True)
    if result.returncode:
        raise ValueError(f'{args[0]} failed: {result.stderr[-4000:]}')
    return result


def assembled_cubin(path):
    data = path.read_bytes()
    if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', data, 18)[0] != 190:
        raise ValueError('expected little-endian ELF64 / EM_CUDA cubin')
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'elf_machine': 190}


def source(ty, body):
    return ('language gpu.projection { byte_order little; address_unit byte; '
            'instruction sample { opcode 0x60; mnemonic "sample"; evidence '
            '"synthetic" "fixture" "v1" "projection contract"; semantics { '
            + body.replace('TYPE', ty) + ' } } }\n')


def oracle(kind, bits, slots, depth, capacity, coordinates, null):
    result = {'slots': list(slots), 'depth': depth, 'status': 0xeeeeeeee}
    if any(coordinates) or null == 'status':
        return result
    if null in ('stack', 'depth') or depth > capacity:
        result['status'] = 3
        return result
    required = 2 if kind == 'add' else 1
    if depth < required:
        result['status'] = 1
        return result
    extra = 1 if kind in ('duplicate', 'ordered') else 0
    if capacity-depth < extra:
        result['status'] = 2
        return result
    mask = (1 << bits)-1
    top = slots[depth-1] & mask
    if kind == 'add':
        result['slots'][depth-2] = (top+(slots[depth-2] & mask)) & mask
        result['depth'] = depth-1
    elif kind == 'pop':
        result['depth'] = depth-1
    else:
        result['slots'][depth-1] = top if kind == 'duplicate' else (2*top) & mask
        result['slots'][depth] = top
        result['depth'] = depth+1
    result['status'] = 0
    return result


def state_checks(program, kind, bits):
    rng = random.Random(0xF1510+bits)
    mask = (1 << bits)-1
    edges = [0, 1, mask, 1 << (bits-1), 0xffffffffffffffff, 0x1234567887654321]
    pairs = [(a, b) for a in edges for b in edges]
    pairs += [(rng.getrandbits(64), rng.getrandbits(64)) for _ in range(32)]
    rows = []
    for a, b in pairs:
        slots = [rng.getrandbits(64) for _ in range(8)]
        slots[1:3] = [a, b]
        rows.append((slots, 3, 8, (0,)*6, None))
    slots = [0xffffffffffffffff, 1, 0x1234, 0x88776655, 9, 10, 11, 12]
    for depth, capacity in [(0, 8), (1, 8), (9, 8), (2, 1), (8, 8), (7, 8)]:
        rows.append((slots, depth, capacity, (0,)*6, None))
    for axis in range(6):
        coordinates = [0]*6
        coordinates[axis] = 1
        rows.append((slots, 3, 8, tuple(coordinates), None))
    rows.append((slots, 3, 8, (1,)*6, None))
    for null in ['stack', 'depth', 'status']:
        rows.append((slots, 3, 8, (0,)*6, null))
    for slots, depth, capacity, coordinates, null in rows:
        expected = oracle(kind, bits, slots, depth, capacity, coordinates, null)
        observed = program.execute(slots, depth, capacity, coordinates, null)
        if {key: observed[key] for key in expected} != expected:
            raise ValueError(f'PTX scalar reference mismatch: {kind}/{bits}')
        writes = [x for x in observed['trace'] if x[0] == 'write']
        if any(coordinates) or null == 'status':
            if observed['trace']:
                raise ValueError('non-owner/null-status touched global memory')
        elif expected['status'] != 0:
            if writes != [('write', 0x20000, 4)]:
                raise ValueError('failed preflight changed stack/depth storage')
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fslc', required=True, type=pathlib.Path)
    parser.add_argument('--clang', required=True)
    parser.add_argument('--ptxas', help='required assembly gate when supplied, Linux CUDA toolkit')
    parser.add_argument('--update-artifacts', action='store_true')
    parser.add_argument('--output', type=pathlib.Path, default=pathlib.Path('artifacts/gpu-projection.json'))
    args = parser.parse_args()
    report = {'format': 'fission-gpu-projection-v1', 'status': 'failed', 'profiles': 0,
              'ptx_scalar_reference_states': 0, 'cuda_device_compiles': 0,
              'ptxas_cubins': 0, 'refusals': [], 'artifact_hashes': {},
              'sample_cubins': {},
              'hardware_execution': 'not-run',
              'scope': 'single-owner stack bit-vector reference kernels; no GPU guest decode, SIMT, synchronization or recovered kernel ABI'}
    try:
        fslc = args.fslc.resolve()
        report['compiler_sha256'] = hashlib.sha256(fslc.read_bytes()).hexdigest()
        report['clang_version'] = checked([args.clang, '--version']).stdout.splitlines()[0]
        if args.ptxas:
            report['ptxas_version'] = checked([args.ptxas, '--version']).stdout.strip()
        golden = ROOT/'experiments/gpu/fir-projections'
        lock = tomllib.loads((golden/'projection.lock.toml').read_text())
        with tempfile.TemporaryDirectory(prefix='fsl-gpu-projections-') as directory:
            temp = pathlib.Path(directory)
            samples = [(f'{sign}{bits}-{kind}', kind, bits, source(f'{sign}{bits}', body))
                       for bits in [1, 8, 16, 32, 64] for sign in ['i', 'u'] for kind, body in BODIES.items()]
            samples.append(('jvm-iadd', 'add', 32, (golden/'jvm-iadd.fsl').read_text()))
            for name, kind, bits, text in samples:
                src, package = temp/(name+'.fsl'), temp/(name+'.fslc')
                src.write_text(text)
                checked([fslc, 'compile', src, package])
                for layer, suffix in [('cuda', 'cu'), ('ptx', 'ptx')]:
                    checked([fslc, 'emit', package, '60', layer, temp/(name+'.'+suffix)])
                if name == 'jvm-iadd':
                    checked([fslc, 'emit', package, '60', 'fir', temp/(name+'.fir')])
                    for suffix in ['cu', 'ptx', 'fir']:
                        data = (temp/(name+'.'+suffix)).read_bytes()
                        if args.update_artifacts:
                            (golden/(name+'.'+suffix)).write_bytes(data)
                        elif (golden/(name+'.'+suffix)).read_bytes() != data:
                            raise ValueError('projection artifact mismatch: '+suffix)
                        report['artifact_hashes'][name+'.'+suffix] = hashlib.sha256(data).hexdigest()
                        if not args.update_artifacts and report['artifact_hashes'][name+'.'+suffix] != lock['artifact_sha256'][name+'.'+suffix]:
                            raise ValueError('locked projection hash mismatch: '+suffix)
                    report['package_sha256'] = hashlib.sha256(package.read_bytes()).hexdigest()
                    if report['package_sha256'] != lock['package_sha256']:
                        raise ValueError('portable package hash mismatch')
                program = Program((temp/(name+'.ptx')).read_text())
                report['ptx_scalar_reference_states'] += state_checks(program, kind, bits)
                report['profiles'] += 1
                for opt in ['0', '2']:
                    clang_ptx = temp/(name+'-clang-O'+opt+'.ptx')
                    checked([args.clang, '--target=x86_64-linux-gnu', '-x', 'cuda', '--cuda-device-only',
                             '--cuda-gpu-arch=sm_70', '-nocudainc', '-nocudalib', '-Xclang', '-target-feature',
                             '-Xclang', '+ptx70', '-O'+opt, '-S', temp/(name+'.cu'), '-o', clang_ptx])
                    if '.entry fsl_execute(' not in clang_ptx.read_text():
                        raise ValueError('CUDA compile lost kernel entry')
                    report['cuda_device_compiles'] += 1
                    if args.ptxas:
                        cubin = temp/(name+'-clang-O'+opt+'.cubin')
                        checked([args.ptxas, '-arch=sm_70', clang_ptx, '-o', cubin])
                        metadata = assembled_cubin(cubin)
                        if name == 'jvm-iadd':
                            output = args.output.parent/'gpu-projection'
                            output.mkdir(parents=True, exist_ok=True)
                            (output/cubin.name).write_bytes(cubin.read_bytes())
                            report['sample_cubins'][cubin.name] = metadata
                        report['ptxas_cubins'] += 1
                if args.ptxas:
                    cubin = temp/(name+'.cubin')
                    checked([args.ptxas, '-arch=sm_70', temp/(name+'.ptx'), '-o', cubin])
                    metadata = assembled_cubin(cubin)
                    if name == 'jvm-iadd':
                        output = args.output.parent/'gpu-projection'
                        output.mkdir(parents=True, exist_ok=True)
                        (output/cubin.name).write_bytes(cubin.read_bytes())
                        report['sample_cubins'][cubin.name] = metadata
                    report['ptxas_cubins'] += 1
            product = fslc.parents[2] # target/debug/fslc inside compiler checkout
            refusal_sources = [("u128", source('u128', BODIES['add']))]
            for name in ['amdgcn-gfx900-sadd-u32', 'amdgcn-gfx900-vadd-u32-wave64', 'amdgcn-gfx900']:
                refusal_sources.append((name, (product/'crates/fission-fsl/specs'/(name+'.fsl')).read_text()))
            for name, text in refusal_sources:
                src, package = temp/(name+'.fsl'), temp/(name+'.fslc')
                src.write_text(text); checked([fslc, 'compile', src, package])
                command = ['emit', package, '60'] if name == 'u128' else ['emit-bytes', package]
                if name != 'u128':
                    # Read names/valid bytes from the fixture contract, not a new decoder.
                    fields = {'amdgcn-gfx900-sadd-u32': ['amdgcn.gfx900.sadd_u32', '00010280'],
                              'amdgcn-gfx900-vadd-u32-wave64': ['amdgcn.gfx900.vadd_u32.wave64', '00030068'],
                              'amdgcn-gfx900': ['amdgcn.gfx900', '810080be']}
                    command += fields[name]
                for layer in ['cuda', 'ptx']:
                    target = temp/(name+'-refused-'+layer)
                    result = subprocess.run([str(x) for x in [fslc, *command, layer, target]], capture_output=True, text=True)
                    if result.returncode == 0 or target.exists():
                        raise ValueError('unsupported GPU projection accepted: '+name+'/'+layer)
                    if not any(reason in result.stderr for reason in ['integer widths', 'state effects', 'unsupported semantics']):
                        raise ValueError('refusal failed before semantic gate: '+result.stderr)
                    report['refusals'].append({'source': name, 'layer': layer, 'reason': result.stderr.strip()})
        report['status'] = 'passed'
    except (OSError, ValueError) as exc:
        report['error'] = str(exc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ['artifact_hashes', 'refusals']}, indent=2))
    return 0 if report['status'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())

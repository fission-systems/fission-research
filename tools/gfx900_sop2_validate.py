#!/usr/bin/env python3
"""Compare the authored SOP2 FSL against LLVM and check byte round trips.

This checks encoding/SGPR fields, not GPU execution semantics. The FSL opcode
reference and LLVM oracle share LLVM lineage; agreement is not a semantic proof.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import pathlib
import random
import re
import subprocess
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = 'amdgcn.gfx900.sop2'


def run(args, *, input=None, accepted=True):
    result = subprocess.run([str(a) for a in args], input=input, text=True,
                            capture_output=True, timeout=120)
    if result.returncode != (0 if accepted else 1):
        raise ValueError(f"unexpected exit {result.returncode}: {args[:2]}: {result.stderr}")
    return result.stdout


def assembly(name, registers):
    wide = name.endswith('64')
    pair = [wide, wide, wide and not name.startswith(('s_lshl', 's_lshr'))]
    return name + ' ' + ', '.join(f's[{v}:{v+1}]' if p else f's{v}' for v, p in zip(registers, pair))


def validate(fslc, llvm_mc, llvm_objdump, work):
    source = ROOT / 'specs/gpu/amdgcn/gfx900-sop2.fsl'
    package = work / 'sop2.fslc'
    run([fslc, 'compile', source, package])
    # Check deterministic packaging, separately from golden historical artifacts.
    lock = tomllib.loads((ROOT / 'experiments/gpu/gfx900-sop2/source.lock.toml').read_text())
    if hashlib.sha256(package.read_bytes()).hexdigest() != lock['package_sha256']:
        raise ValueError('FSL package hash differs from the reviewed snapshot')
    second = work / 'second.fslc'
    run([fslc, 'compile', source, second])
    if package.read_bytes() != second.read_bytes():
        raise ValueError('FSL package compilation is nondeterministic')
    with (ROOT / 'experiments/gpu/gfx900-sop2/additions.tsv').open() as stream:
        additions = list(csv.DictReader(stream, delimiter='\t'))
    if len(additions) != 32 or any(row['category'] != 'spec-only' for row in additions):
        raise ValueError('unexpected extension ledger')
    names = [row['instruction'] for row in additions]
    # Register boundaries plus seeded operand combinations; no encoding constants
    # from the .fsl are used to produce expected bytes.
    rng = random.Random(900)
    cases = []
    for name in names:
        for i in range(8):
            regs = [0, 2, 94] if i == 0 else [rng.randrange(48)*2 for _ in range(3)]
            if not name.endswith('64') or name.startswith(('s_lshl', 's_lshr')):
                regs[2] = 95 if i == 0 else rng.randrange(96)
            edits = [92, regs[1], regs[2]]
            cases.append((name, regs, edits))
    asm = '\n'.join(assembly(name, regs) for name, regs, _ in cases) + '\n'
    edited_asm = '\n'.join(assembly(name, edits) for name, _, edits in cases) + '\n'
    def encode(text):
        listing = run([llvm_mc, '-triple=amdgcn-amd-amdhsa', '-mcpu=gfx900', '-show-encoding'], input=text)
        records = re.findall(r'encoding: \[([^\]]+)\]', listing)
        blobs = [bytes(int(v.strip(), 16) for v in record.split(',')) for record in records]
        if len(blobs) != len(cases) or any(len(blob) != 4 for blob in blobs):
            raise ValueError('oracle corpus is incomplete or contains extended instructions')
        return blobs
    blobs, edited_blobs = encode(asm), encode(edited_asm)
    obj = work / 'oracle.o'
    run([llvm_mc, '-triple=amdgcn-amd-amdhsa', '-mcpu=gfx900', '-filetype=obj', '-o', obj], input=asm)
    disasm = run([llvm_objdump, '-d', '--mcpu=gfx900', obj])
    observed = [line.split('//')[0].strip() for line in disasm.splitlines()
                if re.search(r'//\s*[0-9a-fA-F]+:', line)]
    if observed != asm.splitlines():
        # whitespace varies across LLVM releases; preserve operand spelling.
        normalize = lambda text: re.sub(r'\s+', ' ', text).strip()
        if list(map(normalize, observed)) != list(map(normalize, asm.splitlines())):
            raise ValueError('LLVM assembler/disassembler disagree on corpus operands')
    if hashlib.sha256(b''.join(blobs)).hexdigest() != lock['corpus_sha256']:
        raise ValueError('LLVM corpus hash differs from the reviewed snapshot')
    output = work / 'encoded.bin'
    for (name, registers, _), blob, edited in zip(cases, blobs, edited_blobs):
        decoded = run([fslc, 'decode-bytes', package, PROFILE, blob.hex()])
        instruction = re.search(r'^instruction (\w+) encoding=', decoded, re.M)
        fields = dict((key, int(value)) for key, value in re.findall(r'^  (\w+)=(\d+) ', decoded, re.M))
        if instruction is None or instruction[1] != name:
            raise ValueError('FSL instruction differs from oracle')
        if fields != dict(zip(['destination', 'source0', 'source1'], registers)):
            raise ValueError('FSL SGPR fields differ from oracle assembly operands')
        if 'unsupported semantics' not in decoded:
            raise ValueError('GPU semantics unexpectedly claimed implemented')
        run([fslc, 'reencode', package, PROFILE, blob.hex(), output])
        if output.read_bytes() != blob:
            raise ValueError('unchanged encoding round trip differs')
        run([fslc, 'reencode', package, PROFILE, blob.hex(), output, 'destination=92'])
        if output.read_bytes() != edited:
            raise ValueError('edited encoding differs from LLVM reassembly')
    rejected = 0
    for blob in blobs[::8]:
        for byte_index, value in [(0, 255), (1, 255), (2, 96)]:
            bad = bytearray(blob)
            bad[byte_index] = value
            run([fslc, 'decode-bytes', package, PROFILE, bad.hex()], accepted=False)
            rejected += 1
    for profile, raw in [(PROFILE, '00000000'), (PROFILE, '0000'), ('wrong.profile', blobs[0].hex())]:
        run([fslc, 'decode-bytes', package, profile, raw], accepted=False)
        rejected += 1
    return {'status': 'passed', 'profile': PROFILE, 'instructions': len(names),
            'corpus_cases': len(cases), 'decode_field_comparisons': len(cases),
            'unchanged_roundtrips': len(cases), 'edited_oracle_comparisons': len(cases),
            'rejected_inputs': rejected, 'extensions': {'spec_only': 32, 'generic_primitive': 0, 'architecture_escape': 0},
            'scope': 'SGPR 0..95, aligned pairs; register-only encoding',
            'gpu_execution_semantics': 'unsupported',
            'oracle_limit': 'Separate LLVM executable; FSL opcode reference shares LLVM lineage.',
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
            'corpus_sha256': hashlib.sha256(b''.join(blobs)).hexdigest(),
            'fslc_binary_sha256': hashlib.sha256(pathlib.Path(fslc).read_bytes()).hexdigest(),
            'llvm_mc_version': run([llvm_mc, '--version']).splitlines()[0],
            'llvm_objdump_version': run([llvm_objdump, '--version']).splitlines()[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fslc', required=True, type=pathlib.Path)
    parser.add_argument('--llvm-mc', default='llvm-mc')
    parser.add_argument('--llvm-objdump', default='llvm-objdump')
    parser.add_argument('--report', type=pathlib.Path, default=ROOT / 'artifacts/gfx900-sop2.json')
    args = parser.parse_args()
    report = {'status': 'failed', 'gpu_execution_semantics': 'unsupported'}
    try:
        with tempfile.TemporaryDirectory(prefix='fission-sop2-') as directory:
            report = validate(args.fslc.resolve(), args.llvm_mc, args.llvm_objdump, pathlib.Path(directory))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fetch hash-locked Linux ptxas and its license for research CI only."""
import argparse
import hashlib
import io
import pathlib
import tomllib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def verify(data, expected, what):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(what+' SHA-256 mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=pathlib.Path, help='verify an already downloaded locked wheel')
    parser.add_argument('--output-dir', type=pathlib.Path, default=pathlib.Path('.cuda-toolchain'))
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    lock = tomllib.loads((ROOT/'data/gpu-projection-toolchain.lock.toml').read_text())
    if args.wheel:
        data = args.wheel.read_bytes()
    else:
        with urllib.request.urlopen(lock['url'], timeout=30) as response:
            data = response.read(lock['size']+1)
    if len(data) != lock['size']:
        raise ValueError('wheel size mismatch')
    verify(data, lock['sha256'], 'wheel')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('duplicate wheel members')
        executable = archive.read(lock['executable_member'])
        license_text = archive.read(lock['license_member'])
    verify(executable, lock['executable_sha256'], 'ptxas')
    verify(license_text, lock['license_sha256'], 'license')
    if not args.verify_only:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir/'ptxas').write_bytes(executable)
        (args.output_dir/'License.txt').write_bytes(license_text)
        (args.output_dir/'ptxas').chmod(0o755)
    print('NVIDIA ptxas '+lock['version']+': wheel, executable and license hashes verified; Linux x86_64 tool only')


if __name__ == '__main__': main()

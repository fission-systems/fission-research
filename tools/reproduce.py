#!/usr/bin/env python3
"""Regenerate locked research artifacts without modifying tracked outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: pathlib.Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"hash mismatch: {path}: expected {expected}, got {actual}")


def reproduce(root: pathlib.Path, manifest: dict, work: pathlib.Path) -> list[dict]:
    for item in manifest['inputs']:
        verify(root / item['path'], item['sha256'])
    rows = []
    for job in manifest['jobs']:
        expected = root / job['artifact']
        verify(expected, job['sha256'])
        output = work / job['artifact']
        output.parent.mkdir(parents=True, exist_ok=True)
        args = [sys.executable] + [arg.replace('{work}', str(work)) for arg in job['args']]
        print(f"reproduce: {job['name']}", flush=True)
        result = subprocess.run(args, cwd=root, capture_output=True, timeout=600, check=True)
        if job.get('stdout', False):
            output.write_bytes(result.stdout)
        verify(output, job['sha256'])
        rows.append({'name': job['name'], 'artifact': job['artifact'],
                     'sha256': sha256(output), 'status': 'identical'})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=pathlib.Path, default=ROOT / 'artifacts/reproduction.json')
    args = parser.parse_args()
    report = {'status': 'failed', 'scope': 'locked research artifacts; no execution equivalence claim'}
    try:
        manifest = tomllib.loads((ROOT / 'experiments/reproduction.lock.toml').read_text())
        head = subprocess.run(['git', '-C', str(ROOT / 'Fission'), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, check=True).stdout.strip()
        if head != manifest['sla_source_commit']:
            raise ValueError('SLA source checkout must match the pinned commit; see docs/reproduction.md')
        with tempfile.TemporaryDirectory(prefix='fission-reproduce-') as directory:
            report['jobs'] = reproduce(ROOT, manifest, pathlib.Path(directory))
        report['status'] = 'passed'
        report['sla_source_commit'] = head
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            report['stderr'] = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr
        print(f"reproduce: {exc}", file=sys.stderr)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())

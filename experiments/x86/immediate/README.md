# x86 displacement / literal split and immediate memory stores

2026-10-11. This is a bounded research continuation of the
[ordered store/frame slice](../stateful/README.md).

## What is implemented

- `owned-x86-v2` and `FSLXPKG2` preserve explicit wrapper format identity.
  Canonical FIR remains v11. V1 package bytes/projections retain their old meaning.
- The optional pool has 48 encoding rules and 150 FIR bodies. Nine new bodies
  express MOV C7 immediate stores for operand/address widths 16/32/64.
  The count includes width combinations, not 150 distinct instructions.
- A normalized seven-field token has a 64-bit address addend and independent
  32-bit literal. Legacy six-field tokens stay unchanged. The address addend
  includes resolved IP-relative addresses; original bytes remain in origins.
- Generic operand syntax supplies ModRM/SIB, displacement, prefixes and length.
  FIR supplies truncation, sign extension and ordered stores. No new FIR
  primitive or architecture-specific arithmetic executor is added.

Extension accounting: **9 authored FSL bodies**, **0 new encoding rules**,
**0 new generic semantic primitives**, **1 versioned generic operand binding
extension**, **0 architecture semantic escapes**. This is not a claim that the
feature was added solely through data: the shared decoder/binder/package and
C field-array generation changed to support the seventh operand field.

## Locked actual binaries and independent observations

Clang/LLD 22.1.8 compiled three SysV AMD64 C functions at O2. Each computes the
old two-word sum, then writes a literal at RDI+8, then returns. Fixtures include:

| Fixture | Write | Bytes in function |
|---|---|---:|
| imm16 | 0x9876, upper neighboring bytes preserved | 14 |
| imm32 | 0x87654321, upper neighboring bytes preserved | 15 |
| imm64 | imm32 -7 sign extended to u64 | 16 |

Sources, complete ELFs, original bytes, compile command, generated package hash,
FSL/register sources, twelve outputs and machine adapter sources are pinned in
[source.lock.json](source.lock.json). Selected spans are at 0x401000, offset4096;
no relocated or PC-relative references occur in these three spans. IP-relative,
SIB, negative displacement, mode and prefix behavior are separate synthetic tests.

The shared validator uses boundary/deterministic cases and an arithmetic/state
model independent of the FIR implementation. It checks 256 states per fixture:
768 FIR full modeled GPR/flags/160-byte memory/exit states and 6,144 C/Rust O0/O2
success/rollback rows. Budget 3 follows the actual immediate store; rollback
preserves all modeled caller state and memory. Native or Rosetta64 adapters
execute the original byte spans: 768 cases checking result, six defined flags,
two external words, preserved RBP and balanced SP.

Hardware observations exclude full register/stack snapshots, CPU faults,
concurrency and general ABI recovery. The memory/transaction/scratch contract
is the earlier bounded flat-byte model, not an architectural fault model.
All three actual spans are 64-bit; 16/32-bit modes have synthetic coverage here.

The actual SLA/canonical P-code evaluator is an implementation comparison, not
a Ghidra decompiler-output baseline. Current comparison agrees on modeled GPRs,
exit and memory; AF differs 96/256 times per fixture because the legacy spec
omits AF. No IR accuracy superiority or metadata ablation is claimed.

[Local report](validation-local-2026-10-11.json) records the clean committed
native snapshot and Rosetta64 observations. Native full nextest71, Python29,
strict FSL Clippy with/without x86 and format checks passed. Linux CI is a
separate execution and must be checked live.

## Reproduce

```sh
python3 tools/x86_migrate.py --fission-root Fission --memory-immediates \
  --output-dir artifacts/x86-immediate-specs
python3 tools/x86_stateful_validate.py \
  --fixture-root experiments/x86/immediate \
  --fsl-x86 /absolute/path/to/fsl-x86 \
  --pcode-baseline /absolute/path/to/x86_fir_baseline \
  --baseline-root /absolute/path/to/Fission \
  --cc clang-18 --rustc 'rustup run 1.98.1 rustc' \
  --machine-host native-x86 --report artifacts/x86-immediate.json
```

The report preserves input/output/source/executable/tool/checkout hashes and
replaces stale success on failure. Fixture metadata supplies expected literal
bytes independently; it is not read from decoded FIR. The shared validator's
store oracle and backward-compatible generator have Python regression coverage.

## Remaining boundaries

Other memory ALU immediate destinations refuse until authored semantics exist.
Byte/high-byte registers, LOCK/REP/segment effects, faults, CALL/callee ABI,
recovered guest CFG joins/loops and full x86/SLEIGH replacement remain incomplete.
Normal source prototypes are candidates. No external decoder dependency was added.

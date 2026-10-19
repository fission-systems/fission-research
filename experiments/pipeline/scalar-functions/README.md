# Owned x86 ELF → FIR → scalar C functions

Native pin: [`0364df0634299c8106b50dcdaa94daee4b181f32`](https://github.com/fission-systems/Fission/commit/0364df0634299c8106b50dcdaa94daee4b181f32),
experimental branch `codex/fsl-jvm-iadd-parity`, PR #176.
Product SLEIGH remains operational. No new computation domain or library
dependency was added.

## Implemented contract

An owned `.fslpc` catalog selects the canonical ELF loader profile and pins the
existing 48-rule / 150-body x86 package. Caller-selected executable bytes lift
to canonical FIR. Shared abstract transfers recover instruction CFG edges,
return/control dependencies and affine register facts. Unknown FIR conditions
explore both alternatives. The acyclic path checker admits a restricted,
explicitly selected `sysv-amd64-u64-leaf-v1` contract:

- Return/control results depend only on integer argument registers.
- Preserved GPRs retain entry identities and RSP increases by eight.
- The sole memory load is the original stack return token; it remains the
  exact return PC. Data loads, dead faulting loads and stores refuse.
- Loops, indirect non-return flow, missing successors, unknown entry flags and
  non-argument dependencies refuse. Path budgets fail closed.

The public C function accepts a `uint64_t` argument prefix and returns `uint64_t`.
Its internal dispatcher and state helpers are emitted by the existing canonical
FIR backend. There is no SLEIGH, P-code, NIR/HIR, new executable IR or duplicate
x86 arithmetic implementation. The smallest observed argument-register prefix
is **not the original source prototype or parameter count**. ABI selection and
candidate boundaries remain explicit caller inputs.

## Measured locally

[The macOS report](validation-macos.json) records a clean native pin:

- Three authored freestanding C functions, each compiled at O1 and O2: six
  compilation cases, with arithmetic, masking and a two-return conditional CFG.
  O1/O2 produce identical bytes for each function in this local toolchain;
  these are three distinct byte sequences, not six independent algorithms.
- LLVM/Clang 22.1.8 builds real ELF files. The flag
  `-mllvm -x86-cmov-converter-force-all` constrains output to the existing owned
  branch subset. Boundaries come from compiler ELF symbols.
- 2,048 input triples per compilation case: 512 boundary combinations and 1,536
  seeded random inputs. Exact relocation-free function bytes extracted from
  ELF execute through Rosetta x86-64. A separately compiled host-native source
  reference also matches, for 12,288 source-reference comparisons.
- Generated C compiles at O0 and O2 with fatal undefined-behavior sanitization.
  All **24,576 original-byte versus recompiled-C comparisons** match.
- Native full fission-fsl nextest: 123 passed with no skipped/leaky diagnostics in the clean-pin rerun. Strict
  Clippy, formatting and downstream decompiler/CLI checks pass. Focused catalog,
  ABI/CFG and refusal checks: nine passed.

`capture/` preserves the six ELF files, source C, disassembly, generated C,
canonical FIR and projection/loader reports. The ABI source and catalog are
copied from the pinned compiler. `source.lock.json` hashes the frozen capture;
the capture checker verifies its consistency. Host compilers can produce
different instruction selections and hashes; the fresh execution driver checks
behavior rather than requiring a different LLVM version to reproduce local
binaries byte for byte.

## Reproduce

```sh
cargo build --manifest-path /path/to/Fission/Cargo.toml \
  -p fission-fsl --features x86 --bin fsl-x86
python3 tools/scalar_function_capture_check.py
python3 tools/scalar_function_validate.py --fission /path/to/Fission \
  --cli /path/to/Fission/target/debug/fsl-x86 \
  --output artifacts/scalar-functions.json --keep artifacts/scalar-functions
```

Requirements: Clang, LLD, LLVM objdump/objcopy/nm/readelf and a native x86-64
host or macOS with Rosetta. On macOS, `--host-cc /usr/bin/clang` uses the SDK
compiler for host executables. Linux supports optional `--trace /usr/bin/strace`.
The new `owned-scalar-functions` CI job fetches only crates/build configuration,
checks absence of `utils`/`vendor`, executes on Linux x86-64 and audits seven
CLI file traces for attempted legacy specification access. Its result must be
observed independently; the local report has no file tracing.

## Remaining limits

This is an authored scalar leaf experiment, not a DecBench score or a general
function decompiler. Existing DecBench eligibility remains the historical
0/250 measurement; this new route has not been evaluated on that corpus.
There is no automatic source signature recovery, function discovery, calls,
loops, data memory, stack arguments, float/aggregate ABI, x86-32 function
projection, fault model or formal original/output equivalence proof. Complete
SLEIGH asset migration and product consumer cutover remain open. The next
useful step is reusable memory/call/loop contracts and an independently selected
real corpus, with refusal counts retained.

# Integer-controlled quantum CFG — 2026-10-17

Owned native compiler: `f15f0293da424b454bceeca7a2d4e4f16c86f5bb`, experimental
Fission branch `codex/fsl-jvm-iadd-parity`. Source and package are FSL/FSLC;
JSON contains diagnostic evidence and provenance only. No new runtime dependency.

## Implemented scope

The existing single FIR integer operations now execute alongside quantum effects:
constants, modular add/sub, and/or/xor, eq/unsigned-less/signed-less, and strict
width extension/truncation. Classical SSA slots hold exact 1..64 bit patterns;
signed values use two's complement. Measurements and branch/feed-forward
conditions remain unsigned u1. Parallel edge arguments carry loop counters.
The strict entry point still rejects cycles; the bounded entry point follows
validated CFG edges with step/split/branch budgets, retaining incomplete state
and probability rather than returning a terminal output.

| Authored family | Bodies | Input states per body |
| --- | ---: | ---: |
| u8/u16/u32/u64 decrementing counters, 0/1/3/6 iterations | 16 | 21 |
| i8/i64 counters from -2 to 1 | 2 | 21 |
| u1/u8/u32/u64/i8/i64 arithmetic boundary pairs | 18 | 21 |
| Signed/unsigned 8-to-64 extension, 64-to-16-to-8 truncation | 4 | 21 |
| Measurement-selected trip count | 1 | 21 |
| Cycle with two entry blocks and measurement-selected entry | 1 | 21 |

Total: 42 bodies / 882 inputs / 1,344 instrument comparisons, including strict
and bounded execution for 22 linear bodies. Each 2-qubit input set contains basis,
complex product and complex entangled states. Python stdlib uses arbitrary-size
integers with explicit modulo and closed-form loop summaries, plus unnormalized
dense density operators. Native uses fixed-width integer helpers and amplitude
branches. Compare exact SSA slots (including None and full u64), ordered
measurement history, conditional density, aggregate density and probability.
A zero/one-iteration path must retain unexecuted slots as None. The two-entry
cycle checks arbitrary admitted CFG traversal without a structured-loop rewrite.
No parser/conformance independence or whole-program equivalence is claimed.

All 42 unsupported OpenQASM projections refuse before creating output. One
stopped-counter CLI check verifies nonzero exit, `result:null`, exact SSA slots
and preserved probability. Native tests additionally cover parallel cyclic
arguments with u64 values, budget stop, invalid conditions and untaken foreign
effects. The old OpenQASM subset remains unchanged.

## Reproduce

```sh
cargo build --locked --manifest-path /path/to/Fission/Cargo.toml -p fission-fsl --bin fslc
python3 tools/quantum_integer_probe.py --fslc /path/to/Fission/target/debug/fslc --compiler-root /path/to/Fission
python3 -m unittest discover -s tests -p test_quantum_integer_probe.py -v
```

The probe freezes the executable and source hashes, records revision/dirty state,
and verifies package/oracle/input hashes. `source.lock.json` pins source, native
revision, oracle and archived report hashes. Existing ideal/channel/calibration
oracles and original evidence archives remain untouched. Separate research CI
job `quantum-integer-cfg` fetches the exact owned compiler pin without utils or
vendor assets, reruns all four experiments and uploads raw evidence.

## Limits and device access

The user confirmed no currently connected QPU. No hardware request was submitted;
no current calibration was fetched. This stage does not add live-device transport,
QPU execution, current-device noise fitting/correction, pulse timing, general
OpenQASM, dynamic qubit addressing, memory/calls or mixed CPU/GPU effects. The
historical 2024 Manila parameter experiment remains a declared mathematical
model. CFG support means traversal within this bounded operation subset; general
quantum program support remains incomplete. No new DecBench score, x86 execution
corpus measurement, speedup or formal equivalence claim.

## Local observations

Clean native pin: 26 quantum integration tests; full crate with x86 110 passed,
0 skipped; strict Clippy (default/x86) and workspace fmt passed. Research suite
71 passed with the native x86 adapter fixture enabled. New maximum instrument
error is 4.440892098500626e-16 (tolerance 2e-10). Archived reports:

- `validation-local.json`: 1,344 new comparisons, 42 projection refusals, partial stop.
- `ideal-regression-local.json`: old 308 comparisons, unchanged package/QASM hashes.
- `channels-regression-local.json`: old 678 comparisons, unchanged package hash.
- `execution-regression-local.json`: old 420 idle comparisons, 6 loop inputs and partial retry.

CI results will be recorded with their exact run and compiler revision; these
local results do not certify unobserved remote jobs.

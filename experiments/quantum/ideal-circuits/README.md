# Quantum effects in canonical FIR — 2026-10-17

Native compiler: `1f5e4c5b0aa10f7fba29587699906e42dfc3878c` on experimental branch
`codex/fsl-jvm-iadd-parity`. [PR #176 — Project Fission: A Unified Semantic Engine](https://github.com/fission-systems/Fission/pull/176).

## Implemented slice

The same `FirOp` table now has H/X/Z/CX, Z measurement, reset and classical u1
feed-forward X. FSL compiles these to v12 FSLC. Earlier nonquantum sources retain
their previous versions/bytes. There is no second quantum IR or new dependency.
Logical qubit indices name subsystems of a joint state. CPU/GPU/VM arithmetic
is not used to pretend that a qubit is a classical bit.

The classical-host reference accepts explicit pure joint inputs, enumerates
measurement outcomes with probabilities and post-states, and represents mixed
outputs as weighted ensembles. Reset's hidden outcomes are summed when producing
a density matrix; they are not exposed as observable measurements. Bit0 of a
basis index is qubit0. C/Rust/Go/CUDA/PTX/native JIT/AOT consumers reject quantum
semantics; this slice does not generate a C quantum simulator or QPU executable.

Reference bounds: 1..8 state qubits, 256 linear ops, 64 classical SSA slots and 12
measurement/reset effects (at most 4096 enumerated branches). The canonical op
encoding supports logical indices 0..255; interpretation/export admission remains
separate. This implementation has no resource allocator, linear type system,
explicit effect SSA or general mixed classical/quantum CFG.

Restricted OpenQASM 3.0 input/output supports fixed q/m names, static indices,
dense single-assignment classical bits, supported gates/measure/reset and one
conditional-X shape. Other constructs refuse. Source SHA is retained in package
evidence. Import returns declared qubit count separately; callers must retain
it, including unused qubits, alongside the explicit initial state. `.fslc`
stores instruction effects, not the whole OpenQASM program envelope. No default
zero-state assumption follows from a QASM declaration. The sample basis:0 runs
explicitly impose that input. Full QASM/QIR import, arbitrary gates/angles,
physical qubits, pulses, device layout/calibration and noise are outside scope.

## Evidence

Seven authored circuit bodies in [circuits.fsl](circuits.fsl): Bell measurement,
coherent Bell, H;H, H;Z;H, measurement feed-forward, entangled reset and measured
GHZ. Their opcode bytes are synthetic logical-profile selectors, not hardware
ISA encodings. This is not binary quantum decompilation.

[tools/quantum_validate.py](../../../tools/quantum_validate.py) uses Python stdlib
dense density-matrix multiplication and Kraus channels, separately from the
native state-vector interpreter. 154 basis/complex-product/entangled initial
states supply 308 native/original-QASM-roundtrip comparisons. It checks measurement
records/probabilities, each record's unnormalized density operator, post-state
normalization and the total density matrix, within 2e-10. Native and own QASM
roundtrip outputs must agree. This does not independently validate a full QASM
parser and is not a proof for arbitrary programs/states.

The oracle regression includes a lost-coherence counterexample: a classical
00/11 mixture must not pass as a coherent Bell state even though Z measurement
histograms match. Native tests separately cover complex interference, collapse,
reset mixtures, feed-forward, classical constants, small nonzero probability,
resource/type/SSA errors and foreign-backend refusal.

All calculations use f64; rounding and underflow limit the claims. No exact
symbolic identity, formal equivalence, hardware measurement or quantum speedup
is claimed. A GPU/CPU simulator backend and scalable Clifford/stabilizer method
would be separate future work.

## Reproduce

```sh
# In the pinned compiler checkout:
cargo build --locked -p fission-fsl --bin fslc
cargo nextest run --locked -p fission-fsl --features x86 --test quantum
# In this research repository:
python3 tools/quantum_validate.py \
  --fslc /absolute/compiler/target/debug/fslc \
  --compiler-root /absolute/compiler
```

A quantum CI job fetches the pinned compiler source, builds without legacy assets,
runs the focused tests and regenerates the numerical report. Existing x86 and
GPU gates keep their own historical compiler pins. CI completion is recorded
separately from local evidence. The checker snapshots the native executable so
concurrent Cargo builds cannot replace it during measurement.

Semantic sources: [OpenQASM reset/measurement](https://openqasm.com/versions/3.0/language/insts.html),
[classical control](https://openqasm.com/versions/3.0/language/classical.html),
[standard gate definitions](https://github.com/openqasm/openqasm/blob/main/examples/stdgates.inc).
Source code/fixture/oracle were authored here; no vendor runtime is linked.

## Archived local artifacts

- [validation-local.json](validation-local.json): clean compiler provenance,
 154 inputs / 308 conditional-state comparisons; maximum absolute error about
 1e-15, with 2e-10 acceptance tolerance.
- [source.lock.json](source.lock.json): compiler pin and fixture/package/QASM/
 validator/report/sample hashes. CI regenerates the package and QASM and checks
 numerical behavior; host-specific diagnostic report hashes need not match.
- [Bell OpenQASM](outputs/bell.qasm) and [basis:0 simulation](outputs/bell-basis0.json):
 correlated 00/11 outputs with approximately 0.5 probability each, including joint
 post-states and classical measurement records.

The import/export program-envelope limitation and f64/hardware limits above
apply to these artifacts. Existing CPU/GPU/VM evidence has not been promoted to
quantum evidence or rerun on quantum hardware.

Local suites: Rust 93, Python 54, strict FSL Clippy with/without x86 and formatting
pass. [Existing x86 output regression](x86-regression-local.json) also passes at
the same clean compiler pin: nine source compilations, three entry-only output
comparisons and 11 refusal checks. This gate does not rerun original-x86 machine
execution or claim a DecBench score improvement.

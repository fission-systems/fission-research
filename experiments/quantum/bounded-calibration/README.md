# Bounded quantum loops and historical relaxation parameters — 2026-10-17

Native `4a3c48297d5a3649774b70f5fff40e1857eb9beb` extends the **same canonical FIR**.
There is no extra IR or runtime library dependency.

## Cyclic execution contract

`simulate_bounded` executes existing blocks, u1 conditions and parallel edge
parameters. Limits count global operations/terminators, per-path splits, and total
retained pure-state alternatives. A stopped run retains completed branches plus
the exact pending block/op positions, latest dynamic SSA values, measurement
history and split counts. It does not discard or normalize pending probability.
Repeated executions of a measurement ID append separate events to its history.

Incomplete runs cannot convert to terminal `QuantumResult`. Diagnostics contain
`result:null`, completed/frontier probability and states; the CLI exits nonzero.
Default strict simulation continues to reject cycles. Worklist order is depth
first, so partial completed probability depends on the budget/traversal. This is
not unbiased sampling or proof of termination. Resume serialization is absent.

Six basis/complex input states for an authored terminating measurement loop match
a separate density/record oracle. A retry-until-zero loop stopped at four splits
retains **15/16 completed + 1/16 pending** probability; no complete result is
claimed. Rust checks additionally cover step/branch limits, atomic stops, invalid
bounds and cyclic parallel parameter transfer. The executor still admits only
u1 classical values and the supported quantum effects, not arbitrary classical
counter arithmetic or general OpenQASM loops.

```sh
fslc simulate-quantum-bounded PACKAGE terminating_loop 1 basis:0 1000 12 4096
fslc simulate-quantum-bounded PACKAGE retry_loop 1 basis:0 1000 4 4096
# The second command returns a partial JSON envelope and exits with status 1.
```

## Historical calibration parameters

The archived upstream `props_manila.json` is IBM's fake-provider snapshot for
`ibmq_manila`, updated **2024-05-27**. It is not live calibration. Source repository
commit `7a7fa0f6d5fd2d284611b62d5546e12112a1985a`, SHA-256 and Apache-2.0 license are
recorded in the lock; the complete original JSON and license are retained here.
External JSON is source evidence, not our executable language/package format.

The importer converts T1/T2 and idle-gate length units into integer picoseconds,
rounds explicitly within 0.5ps and records residuals. Invalid T1/T2 (including
T2>2*T1), nonfinite values or unknown units refuse. No silent physical clipping.
Each physical snapshot qubit is mapped explicitly to logical **model slot 0**;
slot 1 is an abstract spectator for joint-state checks, not a claimed routed QPU.

`quantum.relaxation q,duration_ps,t1_ps,t2_ps;` (FSLC v14) is a declared
zero-temperature Markovian idle model: population exp(-t/T1), coherence exp(-t/T2).
Native code composes amplitude damping and phase flip. A separate oracle applies
the direct exponential map to density blocks. Across five snapshot rows and four
durations, **420 complex/basis/entangled state comparisons** passed (maximum error
2.7755575615628914e-16). Quantization's
density effect relative to the original parameters is measured separately and
observed 8.820099595130415e-09 and must remain <=1e-7; this finite-input bound is not a universal error proof.

This does **not** perform hardware calibration, error correction/mitigation,
readout-error fitting, gate-error or crosstalk modeling, finite-temperature
relaxation, timing recovery or prediction validated on a current device.

## Validation and reproduction

`validation-local.json` records the clean native pin, source/package/validator
hashes, exact errors, row mappings and conversion residuals. Previous ideal and
rational-channel experiments were rerun at this pin: 308 and 678 comparisons
passed with unchanged old package/QASM hashes; their new regression reports are
separate files here. Historical experiment artifacts are preserved.

Native full crate with x86: 105 passed, 0 skipped. Quantum integration: 21 passed.
Strict Clippy and formatting passed. No new CPU binary corpus or DecBench score
was measured.

```sh
python3 tools/quantum_execution_probe.py --fslc "$FISSION_ROOT/target/debug/fslc" --compiler-root "$FISSION_ROOT"
```

Model references: [IBM thermal-relaxation modeling](https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models),
[pinned historical snapshot](https://github.com/Qiskit/qiskit-ibm-runtime/blob/7a7fa0f6d5fd2d284611b62d5546e12112a1985a/qiskit_ibm_runtime/fake_provider/backends/manila/props_manila.json).

## Linux CI

[Run 39021701663 / quantum-bounded-and-inputs](https://github.com/fission-systems/fission-research/actions/runs/39021701663)
passed at the same clean native pin. Raw Linux reports are archived here and
hashed in source.lock.json. Native quantum integration 21 passed; loop/idle-model
checks and the separate reference GCC build + 200 word comparisons passed, along
with old ideal/channel regressions. Latest-head Fission full PR CI
[39021009277](https://github.com/fission-systems/Fission/actions/runs/39021009277)
also passed. Research job evidence is separate from other research workflow jobs.

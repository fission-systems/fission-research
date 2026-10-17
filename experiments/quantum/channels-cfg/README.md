# Declared noise channels and acyclic control — 2026-10-17

Native Fission commit `1fe65569e84e92bd6fd7d1a3b4772580ac8da975` adds to the
**same canonical FIR**:

- Bit flip, phase flip and zero-temperature amplitude damping channels.
- Rational probability `numerator/denominator`, each an unsigned 8-bit integer,
  denominator nonzero and numerator <= denominator. Noise selects FSLC v13;
  existing ideal programs retain v12 and previous bytes.
- Execution of canonical acyclic blocks, u1 conditions, parallel block arguments,
  joins and returns. Quantum paths keep joint post-states; a join does not measure.

No new library dependency or separate quantum IR. OpenQASM projection refuses
noise and CFG. Classical/native output backends remain unavailable for quantum
effects. Cycles, mixed CPU/GPU effects and general classical computations refuse
before execution. Bounds remain 8 simulated qubits, 256 operations, 64 u1 values
and 12 total measurement/reset/noise operations (at most 4,096 branches).

## Evidence

`validation-local.json`: **33 cases / 678 input comparisons** passed with a
Python stdlib dense-density/Kraus oracle. Thirty cases cover three channels,
five probability ratios (0/1, 1/1, 1/2, 1/255, 254/255), and both subsystems
of an entangled pair. Three CFG cases cover measurement-driven correction,
branch-local noise and measurements, u1 argument transfer and joins. Inputs
include basis, complex product and entangled states. Compare conditional density,
observable measurement IDs/history, all SSA slots (including unexecuted slots),
probability and total density; hidden environment alternatives are summed.

The reference uses unnormalized density matrices and Kraus sums; native execution
enumerates normalized state-vector alternatives. Both implement authored logical
specifications. This is an independent numerical calculation, **not** an independent
ISA/language parser oracle, proof of equivalence, hardware calibration or QPU test.
Tolerance is 2e-10; observed maximum absolute error is 4.440892098500626e-16.
Executable/source hashes are in the report.

`ideal-regression-local.json`: the prior seven ideal programs still pass their
154 inputs / 308 native and own-QASM-roundtrip comparisons with unchanged package
and QASM hashes. Original archived ideal experiment reports are preserved.

Native checks: quantum integration 15 passed; entire crate with x86 99 passed,
0 skipped; strict Clippy with x86 and formatting passed. Research Python suite
59 passed, including the native owned-entry adapter fixture.
SLEIGH library regression after integration with main: 359 passed, 3 skipped.
These synthetic checks establish no new DecBench score or CPU decompiler quality.

## Reproduce

Checkout the pinned native commit and build `fslc`. Run from this research repo:

```sh
cargo build --manifest-path "$FISSION_ROOT/Cargo.toml" --locked -p fission-fsl --bin fslc
python3 -m unittest discover -s tests -p test_quantum_channels_validate.py -v
python3 tools/quantum_channels_validate.py --compiler-root "$FISSION_ROOT" --fslc "$FISSION_ROOT/target/debug/fslc"
python3 tools/quantum_validate.py --compiler-root "$FISSION_ROOT" --fslc "$FISSION_ROOT/target/debug/fslc" --report artifacts/quantum-ideal-regression.json
```

`source.lock.json` freezes fixture, portable package, compiler commit, oracle
sources and local reports. CI has a separate `quantum-channels-cfg` job at this
native pin. New reports go into `artifacts/`; historical evidence is not replaced.

## Remaining boundaries

No real QPU binary execution, calibrated device noise, pulse/timing model, cyclic
quantum execution, general OpenQASM CFG or full quantum frontend. The selected
binary research candidate and configuration gaps are recorded in the
[QPU input investigation](../../../docs/qpu-binary-boundary.md).

Channel formula reference: [Qiskit Aer definitions](https://github.com/Qiskit/qiskit-aer/blob/main/qiskit_aer/noise/errors/standard_errors.py).
No Aer code is copied, linked or invoked by the simulator.

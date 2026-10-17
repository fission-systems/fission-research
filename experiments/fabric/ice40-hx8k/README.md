# FIR to iCE40: fixture proofs and unprogrammed bitstreams

**Observed 2026-10-18, Asia/Seoul.** Eight existing authored FIR kernels now
produce iCE40HX8K / CT256 configurations through synthesis, placement, routing
and packing. These use automatically assigned pins, without a board pinout or
electrical interface contract. No FPGA was programmed or executed. The tensor,
LIF, RC and PIM functions retain their [initial model limits](../initial-slices/README.md).
They are the same eight functions mapped to an FPGA, not eight device backends.

## What changed

```text
authored .fsl -> owned fslc -> canonical FIR -> generated 64-bit-slot RTL
                                            |       |
                      independent formula <- SAT    typed port adapter
                                                    |
                                                synth_ice40
                                                    |
                                              SB_LUT4 / SB_CARRY
                                                    |
                                                nextpnr-ice40
                                                    |
                                             routed .asc -> .bin
```

The compiler is the clean native experimental pin
`cb7b12f5c0c5c6790de58db3d0ef0de05e826d91`. This step reuses its `emit-fabric`
and `run-fabric` commands. No native Rust dependency or alternate semantic IR
was added. The new research driver reads declared widths from the existing
`axes.toml`; its target adapter only narrows physical ports and zero-extends
input slots. Workload formulas are confined to the independent oracle fixture,
not supplied as a target implementation.

## Formal boundary

`oracles.v` independently expresses unsigned wrapping add, saturation, dot,
MAC, discrete LIF, XOR, discrete RC and arithmetic diamond. For each kernel,
Yosys constructs an equality miter between the generated RTL and this oracle.
`sat -verify -prove-asserts -set-def-inputs` succeeds for **all two-valued 64-bit
input slots**, including upper input bits that typed FIR pops discard. The proof
compares complete 64-bit output slots, so it also checks that upper output bits
are zero before the adapter narrows them. Inputs have no workload range
assumptions. All eight miters proved.

Each of eight negative controls flips output bit zero in a generated RTL copy.
Each must produce a SAT counterexample and nonzero tool exit; timeouts and tool
errors cannot count as a successful rejection. Proofs use a 15-second SAT bound
and a 45-second subprocess bound. Logs, commands and counterexamples are archived.

The trusted base includes Yosys transformations/SAT and the authored formulae.
These are not independently checked proof certificates or a proof of the FIR
evaluator/compiler for arbitrary programs. **Synthesis, routing and bitstream
semantics are not formally proved.** Exploratory mapped-cell proof attempts
did not complete within 20/25-second process bounds, so no result from those
attempts is used. RC proofs concern the discrete integer recurrence, not its
continuous differential equation; LIF proofs concern one externally advanced
step, not an asynchronous neuron model.

## Observations

| Authored function | Routed logic cells / 7,680 | IO / 206 | Mapped simulation cases |
|---|---:|---:|---:|
| `fpga_add` | 10 | 24 | 65,536 |
| `dsp_sat_add` | 11 | 24 | 65,536 |
| `tensor_dot2` | 333 | 64 | 2,068 |
| `asic_mac` | 339 | 64 | 2,068 |
| `lif_step` | 32 | 25 | 2,596 |
| `pim_bank_xor` | 34 | 96 | 2,468 |
| `rc_euler_step` | 49 | 48 | 2,596 |
| `dataflow_diamond` | 354 | 48 | 2,468 |

- **8** RTL/oracle proofs; **8** counterexample controls.
- **145,336** cases compare native FIR, independent Python integer oracle and
  Icarus simulation of the iCE40-mapped netlist, using the pinned Yosys primitive
  models. Only LUT/carry cells and scope metadata are admitted after mapping.
- **8** successful HX8K/CT256 place-and-route runs, seed 1, automatic IO pins.
- **8** packed configurations, **135,100 bytes each**. Pack -> unpack -> repack
  produces identical bytes for every configuration. Separate local runs also
  reproduced all eight configuration hashes.

Mapped simulation is before placement/routing and does not simulate the
configured fabric or back-annotated timing. The configuration round-trip checks
encoding stability, not behavior. No clock, external IO delay constraints,
system timing closure, voltage compatibility, power or board runtime is claimed.
The small LC counts measure these authored functions, not device ISA coverage,
decompiler quality or accelerated performance. ASIC PDK/fabrication and the
other seven axes' device runtimes remain absent.

## Reproduce

Use Python 3.12+, the pinned native compiler, and Icarus `iverilog` / `vvp`.
Install EDA tools in a separate environment, then choose a fresh work directory:

```sh
python3 -m venv artifacts/ice40-tools
artifacts/ice40-tools/bin/pip install -r experiments/fabric/ice40-hx8k/tool-requirements.lock.txt
artifacts/ice40-tools/bin/python tools/fabric_ice40.py --fslc /path/to/Fission/target/debug/fslc --compiler-root /path/to/Fission --tool-dir artifacts/ice40-tools/bin --work artifacts/ice40-reproduce --report artifacts/ice40-reproduce.json
python3 tools/fabric_ice40_capture_check.py --report artifacts/ice40-reproduce.json
```

The driver refuses a dirty/different compiler, preexisting work directory,
unsupported port type, unproved formula, missing mutation counterexample,
unknown/stateful mapped cell, failed simulation, PnR failure, round-trip mismatch
and source/compiler drift. It has no device-programming command or network
submission path. The `computational-fabric` CI job executes this after the
historical fabric checks and uploads the generated configurations and logs.
CI status must be observed separately; local success alone is not a Linux result.

`validation-local.json` records source/executable/package hashes, installed Wasm
objects, iCE40 technology files/chip database, tool versions and result hashes.
`source.lock.json` freezes selected reviewable captures, including the actual
eight `.bin` files. Large vectors, routed JSON and complete intermediate files
are regenerable or CI artifacts. The capture checker compares proof outcomes,
utilization, vectors, RTL/adapter/scripts and actual bitstream hashes across
runs; tool logs and platform-specific executable hashes may differ.

`reference-provenance.json` records the published nextpnr wheel hash, upstream
release/license and the boundary that the bundled IceStorm source commit has
not been recovered. Yosys provenance is retained in the preceding experiment.
See the upstream [nextpnr flow](https://github.com/YosysHQ/nextpnr/blob/62e659ed6748e9f60b2a4aa25dd4fe79a9605881/README.md)
and [Yosys SAT interface](https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/sat.html).

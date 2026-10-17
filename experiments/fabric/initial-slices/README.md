# Eight computational axes: initial FIR / fabric slices

These are eight **authored research functions**, not eight supported hardware
ISAs. All use the same canonical FIR body and a new borrowed `FabricPlan` HDL /
dependency projection. No FPGA board, DSP/NPU/TPU, ASIC, neuromorphic, PIM or
analog hardware was executed. No bitstream was created.

Native implementation: `cb7b12f5c0c5c6790de58db3d0ef0de05e826d91`, experimental
branch `codex/fsl-jvm-iadd-parity`. [Domain contracts](../../../docs/computational-domains.md)
separate initial functions from the missing domain semantics and target work.

| Axis | FSL body | Initial contract |
|---|---|---|
| FPGA | `fpga_add` | 8-bit wrapping add; combinational Verilog |
| DSP | `dsp_sat_add` | Exact unsigned 8-bit saturation through wider arithmetic/masks |
| NPU / TPU | `tensor_dot2` | Fixed two-element u8 dot product promoted to u32; scalar elaboration |
| ASIC | `asic_mac` | 16-bit wrapping MAC; technology-independent synthesis |
| Neuromorphic | `lif_step` | One explicit discrete state step and spike; caller advances time |
| PIM | `pim_bank_xor` | Caller-provided u32 words XOR; same-bank placement is metadata only |
| Analog | `rc_euler_step` | Q8.8 forward-Euler RC approximation, dt=1ms / tau=4ms / floor rounding |
| Dataflow / CGRA | `dataflow_diamond` | Untimed arithmetic fork/join; canonical dependency DOT |

`axes.toml` declares port order, shape/model assumptions, time/voltage units and
unsupported features. `kernels.fsl` defines executable bit-vector behavior.
Selectors 1..8 are synthetic fixture opcodes, not device encodings. The same
source is mirrored byte-for-byte in native `specs/fabric-kernels.fsl` for the
crate's self-contained regression fixture.

## Numerical / projection implementation

Three generic operations were added to existing `IntBinaryOp`: wrapping
multiply, unsigned left shift and unsigned logical right shift. A shift count
at least the declared width yields zero, including counts >=64. Signed logical
shifts refuse. They require package v15; profiles without them keep their prior
selected version. The old stack/control consumer gap for binary operations was
also closed. C/Rust use one shared bit-vector expression emitter and guarded
host shifts. No architecture-name branch supplies arithmetic semantics.

All eight profiles are FSL definitions. Five use the new generic multiply and/or
shift operations; none requires an architecture-specific runtime escape.
Adding a new authored kernel in the admitted subset needs source only. This is
an expressiveness observation on fixtures, not ISA migration coverage.

`FabricPlan` accepts only straight-line, 1..64-bit integer stack functions, with
bounded values/ops/ports. It emits width-preserving combinational wires and
resolves stack operations to explicit input/value/output aliases. It refuses
explicit CFG, register/flag, memory, lane, guest-PC and quantum effects. Module
symbols are restricted ASCII names with `fsl_` prefixes. No new Rust dependency
or separate canonical IR was introduced.

Ports are 64-bit slots, bottom of stack first; typed pops mask their widths.
The dependency projection retains canonical op indices/value IDs. It is not a
CGRA mapping, executable alternate IR or stream/channel semantics. HDL behavior
is two-valued and untimed: no X/Z, clock, reset-domain, handshake or physical
propagation-time guarantee is claimed. Verilog simulation's `#1` observation
delay does not establish a device latency.

## Measured local scope

- Native: **118 passed, 0 skipped**, including four fabric-focused tests.
  Strict Clippy default / x86, workspace formatting and diff checks passed.
- Independent integer oracle versus native FIR and RTL: **184,424 cases**.
- C/Rust at O0/O2: **737,696 executions**; C also enabled fatal undefined-behavior
  sanitizer. These are generated state wrappers, not recovered source ABIs.
- **8 generic syntheses**, each followed by netlist simulation on its fixture
  rows (**145,336 cases**). The 16 auxiliary width/conversion fixtures were RTL /
  host checked but not synthesized.
- Wrapping add and unsigned saturating add each cover all **65,536** pairs of
  typed u8 values. Other fixtures use frozen boundary/random cases; width cases
  cover 1/8/16/32/64-bit multiply/shifts, large shift counts and signed views.
- **4 refusal probes** verify quantum, explicit block, byte memory and flag
  effects refuse without overwriting a sentinel output file. Native admission
  coverage additionally checks unsupported bodies, invalid symbols and arity.

The independent oracle is ordinary Python integer arithmetic. Icarus Verilog
13.0 executes RTL and generic netlists; Yosys 0.70 is distributed through the
separately installed YoWASP package. Generic cell counts are not LUT counts,
standard-cell area, FPGA fitting, timing closure or measured power.

An exploratory `equiv_simple` run on the 16-bit MAC did not complete before it
was manually stopped. No formal equivalence result is claimed. Finite-case
agreement, generic synthesis and scalar/discrete model support do not establish
whole-program equivalence or decompiler quality on actual binaries.

## Analog comparison is intentionally a separate bar

The 64-step stress case uses a 0 to 65535/256 volt authored step. Quantized FIR
agrees with the discrete floor-rounded oracle. Against unquantized rational
Euler, maximum observed rounding error is **2.999338706641784 codes**, below the
four-code contraction envelope for this recurrence. Against the exact
continuous RC step, the unquantized Euler trajectory differs by up to
**13.176935872736237 volts** at this full-scale input. This separates numerical
discretization error from fixed-point rounding. It is not a calibrated circuit,
continuous-time FIR implementation or a formal error-bound proof.

The discrete LIF fixture likewise has no continuous LIF equivalence, refractory
period, event queue, delay or neuromorphic-chip semantics. PIM currently has no
memory effects. Tensor shape is an authored elaboration contract; tensor storage,
layout and accelerator runtime are not implemented.

## Reproduce

External tools are for experiments only. Python 3.12+, Rust/Clang, Icarus
`iverilog`/`vvp` and the locked YoWASP tool environment are needed. Neither CIRCT,
MLIR, NEST nor ngspice is imported or linked into Fission.

```sh
python3 -m venv artifacts/fabric-tools
artifacts/fabric-tools/bin/pip install -r experiments/fabric/initial-slices/tool-requirements.lock.txt
cargo build --manifest-path /path/to/Fission/Cargo.toml --locked -p fission-fsl --bin fslc
python3 tools/fabric_probe.py --fslc /path/to/Fission/target/debug/fslc --compiler-root /path/to/Fission --yosys artifacts/fabric-tools/bin/yowasp-yosys --work artifacts/fabric-reproduce --report artifacts/fabric-reproduce.json
python3 tools/fabric_capture_check.py --report artifacts/fabric-reproduce.json
```

Use a fresh work directory for each run. The probe refuses missing tools,
unexpected results, unsupported effects and source/compiler changes during
measurement. The committed report records source/package/probe/tool hashes,
compiler revision/dirty state, case counts and per-artifact hashes. Example RTL,
DOT, generic netlists and synthesis statistics are retained separately from the
large regenerable vectors. The tool requires a little-endian host for its binary
C/Rust harness vectors. CI repeats this on Linux without hardware access.
The capture checker validates the frozen files plus regenerated package, HDL,
dependencies, input/reference rows, C/Rust sources, counts and approximation
statistics. Executable hashes and tool versions remain platform-specific;
netlist temporary names are not required to be byte-identical across hosts.
`reference-provenance.json` pins upstream tool revisions, license-file hashes,
the installed WASM object and local Icarus distribution metadata.

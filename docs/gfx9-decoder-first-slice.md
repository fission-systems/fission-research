# GFX900 decoder: first slice

## Purpose

This is the first data-driven ISA decoder experiment in the research repository. It recognizes four 32-bit GFX900 instruction patterns from the local LLVM-generated `probe.s` object and emits an annotated decode record with a candidate FIR effect and per-pattern provenance. It does not execute the instructions and is not a general AMDGPU disassembler.

GFX900 belongs to the Vega/GFX9 generation, so the profile uses AMD's Vega instruction reference rather than copying opcode values from the older GCN3 manual. One visible difference in this sample is `V_ADD_U32`: the Vega ISA lists VOP2 opcode 52, which occupies bits 30:25 and yields the high byte `0x68` in the local `v_add_u32_e32 v0, v1, v2` word `0x68000501`. The low fields decode as `SRC0=257` (`v1`), `VSRC1=2` (`v2`), and `VDST=0` (`v0`).

## Current scope

| Pattern | Match | Candidate effect |
|---|---:|---|
| `s_mov_b32 s0, 1` | `0xbe800081` | Copy inline integer 1 to scalar register `s0` |
| `v_add_u32_e32 v0, v1, v2` | `0x68000501` | Per-active-lane unsigned 32-bit addition into `v0` |
| `s_barrier` | `0xbf8a0000` | Synchronize waves in the threadgroup |
| `s_endpgm` | `0xbf810000` | Terminate the current wavefront |

The authored source is [`specs/gpu/amdgcn/gfx900-first.fsl`](../specs/gpu/amdgcn/gfx900-first.fsl), compiled to [`data/patterns/amdgpu-gfx900.json`](../data/patterns/amdgpu-gfx900.json) by [`tools/fslc_probe.py`](../tools/fslc_probe.py). The generic decoder is [`tools/fsl_decode_probe.py`](../tools/fsl_decode_probe.py); [`tools/gfx9_decode_probe.py`](../tools/gfx9_decode_probe.py) remains as a compatibility entry point. The input bytes are extracted from the `.text` section of `probe.o`, and the generated JSON is kept beside that experiment. The LLVM output remains an independent encoding/disassembly comparison artifact, not semantic ground truth.

The source stores match masks, field positions, register classes, selector ranges/cases, display templates, constraints, candidate effects, architecture scope, and evidence links. The decoder uses generic register-index and selector-table transforms rather than a Python branch per instruction form; the GFX9 selector mappings live in the source data. Patterns expressible with these primitives can be added without instruction-specific Python changes. New transform laws and extension-word handling still need to be generalized. FIR-like effects remain candidate-level and uncertain.

## Boundaries

- Four patterns only; unknown words stop decoding instead of being guessed.
- This GFX900 profile uses little-endian 32-bit words. The shared decoder also accepts other byte-aligned fixed widths and either byte order, but it does not yet handle variable-length instructions.
- No literal extension words, SDWA/DPP, relocation, branch-target resolution, dataflow, control-flow recovery, or complete register-source vocabulary.
- The barrier effect records control synchronization but does not infer memory-ordering guarantees.
- The termination effect records wavefront termination only; it does not model implicit outstanding-memory waits or the surrounding dispatch/runtime contract.
- No GPU execution or differential hardware check was performed.

## Next slice

Extend the generic algebra with bitfield composition and relative-address calculation, then add one GFX9 instruction with an extension word and one branch with a target expression. In the JVM track, add instruction operands and variable-length method-code walking. Continue only if the compiler can express these without instruction-specific decoder branches. The longer compiler/IR research plan is in [`fsl-first-compiler-slice.md`](fsl-first-compiler-slice.md); FIR projection boundaries are in [`fir-multiple-projections.md`](fir-multiple-projections.md).

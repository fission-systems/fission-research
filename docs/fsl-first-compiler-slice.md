# FSL compiler probe: GFX900 four-pattern package

Date: 2026-09-30

## Goal

Connect an authored architecture description to a compiled package and a decoder:

```text
specs/gpu/amdgcn/gfx900-first.fsl
        ↓ fslc_probe.py
data/patterns/amdgpu-gfx900.json
        ↓ fsl_decode_probe.py
annotated instruction records
```

This is the first FSL compiler experiment, not a claim that FSL is designed or complete. The source syntax is a restricted TOML profile (`language_version = 0.0.1`) chosen to make the authoring/compiled-package boundary testable before committing to a custom grammar.

## What is in the vertical slice

The source declares four GFX900 patterns: `s_mov_b32`, `v_add_u32_e32`, `s_barrier`, and `s_endpgm`. Each record contains:

- a mask/value predicate and named bit fields;
- operand extraction directives and a display template;
- constraints and uninterpreted fields for the SOPP forms;
- a candidate FIR effect summary; and
- provenance links to the Vega ISA reference and the local LLVM encoding observation.

`fslc_probe.py` validates source format/version, pattern and source identifiers, byte-aligned word width and endianness, field bounds, register-class bounds when present, selector-range/case overlap, provenance references, constraint references, fixed field values, and pairwise pattern overlap. Register classes are optional so register-free VM profiles can use the same package format. It emits a JSON package with architecture metadata, optional register classes and selector tables, pattern descriptors, the FSL source SHA-256, and compiler version. The shared [`fsl_decode_probe.py`](../tools/fsl_decode_probe.py) reads fixed-width word size and endianness from the compiled profile and uses a generic register-index and selector-table interpreter; the GFX9 scalar-source values and ranges live in the FSL data. It also resolves each pattern source ID to source metadata, so decoder output carries links/revisions alongside claims. The local `probe.text.bin` record was regenerated through this shared decoder; the earlier form-based prototype comparison is described below.

The observed input hash is `bf545049f82875a073eb48c2e2bd5f0e58ae4af81b156ed10c3bdac618b17a18`. Before replacing the earlier generated output, its instruction records were compared with the new records and matched exactly. The former output artifact had SHA-256 `ed64000e9456972e48a127df9697ed0e29dd78392a99ae8e69ab2dc96b847718`; only its hash remains after the output file was regenerated.

| Current artifact | SHA-256 |
|---|---|
| FSL source | `6de4c5bbd93f2c98e7ba30331752dae5444d84534f808958314bac9c39249519` |
| Compiled package | `f7e9b860aba761893440a05c8f7fbb5ae575e400bf8ffc04503ba514cf5e9c09` |
| Decode output (generic fixed-width record with resolved source metadata) | `ca2d6894cd703d8bee70f4213abe353084646c8a48859cc6b0a5eaa65d3afe00` |

Reproduce the current research run from the repository root:

```sh
python3 tools/fslc_probe.py specs/gpu/amdgcn/gfx900-first.fsl --output data/patterns/amdgpu-gfx900.json
python3 tools/fsl_decode_probe.py experiments/gpu/amdgpu-gfx900/probe.text.bin --output experiments/gpu/amdgpu-gfx900/probe.decode.json
```

## What this does not prove

- The source is TOML with a FSL label, not yet a purpose-built language or complete FSL syntax.
- The decoder still has a fixed generic transform vocabulary (`register_index`, `selector_table`). Ordinary patterns expressible with these primitives are data-only, but a new bit permutation, implicit operand rule, or extension-word model outside this vocabulary can still require runtime code.
- The package contains descriptive FIR effect candidates, not executable FIR semantics or an equivalence proof.
- Four patterns do not cover literal words, variable-length encodings, branches, relocations, instruction extensions, or full GFX900 decode.
- The parity comparison is only between two local decoders over the same four-word fixture; LLVM encoding/disassembly and AMD's manual remain separate evidence sources.

## Next experiments

1. Extend the transform algebra to common bitfield extraction, concatenation, sign/zero extension, and relative-address calculation; retain fail-closed behavior for unmodeled cases.
2. Add render-template validation and source maps that retain file and declaration location.
3. Model a variable-length/extension-word GFX9 instruction and a branch target. This will show whether the package can express instruction length and continuation state without a new decoder branch.
4. Import one small source/compiled-SLA constructor slice and compare source rule, SLA decision path, FSL package, and Ghidra decode result while preserving all four provenance edges.
5. **Completed first step:** add a JVM `iadd` sample with explicit stack effect and project one FIR candidate into C/Rust, stack IR, sequential IR, analysis graph, and an AI evidence packet. See [multi-projection experiment](fir-multiple-projections.md). The full JVM domain is still open; this one-byte sample does not cover class files or variable-length instruction decode.
6. Once retrieval is stable, compare the same model with and without exact pattern/evidence packets. Measure decode, evidence citation, and abstention separately; do not infer an AI advantage from a hand-picked example.

## Relation to the main Fission project

The Notion migration plan treats FSL/FIR as unverified research and asks for evidence before main-project adoption. This repository follows the broader exploratory scope requested for the research project. A local prototype or successful decode slice is not a promotion gate; any future migration still needs main-project parity, semantic validation, quality measurements, and an explicit compatibility plan. See [Notion context](notion-fsl-fir-context.md).

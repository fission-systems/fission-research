# GPU FSL: references and compiler requirements

Date: 2026-10-01. Status: source inspection and design, not GPU execution support.

The first fixed-width frontend extension has since landed on the experimental
Fission branch at commit `5376310b2077807de713d908ea100411efd73ef9`:
8/32/64/128-bit mask/value plans, contiguous raw fields, GFX900 decode and
field-aware re-encoding, and explicit unsupported GPU semantic bodies.
See [research status](research-status.md) for the current evidence and remaining
boundaries. The requirements below still include future work, particularly
variable lengths, resolved operands and executable GPU state effects.

## Decision

Build the FSL architecture-description compiler first, extending the text DSL
in the experimental `fission-fsl` crate. GPU frontend rules lower to the same
canonical FIR used by the CPU/VM path. Multiple outputs consume that FIR; no
NIR/HIR split is introduced. Correct encoding and declared observable behavior
are the acceptance criteria. Source readability is a later output concern.

This research checkout already contains a four-instruction GFX900 probe and an
older TOML-based `.fsl` experiment. That syntax is a historical prototype, not
the Rust compiler's accepted text DSL. Likewise its JSON pattern packages are
old probe artifacts, not the chosen compiler/runtime package format. New work
will extend text `.fsl` → verified binary `.fslc`, and migrate accepted rules
explicitly rather than pretending both parsers accept the same language.

Upstream snapshots live in [`../Vendor/`](../Vendor/README.md). The reference
inventory is [`../Vendor/references.lock.toml`](../Vendor/references.lock.toml).
No reference tool was built, and no GPU kernel was executed in this step.

## Findings that change the design

### AMD: versioned encodings and implicit effects

AMD's `isa_spec_manager/include/amdisa/isa_decoder.h` provides encoding offsets,
widths, and operand direction. Its XML reader and decoder separate schema
reading from instruction matching. The downloaded RDNA3 document provides
encoding conditions, literal variants, and implicit operands.

In `amdgpu_isa_rdna3.xml`, `S_ADD_U32` has both a scalar destination and an
implicit SCC result. Encoding it as just wrapping add would discard an
architectural effect. The document also describes `S_ENDPGM` as SOPP opcode 48;
the existing GFX900 experiment uses SOPP opcode 1. Same mnemonic does not imply
the same generation's encoding. These observations are anchored to the XML
hashes in the lock file, not a cross-generation inference.

First AMD roles:

- Keep GFX900 as the existing narrow corpus and reference its Vega documentation.
- Add a distinct RDNA3 profile for a machine-readable import experiment.
- Read encoding/operand facts from XML. Human-readable descriptions require
  separately authored and reviewed executable semantics.
- Preserve SCC, EXEC, register classes, literal words, and address-space effects
  as explicit semantics where supported. No silent flattening into host scalars.

### NVIDIA: encoding and scheduling metadata are separate inputs

envytools' `envydis/dis-intern.h` describes nested mask/value tables and field
operations. Those tables are useful for constructing FSL decode decisions;
their order must not accidentally become an undocumented ambiguity policy.

CuAssembler's `CuSMVersion.py`, `CuControlCode.py`, and instruction repositories
separate architecture versions, instruction bits, reuse, and scheduling controls.
The checked-in repositories include `sm_60`, `sm_61`, `sm_70`, `sm_75`, `sm_80`,
and `sm_86`. Version names in the code alone do not prove complete ISA coverage.

Use `sm_80` as the first NVIDIA profile candidate. Preserve the complete encoded
instruction and control metadata. Predicate guards, inactive-lane behavior,
register state, and synchronization must be modeled before claiming executable
semantics. PTX and SASS remain different input profiles.

### Intel: instruction length depends on compaction

IGA's `Backend/GED/Decoder.cpp` selects instruction size from compaction control,
with 8-byte and 16-byte sizes declared in `Backend/BitProcessor.hpp`. Platform
models and GED tables describe the encoding independently of assembly printing.
Thus a fixed single-byte opcode matcher cannot describe this decoder.

Begin with one explicitly chosen Xe platform model and uncompressed instructions,
then add compaction using that platform's tables. Preserve execution size,
predicate and register regioning. Message/send descriptors must remain
unsupported for execution until address spaces, payloads, and effects have been
established; formatting them as ordinary memory operations would lose behavior.

## Required FSL compiler primitives

All items below are planned extensions; the current Rust compiler only accepts
its initial one-byte stack-instruction subset.

| Primitive | Requirement | Evidence motivating it |
|---|---|---|
| Architecture identity | Vendor, ISA family, exact generation, feature constraints; reject mismatched profiles | AMD opcode differences, Intel platform models, NVIDIA SM repositories |
| Encoding layouts | Endianness, variable instruction lengths, split bitfield slices, masks/values, checked concatenation | GPU word encodings, Intel compaction |
| Conditional extra words | Explicit length conditions and insufficient-input result; no guessed advancement | AMD literal encoding variants |
| Operand selectors | Register banks, inline constants, literal selectors, special registers, invalid selector ranges | AMD operand tables and existing GFX900 source-selector probe |
| Match validation | Detect overlaps and require explicit precedence or disjoint constraints; diagnose unreachable patterns | envytools nested decision tables |
| Ordered state effects | Register reads/writes, flags, lane masks, predication, memory spaces, wave termination | AMD implicit SCC; NVIDIA predicates; Intel execution controls |
| Evidence | Source revision/hash, path, architecture range, encoding and semantic validation tracked separately | All imported reference sources |
| Re-encoding | Retained raw fields plus validated field edits; preserve reserved/control bits with an explicit policy | Assembly references and accuracy/recompilation objective |

Bitfield/decode plans are compiler artifacts, not another semantic IR tier.
Executable lowering produces canonical FIR with explicit effects. GPU effects
that a C/Rust output cannot express must reject emission or call a declared
runtime with a documented contract. Arbitrary unknown effects must not become
no-ops.

## Implementation order

1. Extend the Rust FSL parser and typed encoding model for 32/64/128-bit layouts,
   extracted fields, constraints, architecture identity, and bounds-checked
   instruction lengths. Preserve current JVM `iadd` compilation.
2. Port the existing four GFX900 probe rules into the new text DSL. Match encoded
   bytes, operand fields, and consumed length against the recorded LLVM output.
   Their present effect summaries remain non-executable until reviewed.
3. Import a narrow RDNA3 encoding slice from the official XML into authored FSL,
   retaining source hashes and implicit operand metadata. Schema 1.2.0 (CDNA5)
   is a separate importer scope from schema 1.1.1; never assume interchangeability.
4. Add one sm_80 and one Xe instruction-family slice using the checked-in
   encoding references. Keep architecture-scoped support matrices.
5. Extend canonical FIR to architectural state and ordered GPU effects, starting
   with integer operations and predicate/mask-controlled register writes.
6. Add field-aware re-encoding and then behavioral recompilation. Container
   metadata, kernel ABI, memory and synchronization must be included before
   claiming whole-kernel equivalence.

## Future acceptance gates

These are proposed checks, not results from this source-inspection step:

- Decode: compare bytes, platform, length, mnemonic, operands, implicit operands,
  and unsupported statuses against a fixed reference corpus.
- Encode: reconstruct original encodings where preserved fields permit it, and
  separately check canonical encodings; byte identity is not semantic proof.
- Semantics: compare register/flag/mask/memory changes for supported instructions
  with independent models and, when available, hardware observations.
- Recompile: compare declared observable kernel behavior and failures with a
  retained ABI. Report synthetic, compiler-generated, and hardware evidence
  separately.

Driver/runtime sources become necessary for object loading, ABI, dispatch,
memory mappings, and synchronization questions. They are not the sole starting
point for recovering instruction encodings.

## Primary sources

- [AMD machine-readable ISA](https://gpuopen.com/machine-readable-isa/)
- [AMD ISA decoder sources](https://github.com/GPUOpen-Tools/isa_spec_manager)
- [AMD Radeon GPU Analyzer](https://github.com/GPUOpen-Tools/radeon_gpu_analyzer)
- [NVIDIA binary utilities documentation](https://docs.nvidia.com/cuda/cuda-binary-utilities/)
- [envytools](https://github.com/envytools/envytools)
- [CuAssembler](https://github.com/cloudcores/CuAssembler)
- [Intel Graphics Compiler / IGA](https://github.com/intel/intel-graphics-compiler)

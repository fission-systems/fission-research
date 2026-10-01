# GFX900 SOP2 register-only FSL extension

This is an authored **Rust text FSL** profile, separate from the older TOML
`gfx900-first.fsl`. It describes the contiguous SOP2 opcode family 0x00..0x1f
(32 instructions). The compiler remains owned by the Fission experimental branch.

## Admission scope

- Fixed 32-bit little-endian instructions, explicit profile `amdgcn.gfx900.sop2`.
- SGPR numbers 0..95 only; 64-bit operands use even aligned register pairs.
- 64-bit shifts have a scalar 32-bit source1.
- Special registers, inline constants, literals and extension words are excluded.
- Fields are raw register selectors. SCC, register effects and GPU execution are
  explicitly `unsupported`. Decode success cannot authorize execution or recompilation.

## Provenance and extension measurement

Field layout and opcode numbers were checked against LLVM's tagged
`llvmorg-22.1.0` `SOPInstructions.td` (`SOP2_Real32`, `SOP2_Real_vi`, GFX8/GFX9
section). [source.lock.toml](source.lock.toml) records the reference URL/hash,
compiler commit and reviewed package/corpus hashes. No upstream implementation
is embedded or used as a runtime dependency.

[additions.tsv](additions.tsv) classifies every opcode addition:

| Category | Count | Scope |
|---|---:|---|
| FSL specification only | 32 | Register-only encoding |
| New generic primitive | 0 | None required for this encoding family |
| Architecture-specific compiler escape | 0 | None required |

Compiler baseline `5376310b2077807de713d908ea100411efd73ef9` already provides the
needed masks, fields and exclusions. Validation commit
`bf49f27a9b8f0fdafedeba0c88a232522a39f267` adds tests only; the diff under
`crates/fission-fsl/src` is empty. The measurement applies to this family and
admission scope. It does not measure GPU semantic expressiveness, extended
operands, register-bank resolution or other instruction formats.

## Reproduce

Build `fslc` from the pinned Fission commit, then run from the research root:

```sh
python3 tools/gfx900_sop2_validate.py --fslc /absolute/path/to/target/debug/fslc
```

The runner uses LLVM assembly to obtain expected bytes, without reading opcode
constants from FSL. It also checks LLVM disassembly's mnemonic and operands.
Eight boundary/seeded operand combinations per instruction produce 256 inputs.
FSL decode fields, unchanged reencoding, and destination=92 edits are compared
with these independently executed oracle results. Unknown encodings, literal
selectors, out-of-scope destinations, truncation and foreign profiles must fail.

[validation-2026-10-01.json](validation-2026-10-01.json) records the local run:
256 decode comparisons, 256 unchanged round trips, 256 edited oracle comparisons,
99 rejected inputs; LLVM 22.1.8. CI uses LLVM 18 and requires the same reviewed
package/corpus hashes. A result file is evidence for its recorded run, not a
claim that subsequent CI runs passed.

**Oracle limitation:** LLVM is a separately executed assembler/disassembler,
but the FSL opcode reference shares its lineage. This catches transcription,
field extraction and reencoding errors; common upstream errors remain possible.
AMD specification review and a separate execution oracle are subsequent gates.

## Execution gate

The Fission crate now has five encoding regression tests, including rejection of
GPU `unsupported` semantics by the reference evaluator, C/Rust emitters, JIT and
AOT. Evaluator refusal must preserve its supplied state. All nine crate tests
passed locally, including the prior 1,920-input / 7,680-comparison integer-stack
C/Rust execution test. This is JVM-style bitvector/stack evidence, not GPU state
execution evidence.

Next execution slice: SGPR read/write and SCC as explicit ordered FIR effects;
start with `s_add_u32` and its result/carry state. Compare every state component
against an independent arithmetic oracle before emitting executable C/Rust.
Extend to carry-input arithmetic and logic only after this gate passes. GPU
hardware/emulator execution and full kernel equivalence remain later gates.

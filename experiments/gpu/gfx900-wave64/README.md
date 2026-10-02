# GFX900 wave64 masked vector-add slice

Date: 2026-10-02. Native implementation:
[`0bc0efbb1`](https://github.com/fission-systems/Fission/commit/0bc0efbb107e77c2baa84c942b567938da63d571),
on `codex/fsl-jvm-iadd-parity`, [PR #176](https://github.com/fission-systems/Fission/pull/176).
This remains an experimental crate, not a replacement of the product frontend.

The [FSL source](../../../specs/gpu/amdgcn/gfx900-vadd-u32-wave64.fsl) defines
two VOP2 e32 patterns: VGPR/VGPR and SGPR0..95 broadcast/VGPR. Both consume
the same FIR wrapping addition with explicit mask/read/write effects.
The implementation has no mnemonic or architecture dispatch in its evaluator.

## Single FIR effect model

- `lane.mask.read 64` snapshots EXEC with explicit extent.
- `lane.register.read field, bias, %mask` captures all lane slots; the
  source definition supplies selector bias (256 for SRC0 VGPR codes).
- `lane.register.write field, %value, %mask` updates exactly active lanes.
- `WaveContract` derives uniform/mask/lane domains from typed producers.
  Ordinary wrapping addition broadcasts uniform inputs. Masks cannot become
  arithmetic operands; lane values cannot enter uniform effects.
- Scalar effects execute once even when EXEC=0. Field/bank/flag/extent
  preconditions are checked before any architectural mutation.

The `WaveState` projection contains scalar registers, u1 flags, explicit lane
extent, EXEC and register-major lane slots. It adds no NIR/HIR layer. Package
v5 stores the three new generic effects; historical package versions and
SOP2 hashes remain unchanged. There are two encoding patterns, three common
primitives and zero architecture-specific escapes in this increment.

## Measured evidence

[Validation record](validation-2026-10-02.json):

- 1,984 valid states plus 19 invalid emitter rows, 8,012 C/Rust O0/O2 comparisons,
  zero mismatches against independent widened modulo sums/full-state expectations.
- Zero/full/alternating/sparse/highest-lane and seeded masks; source/destination
  aliasing; SGPR broadcast; inactive high bits and unrelated state preserved.
- A separate four-lane synthetic contract: four rows / 16 recompilation
  comparisons for mask bounds, scalar effects at EXEC=0, masked writes and
  prevalidation before a late invalid bank. This is not GPU wave32 evidence.
- Maximum VGPR255/SGPR95 boundaries are reference-only checks.
- 22 native crate tests passed, including earlier scalar, stack and migration
  regression gates. Formatting and Clippy with warnings denied passed.
- LLVM-generated 128 encodings: 128 field checks, 128 unchanged byte roundtrips,
  128 edited reassembly comparisons and nine explicit refusals.

The ISA source is [AMD Vega ISA](https://docs.amd.com/v/u/en-US/vega-shader-instruction-set-architecture)
§3.3 (EXEC), §12.7 (VOP2), with source attribution retained in FSL. LLVM is a
separate encoding implementation; it supplies no execution oracle here.

## Reproduction

```sh
python3 tools/gfx900_wave_validate.py --fslc <Fission-worktree>/target/debug/fslc
```

The [lock](source.lock.toml) pins source, portable package and LLVM corpus
hashes. The tool rejects drift, generates the package twice, checks both
operand classes and validates unedited/edited bytes. CI pins the native
compiler commit, compares the source copy and runs the same validation with
LLVM 18 plus native state/recompilation tests.

## Limits and next work

No GPU hardware or emulator execution, kernel equivalence, performance or
decompilation-quality claim follows from these synthetic states. EXEC writes,
VCC operations, divergence, synchronization, memory, traps, inline/special/
literal sources, SDWA/DPP and Cranelift wave JIT/AOT remain unsupported.
The wave executor rejects carry/stack operations in mixed bodies. No wave32
architectural profile is claimed.

Next: FSL register layouts and ABI linking, preserving shared/overlapping
storage before importing additional cspec allocation rules. Direct SLA
decision/context/ConstructTpl lowering remains a separate gate. Further GPU
effects need independent semantics evidence and full-state comparisons.

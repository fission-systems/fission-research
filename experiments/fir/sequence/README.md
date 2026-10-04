# Sequential instruction state and origin

Date: 2026-10-04. Native owner is `fission-fsl` in Fission's experimental
`codex/fsl-jvm-iadd-parity` branch, compiler [`16f84f47e`](https://github.com/fission-systems/Fission/commit/16f84f47e0cb53278fddde2522dfbe581fce5ddf) / [PR #176](https://github.com/fission-systems/Fission/pull/176).
This repository holds authored windows, source definitions, output artifacts
and a hash lock. These are explicit sequential windows, not binary functions.

`FirSequence` owns one immutable compiled FIR body pool. Each instance references
its instruction index and records an address, input offset, length and exact
raw bytes/fields. The sequence binds the input window and compiled package with
SHA-256; the body retains specification evidence. Local value IDs are scoped to
each invocation. One ordered register/flag runtime context carries state to the
next instance. `.fslseq` embeds the unchanged `.fslc` and exact input bytes; it
introduces no additional semantic IR or P-code lowering.

The exact register/flag bank sizes are part of the execution ABI. The wrapper
runs on copied state and commits only after all instances succeed. Selector and
semantic admission checks cover the entire window before execution. Invalid
bank sizes/flags preserve original storage. This transaction is not guest fault
ordering or concurrent CPU atomicity; dynamic guest faults remain unsupported.
C source callers supply disjoint valid arrays and nonnull dummy storage for an
empty bank. Both banks are bounded to 4,096 logical slots.

| Fixture | Window / bodies | Locked container |
|---|---|---:|
| `scalar-chain` | `s_add_u32 → s_addc_u32`, carry handed off through SCC; self-authored GFX900 bytes | 7,687 bytes |
| `register-chain` | Three invocations of the existing conversion/register CFG body, reading earlier writes | 911 bytes |

Origin base `0x1000` is caller supplied. The scalar bytes are
`0002048001030582`; the register bytes are `10a2000021a0000002a10000`.
The lock records source/package/container hashes and all six output hashes.
Original `.fslc` layouts and old artifacts stay unchanged.

## Observed validation

- Native reference/u128 oracle: 1,060 two-instruction arithmetic states.
- Scalar sequence recompilation: five widths × two alias placements × 132
  success/failure rows = 1,320 rows / 5,280 C/Rust O0/O2 comparisons. Widths
  other than 32 are synthetic primitive checks, not GPU ISA support.
- Three structured bodies: 256 successful inputs + three failed ABIs = 259
  rows / 1,036 comparisons, including full backing storage on failure.
- Explicit zero-register and zero-flag banks: two rows / eight comparisons.
- New source comparison total: **6,324**, with warnings denied in C and Rust.
- Entire native crate: 53 tests passed serially, zero skipped/leaky; Python 27
  tests passed. Formatting and warning-denied Clippy passed.
- Python reproduction independently verifies two envelope byte/length/hash
  contracts and six exact outputs, 112 native CLI oracle states and four failures.
- Previous structured/conversion package/output hashes and historical, SLA,
  layout, ABI, library artifacts reproduced unchanged.

```sh
python3 tools/sequence_fir_reproduce.py --fslc /absolute/path/to/fslc
# Native worktree:
cargo nextest run --locked -p fission-fsl -j 1
```

The CI compiler revision is pinned in `.github/workflows/reproduce.yml`.
`validation-2026-10-04.json` records the local evidence separately from remote CI.

## Limits and next boundary

Validation uses authored specifications and windows, not a GPU execution oracle.
Only explicitly bounded sequential flow is supported. Body branch/return applies
inside that instruction, then the next supplied word runs; no guest PC write,
branch target recovery or function entry/return is inferred. Loop execution,
GPU CFG/divergence, memory/calls/exceptions, actual binary function lifting,
variable-width/mixed profiles, and sequence native Cranelift JIT/AOT remain
unsupported. CUDA/PTX sequence output refuses.

Window SHA is not whole-file SHA, and compiled-package SHA is not `.fsl` source
SHA. Base address and bank ABI are caller supplied; hashes are not authenticity
evidence. Changing those to another valid contract yields a different plan.
No file-offset/virtual-address map, symbol, ABI allocator or register-layout
binding is claimed. The research lock also hashes the entire envelope.

The next implementation should define inter-instruction branch/PC contracts and
connect explicitly selected binary spans to loader-backed origins before making
binary function lifting claims. Existing in-body CFG support remains distinct.

# Automated reproduction

`make reproduce` regenerates nine historical artifacts in a temporary directory,
then requires exact SHA-256 matches against `experiments/reproduction.lock.toml`.
Tracked golden files are never overwritten. Locked inputs include the probes,
fixture bytes, old TOML FSL sources and all 133 SLA files. Missing prerequisites,
probe errors, changed inputs and changed outputs fail the command. The report is
written to `artifacts/reproduction.json`; a failed run replaces any previous success report.

Requirements: Python 3.11+ (CI uses 3.12), Git, and the pinned Fission comparison
checkout. For a fresh checkout without a `Fission/` directory:

```sh
git init Fission
git -C Fission remote add origin https://github.com/fission-systems/Fission.git
git -C Fission sparse-checkout init --cone
git -C Fission sparse-checkout set utils/sleigh-specs/compiled
git -C Fission fetch --depth=1 --filter=blob:none origin 96fc71f75cecdee305faf9497561c577a8955468
git -C Fission checkout --detach FETCH_HEAD
make test reproduce
```

An existing comparison checkout must already have that commit. Reproduction
performs no fetch or checkout automatically. No Vendor clones are required.

The historical gate covers old JSON pattern packages, GPU/JVM decode, JVM
projections, two AMDGPU ELF inventories, an AQL packet inventory and the complete
SLA structural inventory. It checks regeneration, not instruction semantics or
SLEIGH replacement. The old TOML format and JSON artifacts are retained as
historical probes; the Rust text FSL and binary `.fslc` compiler are separate.

## Encoding and execution gates

The second CI job fetches Fission compiler commit
`217d7eafd90b396edc46f0c24fdb6372caf60354` separately into `.compiler/`. It builds
`fslc` with pinned Rust 1.98.1, runs its existing FIR execution/recompilation tests, then validates the
research SOP2 profile against LLVM 18. Local validation also records the oracle
version; the first local run used LLVM 22.1.8.

```sh
cargo test -p fission-fsl --test recompilation -- --nocapture
# Run above in the Fission experimental worktree, then from this repository:
python3 tools/gfx900_sop2_validate.py --fslc /absolute/path/to/fslc
```

GPU encode/decode and JVM execution are distinct evidence scopes. CI passing
both does not establish GPU execution correctness. A subsequent GPU execution
gate must model SGPRs, SCC and instruction-specific effects in canonical FIR,
then compare full before/after state with a separate oracle. Byte round trips
alone cannot pass that gate.

When probes or scope intentionally change, review newly generated artifacts and
input/output hashes together before updating the lock. Never refresh hashes
merely to silence a failed CI run.

## Observed remote reproduction

[Run 36801812921](https://github.com/fission-systems/fission-research/actions/runs/36801812921)
passed both jobs at research commit `ccfcbab82a02c50ebd41b806f14f220b66f14ada`.
The Ubuntu oracle was LLVM 18.1.3 and the Rust compiler was 1.98.1. Its package
and corpus hashes matched the macOS LLVM 22.1.8 observations. Subsequent runs
preserve reports as GitHub Actions artifacts; runtime/tool versions remain part
of each report or job log.

## Register layout gate

`make layout-reproduce` regenerates three `.fslregs` files and one provenance
report from the same pinned input snapshot. All four files must match the
captured artifacts byte for byte. Existing first-slice migration files are
unchanged. The declaration-prefix importer admits BPF LE and eBPF LE/BE;
non-byte spaces, unknown declarations and changed entry preprocessing refuse.

```sh
make test reproduce migration-reproduce layout-reproduce
python3 tools/register_layout_reproduce.py --fslc /absolute/path/to/fslc
```

With a native compiler, the gate parses all three layouts, links both eBPF
byte-order layouts, checks the expected BPF stack-width refusal, and executes
two linked leaf cases. The report at `artifacts/register-layout.json` is replaced
on failure as well as success. CI regenerates sources in the historical job,
then compares compiler copies and runs native gates in the compiler job; source
snapshot and compiler commits are fetched separately. The native crate tests
also compare 968 synthetic byte-storage states. These are metadata/reference
gates, not ABI allocation, GPU kernel behavior or direct SLA semantic migration.

## Direct SLA gate

`make sla-migration-reproduce` rebuilds three new golden files from the binary
eBPF SLA, then checks eight semantic/selector/decision-priority mutations refuse.
With `--fslc`, it additionally parses instruction/layout source, links the ABI,
checks a locked portable package hash and executes one linked CLI state.
The compiler's native tests compare 65,536 source/SLA prefixes and separately
recompile the SLA-derived FIR in C/Rust. CI gives this gate a compiled-only input
checkout and asserts no language-source directory exists. There is no Vendor
runtime dependency. JSON remains the reproduction/evidence report; instruction
and register source are owned FSL text.

```sh
make test reproduce migration-reproduce layout-reproduce sla-migration-reproduce
python3 tools/sla_migration_reproduce.py --fslc /absolute/path/to/fslc
```

The admitted conversion is one bound register ADD64 branch. Other constructor
effects, context, memory, dynamic handles and general decisions are subsequent
registry extensions. Historical artifact/migration locks remain unchanged.

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

The historical job also fetches pinned `utils/signatures` for the 988-file
asset inventory and one FPK prototype-candidate migration. Run
`make library-migration-reproduce` after restoring that directory. The native
job separately fetches the generic signature input into `.library-input/`,
regenerates `.fslib`/`.fsldb`, checks native parsing and three exact queries,
and compiles the self-authored `.fslib` fixture without a legacy input.
Reports preserve unresolved types and unknown variadic evidence. These gates
do not replace the product signature loader or establish callable ABI semantics.

The second CI job fetches Fission compiler commit
`8211a05610204670a4f5542298d8a4e0d9fe5983` separately into `.compiler/`. It builds
`fslc` with pinned Rust 1.98.1, runs its existing FIR execution/recompilation tests, then validates the
research SOP2 profile against LLVM 18. Local validation also records the oracle
version; the first local run used LLVM 22.1.8.

The native gate now includes structured semantic-body FIR: typed constants,
three comparisons, block arguments, branches and joins. The compiler's control
test compares 2,048 reference/oracle states and 8,192 C/Rust O0/O2 outputs; a
separate test covers 65,536 bounded inputs. `tools/structured_fir_reproduce.py`
regenerates a locked v6 package and FIR/C/Rust outputs, then verifies 12 native
CLI oracle cases and two failure cases. These are self-authored CFG fixtures,
not real binary function decompilation or whole-function equivalence evidence.

The v7 conversion/register CFG gate adds 24 conversion profiles and an
exhaustive scalar register/flag diamond. Its C/Rust O0/O2 comparisons total
48,208: conversions 12,288; register CFG 27,680; two constructed carry CFGs
8,240 (including source ABI refusals). `tools/register_fir_reproduce.py`
regenerates the locked 803-byte package and three outputs, then checks 44
native CLI oracle states and three failures. These register-CFG fixtures do not
validate loops, memory, GPU CFG or real binary function lifting.

```sh
python3 tools/structured_fir_reproduce.py --fslc /absolute/path/to/fslc
python3 tools/register_fir_reproduce.py --fslc /absolute/path/to/fslc
python3 tools/sequence_fir_reproduce.py --fslc /absolute/path/to/fslc
```

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
# CUDA C++ / PTX projection

동일 FIR의 GPU reference 출력은 `python3 tools/gpu_projection_validate.py --fslc /path/to/fslc --clang clang-18`로 재현한다. 3개 projection artifact와 package lock, 41 profiles의 scalar reference/Clang device compilation, 8개 refusal을 검사한다. Linux에서는 `python3 tools/gpu_projection_toolchain.py`로 hash-locked ptxas와 license를 복원한 후 `--ptxas .cuda-toolchain/ptxas`를 추가한다. [실험 범위](../experiments/gpu/fir-projections/README.md)에 ABI·주소 전제와 hardware 실행 미검증을 기록한다.

## Explicit instruction sequence reproduction

`sequence_fir_reproduce.py` regenerates two `.fslseq` envelopes and six FIR/C/Rust
outputs. It independently verifies their embedded package/window bytes, hashes,
lengths, base and bank contract, then compares 112 native CLI oracle states and
four failures. Native sequence tests add 6,324 C/Rust O0/O2 comparisons and a
separate 1,060-state u128 arithmetic oracle. The ABI is exact logical bank sizes;
invalid input preserves state. These are authored sequential instruction windows
and do not establish real binary function lifting, loops, GPU CFG or memory
semantics. See [scope/lock](../experiments/fir/sequence/README.md).

## Owned x86 memory and stack gate

The original x86 windows, readonly memory pool and stateful pool are retained
separately. The historical job regenerates each pool and compares all five
source/inventory artifacts. The compiler job reproduces the original projections,
then executes the readonly and stateful ELF windows with C/Rust O0/O2 and original
Linux x86 bytes. The i386 oracle is a static libc-free adapter; the 64-bit adapter
checks two-word external memory in addition to result, flags and frame balance.

```sh
python3 tools/x86_stateful_validate.py \
  --fsl-x86 /absolute/path/to/fsl-x86 \
  --pcode-baseline /absolute/path/to/x86_fir_baseline \
  --baseline-root /absolute/path/to/Fission \
  --cc clang-18 --rustc 'rustup run 1.98.1 rustc' --machine-host native-x86
```

The stateful gate checks 768 modeled FIR states and 6,144 compiled success/rollback
rows. Budget failures follow actual PUSH/MOV stores. Reports preserve host/tool,
source/executable hashes, checkout provenance and measured SLA baseline differences.
Local ARM64 macOS observes only 512 original-byte cases through Rosetta; Linux CI
requires all three adapters (768 cases). The baseline is an implementation
comparison, not an expected mismatch count or proof of an IR expressive limit.
See [stateful contracts and scope](../experiments/x86/stateful/README.md): bounded
flat memory, modern IA-32 stack ordering, no complete ABI or full x86 migration.

## Split x86 operand reproduction

The optional fourth x86 pool is generated with `--memory-immediates`. CI compares
its five source/inventory files and executes three compiled AMD64 C7-store
spans using the same independent stateful validator:

```sh
python3 tools/x86_stateful_validate.py --fixture-root experiments/x86/immediate \
  --fsl-x86 /absolute/path/to/fsl-x86 --cc clang-18 \
  --rustc 'rustup run 1.98.1 rustc' --machine-host native-x86 \
  --report artifacts/x86-immediate.json
```

This gate checks 768 modeled states, 6,144 compiled success/rollback rows and
768 original-byte cases. Partial stores preserve neighboring bytes; imm32 is
sign extended for 64-bit writes. Existing v1 hashes remain unchanged. See
[format, accounting and limits](../experiments/x86/immediate/README.md).

## Source backend plans and bundles

```sh
python3 tools/output_backend_reproduce.py --fsl-x86 /absolute/path/to/fsl-x86 \
  --cc clang-18 --rustc 'rustup run 1.98.1 rustc'
```

This compares 18 locked metadata artifacts and six unchanged source files,
compiles six bundles and checks seven refusals. It does not measure execution
equivalence. The existing x86 immediate validator remains a separate regression
gate. See [the contract and limits](../experiments/output/backend-contract/README.md).

## Go execution projection

```sh
python3 tools/go_backend_validate.py --fsl-x86 /absolute/path/to/fsl-x86 \
  --fslc /absolute/path/to/fslc --go go --cc clang-18 \
  --rustc 'rustup run 1.98.1 rustc'
```

This reuses six locked ELF fixtures and independent state/byte expectations.
16 Go source files reproduce; Go runs at default and disabled optimizations,
C/Rust O0/O2 run the same window cases. Synthetic domains are separate evidence.
Linux host amd64/386 archive builds are not execution on those hosts.
[Inputs, counts and limitations](../experiments/output/go-backend/README.md).

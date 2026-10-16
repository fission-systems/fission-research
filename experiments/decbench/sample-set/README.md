# Owned FSL/FIR — DecBench sample-set baseline (2026-10-16)

This is **static coverage measurement**, not a scored or submission-ready
DecBench decompilation. The engine is `fission-fsl`, separate from product Fission.
Native compiler pin: `0fc6f6f98115cddb88077a71353a0462d28b1a0b` on
`codex/fsl-jvm-iadd-parity` ([PR #176](https://github.com/fission-systems/Fission/pull/176)).

## Contract

The external sample-set kit provides 250 entry addresses across 224 stripped
binaries. Only `functions.json.public` selects targets. Addresses use the linked
ELF VA / PE image base + RVA convention. No function sizes, private mappings,
original source, DWARF answer keys or reference decompiler outputs are consulted.
The kit contains malware: the adapter only launches the trusted native FSL tool,
with target files passed as static inputs. It never executes/emulates targets,
changes their permissions, compiles their output or calls the kit's packager.

The owned ELF mapper validates machine/class/endian directly, without Ghidra
opinion/ldefs. The embedded FSL profile owns decoding and canonical FIR semantics;
no external instruction decoder or SLEIGH/P-code fallback is used. Address-only
selection scans a file-backed executable straight-line prefix to the first near
RET within 65,536 bytes / 4,096 instructions. A branch or unknown instruction
refuses. This conservative window is not a proven source-function boundary.

Every attempt records its address, input hash, raw diagnostic, category and
elapsed time. Checkpoints replace `report.json` after each function. A run must
use a new output directory outside the kit; it never overwrites previous results.
There is no resume mode. Tool/manifest/binary integrity is checked at completion;
rebuilds of the tool during a run invalidate completion. Refusal categories are
text-based diagnostic groupings; raw messages remain the primary evidence.

The current C output accepts explicit registers/flags/memory/budget/exit state
and returns an execution status. It does **not** implement the original source
function's calling convention or return value. Therefore successful bundles are
`state_projection_only`, with `metric_eligible=false`. No `results/results.json`
or submission archive is generated. DecBench's packager rejects an empty
submission; this gate does not fabricate one or report a score from state code.

## Measured baseline

| Stage stopping the selected function | Count |
| --- | ---: |
| Unsupported loader/architecture | 92 |
| Owned instruction decoding unsupported | 148 |
| Branch outside straight-line entry-selection contract | 10 |
| Complete entry-state projections | 0 |
| Ordinary source-function C outputs eligible for scoring | **0 / 250** |

Of the 92 loader refusals, 84 report a mismatch with the admitted little-endian
ELF i386/x86-64 contract and eight are non-ELF. The other 158 attempts reach the
owned x86 entry path. The table is a first-failure distribution, not counts of
all missing instructions or an exhaustive architecture inventory. No GED/type/
byte-match or execution-equivalence metric has been run; absence of a score
must not be reported as a measured zero score.

The archived [coverage-v2.json](coverage-v2.json) retains all 250 observations, tool/adapter/input
hashes and integrity checks. It excludes target binaries, private metadata,
answer keys and source. SHA-256:
`9f54b8db104c0ada314d93735906edb6bce1ebb8897b6e06b49a5300f5aab695`.
[The first baseline](coverage.json) remains unchanged at its original hash
`a06eca9c73f5ed7c1d36de20a1c7beead7617b7954340351558ed159642f4841`.
V2 explicitly treats Rust panic/signal/unexpected exit codes as tool errors,
with only the CLI's normal exit code 1 admitted as a refusal; no such errors
occurred in either corpus run, and all category counts are identical.
[source.lock.json](source.lock.json) locks reports/tools and the compiler pin;
[local pipeline gate](owned-pipeline-local.json) records clean compiler provenance,
nine compilations, three entry-only output comparisons and 11 refusals. This
local run is not filesystem isolation evidence. The fixture integration gate separately admits three
self-authored locked immediate-store ELFs as diagnostic bundles and checks that
their profile hash matches the existing owned package. The isolation gate also
compares their entry-only C/FIR output to locked span outputs under Linux chroot
and file tracing. Fixture admission does not establish DecBench corpus support.

## Reproduce

```sh
# Build the pinned experimental compiler (no legacy assets required).
cargo build --locked -p fission-fsl --features x86 --bin fsl-x86
# From this research repository; binaries are only read for static analysis:
python3 tools/decbench_fsl_evalkit.py \
  --kit-root /absolute/decbench-evalkit-sample-set \
  --fsl-x86 /absolute/compiler/target/debug/fsl-x86 \
  --output /absolute/new-coverage-directory --timeout 10
# Fixture integration, without any DecBench target dependency:
FSL_X86=/absolute/compiler/target/debug/fsl-x86 \
  python3 -m unittest discover -s tests -p test_decbench_fsl_evalkit.py -v
```

A completed coverage run may exit zero with all functions refused. Read
`complete`, `summary.submission_ready` and the status/category distributions.
Tool errors or changed inputs/tool cause nonzero exit. Timeouts are recorded
per function. Generated diagnostics are not guaranteed to compile, because this
adapter does not run compilation or semantic evaluation.

## Remaining work

1. Extend FSL instruction/effect coverage from measured generic missing forms;
   do not erase prefix/control effects to accept a benchmark row.
2. Recover reachable function CFG, calls and returns with explicit uncertainty.
3. Model profile/ABI, live inputs, memory and source return contracts in the same
   FIR before admitting an ordinary C projection to the kit's submission format.
4. Validate source compilation and separate execution-equivalence evidence on
   safe owned fixtures; retain unsupported corpus entries as misses.
5. Human review precedes any upstream DecBench contribution/submission, as
   required by DecBench's AGENTS.md. This research adapter is out of tree and
   has not been submitted upstream.

Alive2 is deferred. It verifies LLVM-IR refinement, not raw binary versus C by
itself. Future use needs a trusted lifting boundary and matching ABI/memory/UB
contracts; it does not independently prove the original-byte lifting correct.
See [Alive2's own scope](https://github.com/AliveToolkit/alive2).

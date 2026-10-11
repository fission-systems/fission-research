# Source backend contract — first slice

The native experimental branch now provides `OutputBackend` descriptor/plan/emit
and an in-process registry. C11 and Rust 2021 use borrowed canonical FIR through
this interface; the existing rendering implementations and source bytes remain
unchanged. No external decoder dependency or second semantic IR was added.

## Implemented

- Shared admission of explicit stack/register/wave/x86-window contracts, with
  dialect/runtime/memory/context and canonical validity checks.
- Requirements for control, bitvectors, registers/flags, masked lanes, guest PC
  and bounded transactional memory. Structured rejection when unsupported.
- Bundles with source, build recipe and symbol-level origins. x86 origins include
  address/raw bytes/input offset/length. Statement source maps are unavailable.
- `plan-binary` and `bundle-binary` CLI; existing output directories refuse.
- Reports explicitly mark compilation and equivalence as unperformed. Separate
  reproduction compiles the generated sources and records observed results.

The registry is an extension point, not proof that any registered provider is
correct. Existing CUDA/PTX projections are outside this registry. Go, Python,
Java, JVM/CPython/WASM method frontends, general ABI recovery, guest memory faults
and concurrent memory semantics are not implemented here.

## Locked experiment

The three original inputs and six source files are the immutable
[x86 immediate-store experiment](../../x86/immediate/README.md). This folder only
adds 18 plan/projection/build metadata goldens and their hashes. These metadata
are implementation-derived goldens, not an independent semantic oracle.

```sh
python3 tools/output_backend_reproduce.py \
  --fsl-x86 /absolute/path/to/fsl-x86 --cc clang-18 \
  --rustc 'rustup run 1.98.1 rustc'
```

Expected: six bundles, 18 metadata artifacts, six standalone C/Rust compilations,
six existing-directory refusals and one unregistered Go refusal. Locked parent
inputs/package/source bytes must match even in `--record` mode. Recording only
updates the new metadata; it cannot regenerate parent source goldens.

[Source lock](source.lock.json) pins the parent lock and native compiler commit.
The local report records compiler executable and source hashes, checkout state
and tool versions; it is not reproducible-build attestation. CI fetches the pin.
Filesystem write failures may leave a partial new bundle directory.

Execution regression uses the independent existing immediate-store validator:
768 FIR inputs, 6,144 compiled success/rollback rows and 768 Rosetta original-byte
cases. These are bounded observables, not whole-function equivalence or evidence
that FIR is more accurate than P-code. [Local bundle report](local-validation-2026-10-11.json) and
[execution regression](local-execution-regression-2026-10-11.json) archive clean
native `cc02f3be7` snapshots. The regression retains the original parent fixture
compiler pin as `expected_native_compiler_commit`; the actual current checkout
and executable are recorded separately. CI reports are uploaded separately.

Next: Go over the same canonical contracts, followed by frontend-specific
semantic domain expansion with explicit exception/object/runtime effects.
See [maturity comparison](../../../docs/fsl-fir-maturity-comparison.md).

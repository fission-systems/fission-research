# Go backend execution slice — 2026-10-11

Native `97366a84157afe163236a99e309fcd4fbfb8e2ae` adds a registered `go` provider (`go1.25`) using the same canonical
FIR and checked contracts as C/Rust. There is no second IR, package change,
decoder dependency or external generated Go package. The generated `package fsl`
functions use uint64 bitvector slots and explicit masks rather than host-sized
integers for guest values. Go integer behavior is grounded in the
[language specification](https://go.dev/ref/spec#Integer_overflow).

## Supported contract

Instruction projection admits existing integer/stack, acyclic scalar CFG and
masked wave effects. x86 projection consumes an already bound, caller-selected
window from the owned decoder. The Go renderer handles operation semantics;
the window wrapper handles dispatch, budget and success-only commit. Origins
retain body/symbol/address/raw bytes/offset/length. Output metadata distinguishes
admission, compilation and observed execution; source generation makes no
validation claim.

Go snapshots state and mutable memory internally. Output bank overlap and x86
exit-pointer overlap refuse without unsafe code. Guest concurrency/faults,
source prototype/ABI recovery, host heap exhaustion, full ISA coverage,
FirSequence Go emission, complete JVM/CPython/WASM methods and GPU hardware
execution remain unsupported/outside this contract. Go functions are currently
package-local execution helpers, not recovered exported source APIs.

## Measured evidence

| Gate | Local result |
|---|---|
| Actual x86 ELF spans | Six existing frame/store/immediate fixtures, including cdecl32 and AMD64 |
| Go default / optimizations disabled | 6,144 full modeled state/memory/return-PC and rollback comparisons |
| C/Rust O0/O2 on identical inputs | 12,288 comparisons; original locked source bytes unchanged |
| Synthetic domains | 18,426 Go comparisons: 1/8/16/32/64 carry, input/destination alias, stack, signed conversion/branch, wave64 VGPR and SGPR broadcast |
| Go host target builds | 12 Linux amd64/386 archive compilations; no execution on those host targets locally |
| Native tests | 80 passed / 0 skipped; strict Clippy with/without x86 and fmt passed |
| Python tests | 35 passed |

The existing independent Python widened arithmetic and byte/state models are
reused; the new Go implementation does not compute expected results. Six actual
ELF fixtures are authored controlled samples. Their source and binary provenance
remain in the parent experiments. This gate does not execute original machine
bytes; CI retains the existing separate original-byte/SLA/FIR gates. Historical
counts are not summed into a new whole-function equivalence claim.

Ten domain projections and six window outputs are locked as 16 source artifacts.
These source goldens detect drift; they are implementation-derived and are not
the independent execution oracle. Input and parent-lock preflight remains active
in record mode. [Source lock](source.lock.json) pins the new native compiler;
[local report](local-validation-2026-10-11.json) records executable/source hashes,
clean checkout, shared model hashes and tools. It is not a build attestation.

## Reproduce

```sh
python3 tools/go_backend_validate.py \
  --fsl-x86 /absolute/path/to/fsl-x86 --fslc /absolute/path/to/fslc \
  --go go --cc clang-18 --rustc 'rustup run 1.98.1 rustc'
```

CI fetches the native pin, installs Go 1.25.5 through a commit-pinned setup action,
compares source goldens, runs both Go optimization settings and C/Rust O0/O2,
and uploads an execution report. Current CI completion is checked separately.

```sh
fslc emit-backend PACKAGE INSTRUCTION go output.go
fsl-x86 bundle-binary PACKAGE BINARY ADDRESS SIZE go NEW_DIRECTORY
go build -o output.a output.go
```

Next: frontend-specific domain contracts before whole JVM/Python/WASM method
support. General x86 CALL/ABI/CFG recovery remains a separate outstanding gap.

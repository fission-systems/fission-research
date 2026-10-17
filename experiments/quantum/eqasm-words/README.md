# Reference-assembled eQASM words — 2026-10-17

This adds **binary layout decoding**, not QPU execution or physical gate lifting.
Own FSL data admits canonical QWAIT/QWAITR words and opaque quantum bundles for
QE-Lab/eQASM_Assembler `9b024494558287a937cdd5a8ccd63fcaa784b1c4`. All three FIR
bodies are explicitly unsupported. The profile is configuration-specific and
little-endian, matching the pinned assembler running on our little-endian hosts;
it is not a universal CC-Light/device encoding assumption.

## What was measured

- Built the pinned assembler and generated **200 actual output words** from
  `corpus.qisa`: 128 QWAIT immediates, 32 QWAITR registers, 32 paired bundles and
  eight QNOP separator variants.
- Compared every word with a separate bit-field calculation, upstream disassembly
  words, owned FSL field decode, and owned byte re-encoding: 200/200 each passed.
- Six short/unknown/noncanonical format inputs refused. Unknown bundle operations
  remain opaque fields; successful format decoding does not admit their semantics.
- FSL additions: three data rules, zero decoder/compiler primitives and zero
  architecture-specific runtime code. This counts encoding expressiveness only.

The corpus bytes were independently calculated, then checked byte-for-byte against
the actual assembler output. They are reference-generated fixtures, not a binary
capture from a QPU. Fission native pin, binary/source hashes and compiler identities
are in `source.lock.json` / `validation-local.json`.

## Oracle build qualifications

`tools/eqasm_binary_probe.py` verifies a clean pinned upstream checkout, uses its
opcode generator and C++14 sources, Bison 3.8.2 and Flex, then compiles a separate
reference executable. A small equality adapter is inserted into **generated**
`location.hh` for source-position compatibility with modern Bison. No upstream
encoding or gate code is modified. The clone remains clean. No SWIG/Python binding
or library installation is used. Fission never links or invokes this executable.

The upstream assembler returns success but emits:

```text
Error: the quantum layout information is not read into assembler
```

The probe requires and records that exact known diagnostic. Its CLI leaves the
layout loader disabled. Therefore target masks/topology, pulse mapping and device
execution are **unverified**. We do not use target-dependent mask instructions as
semantic oracles. Physical gate identities are not inferred from CW_01/CW_02.
Other unexpected diagnostics fail the probe.

The writer emits host-order uint32_t words. The probe checks little-endian bytes
explicitly. Reserved bits for the timing rules must match zero-filled canonical
assembler output; other hardware-valid encodings are not claimed.

## Reproduce

```sh
git clone --depth 1 --branch develop https://github.com/QE-Lab/eQASM_Assembler.git Vendor/eqasm-assembler
git -C Vendor/eqasm-assembler fetch --depth 1 origin 9b024494558287a937cdd5a8ccd63fcaa784b1c4
git -C Vendor/eqasm-assembler checkout --detach FETCH_HEAD
python3 tools/eqasm_binary_probe.py --bison /path/to/bison-3.8.2 --fslc "$FISSION_ROOT/target/debug/fslc" --compiler-root "$FISSION_ROOT"
```

The reference source/license provenance remains in `Vendor/references.lock.toml`.
Timing queues, feedback, gate definitions, pulse calibration, containers, real
device binaries and whole-program lifting remain unsupported. See the
[input contract](../../../docs/qpu-binary-boundary.md).

## Portable reference build qualification

Initial Linux attempts 39021222095 and 39021455363 exposed a missing standard
`<limits>` include in upstream code. The separate build recipe now explicitly
includes that header (`-include limits`) and exposes compiler diagnostics on
failure. No upstream instruction logic or tracked source is changed. The original
local report and its validator hash/revision are preserved;
`validation-local-portable-build.json` records the adjusted recipe and again
passes 200 words / six refusals at the same clean native pin.

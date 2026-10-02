# First source/ABI migration slice

Date: 2026-10-01. Input snapshot: Fission
`96fc71f75cecdee305faf9497561c577a8955468`, including Ghidra language data.
Native consumer: Fission
[`cfcb0e0f3`](https://github.com/fission-systems/Fission/commit/cfcb0e0f3635849e5bcfd23d4f94def0ccd2094d).

`tools/fsl_migrate.py` emits FSL text. JSON is only the evidence report:

- [ebpf-add64-register.fsl](ebpf-add64-register.fsl): one executable
  little-endian ADD64 register leaf, including SRC8 register binding.
- [bpf.fslabi](bpf.fslabi), [ebpf.fslabi](ebpf.fslabi): compiler metadata in
  an FSL-owned ABI text grammar, read by `abi::compile_abi_source` and
  `fslc check-abi` in the native compiler.
- [migration.json](migration.json): input/output hashes, source/license
  attribution, per-cspec refusals and SLA structural inventory.
- [validation-2026-10-01.json](validation-2026-10-01.json): measured native
  execution, reference oracle and reproduction results.

## Measured evidence

484 migrated eBPF register states and 1,936 C/Rust O0/O2 comparisons passed
with zero mismatches. An independent u128 modulo sum produces expected states.
Unused instruction off/imm bits survive decode/reencode; malformed selectors
and immediate-source encodings are refused by the narrow profile.

The existing Fission SLA runtime decoded 121 register combinations and
checked bytes/length, R0..R10 bindings and the single 64-bit IntAdd template.
This shares source lineage with the migrated leaf. The profile follows the
source R10 binding without establishing verifier legality of writing R10.

The recursive inventory found 110 cspecs (including three under old/ paths),
146 slaspecs, 204 sincs and 133 SLAs. Two cspecs were fully admitted by the
strict metadata subset; 108 have recorded refusals. BPF/eBPF preserve the
admitted metadata from 33/47 XML elements: byte sizes/alignments, global spaces,
stack pointer, ordered register entries, cleanup and preserved/output effects.
Rules, groups, join addresses, injections, unknown nodes and extra attributes
cannot silently disappear. Explicit unknown cleanup remains `unknown`.

Symbolic ABI register names remain unlinked; parameter allocation, call
execution and binary ABI packaging are unsupported. Metadata conversion is
not a claim that a calling convention can already execute through FSL.

## Reproduction

```sh
python3 tools/fsl_migrate.py --fission-root Fission --output-dir /tmp/fsl-migration
make migration-reproduce
python3 tools/migration_reproduce.py --fslc <Fission-worktree>/target/debug/fslc
```

The importer requires the pinned snapshot. Reproduction regenerates four
artifacts in a temporary directory and compares their bytes. The optional
compiler checks ABI parsing and migrated FSL execution. CI also compares the
three source copies against the pinned native compiler's fixtures. Historical
artifact locks remain a separate gate.

## Remaining conversion work

This importer admits an explicit entry/token/binding/constructor shape. It is
a leaf probe, not a general SLEIGH preprocessor/compiler. The SLA's 9,036-node
numeric tree is structural evidence; direct decision/context/ConstructTpl
lowering to FSL/FIR is unsupported.

Next: register layouts/overlapping slices and ABI linking/allocation, then
direct SLA semantic lowering with explicit unsupported-operation records.
The [native contract](https://github.com/fission-systems/Fission/blob/cfcb0e0f3635849e5bcfd23d4f94def0ccd2094d/docs/research/fsl-state-and-migration.md)
also specifies the next EXEC/lane domain in the same canonical FIR.

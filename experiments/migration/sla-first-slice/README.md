# Direct SLA symbol/template slice

Pinned input: Fission `96fc71f75cecdee305faf9497561c577a8955468`,
`utils/sleigh-specs/compiled/eBPF/eBPF_le.sla` (SHA-256
`7af0479005e8b93385783cc78a60b27eaef0afde2f546af6b3bc45ec23eb63dd`).
The importer reads the binary directly. It never reads `.sinc`/`.slaspec` or
executes a legacy decoder. Versioned primary format references and attribution
are in `data/sla-v4-format.lock.toml` and the migration report.

## Admitted path

SLA symbols → byte spaces / 12 register views → selector tables / holes →
instruction decision constraints / first-match pair priority →
ConstructTpl BUILD → pure register export → INT_ADD → owned FSL → canonical FIR.

The semantic body is selected by admitted ordered atom/opcode shapes. No known
instruction byte, mnemonic, constructor ID or source line chooses its meaning.
Opcode 60 is a Sleigh BUILD directive in this template context, not executable
phi semantics. Unknown nodes/effects stop conversion. Interpreted ancestor
decision bits constrain each leaf pair; earlier competing pairs refuse, later
overlaps are recorded. The actual ADD pair precedes an overlapping broad jump
pair in this SLA.

There are 129 constructors, including 98 root constructors. The report records
one partially converted root (register branch), its consumed pure export
dependency and all other unsupported constructors. The immediate export branch
refuses. This does not establish semantics for the remaining instructions.

Generated `.fsl` and `.fslregs` text compiles/links with Fission's owned compiler.
The portable package remains v3; `source.lock.toml` pins its SHA-256. Native
execution and recompilation do not load SLA or vendor implementations.

## Evidence

- Source/SLA layout, encoding and canonical FIR agree.
- 65,536 opcode/selector prefixes compared; both candidates admit 121.
- SLA candidate: 484 synthetic states, 1,936 C/Rust O0/O2 comparisons.
- Another 484 states verify SLA-derived byte storage plus ABI linking.
- Legacy SLA runtime: 121 length/register/IntAdd comparisons. Shared lineage;
  not independent architecture/verifier proof.
- Eight mutated opcode, context, extra-effect, handle, BUILD, selector, export
  and pair-priority cases refuse before executable conversion.
- Native crate: 32 tests; Python: 14 tests; existing execution/recompilation
  gates rerun. Format/Clippy pass.

```sh
make sla-migration-reproduce
python3 tools/sla_migration_reproduce.py --fslc /absolute/path/to/fslc
```

Three golden artifacts regenerate exactly; four native CLI gates parse, link
and execute the package, and the package hash must match. CI uses a compiled-SLA
only sparse checkout to demonstrate that source grammar is unavailable. Reports
are written to `artifacts/sla-migration.json`, including failures.

General context/default state, variable-length/context-dependent decoding,
dynamic handles, other opcode bodies, memory/control flow, whole functions/VMs,
GPU lane layout/kernel ABI and hardware execution remain unsupported. eBPF R10
binding follows the source SLA; verifier legality of writing it is not claimed.

# Owned loader profiles: first compiled catalog

2026-10-19. Native implementation:
[`b8114a927`](https://github.com/fission-systems/Fission/commit/b8114a927),
experimental branch `codex/fsl-jvm-iadd-parity`.

This step separates owned profile policy from the canonical format mapper.
Existing product loading still follows its SLEIGH-compatible path. The new
entry point is explicit and currently supports ELF only.

```text
ELF schema facts -> owned profile catalog -> existing ELF mapper
  -> canonical LoadedBinary -> exact decoder/package binding -> FIR -> C/Rust/Go
```

`elf.fslprofiles` declares two authored rules: little-endian ELF machine 3 / 32
bits and machine 62 / 64 bits. Both select `owned-x86-v2` and bind the existing
encoding/FIR package by SHA-256. ABI is explicitly unselected. Compiler, OS ABI,
register policy and injected effects are not inferred from these headers.

The loader owns typed header facts, immutable catalog matching and selection
errors. It rejects overlapping rules rather than using declaration order.
The format implementation owns sections, addresses, relocations and symbols;
there is no second ELF parser or separate program metadata database. The new
`ProfiledBinary` wraps the canonical binary and its selection. Existing serialized
binary fields remain unchanged. Product snapshot/consumer migration is future work.

## Recorded evidence

- The source compiled into **two records / 310 bytes** (`elf.fslpc`).
- `build-local.json` binds source, catalog, compiler binary and native revision.
- Loader/FSL compilation passed; strict FSL Clippy passed with `loader` and
  `x86`; downstream decompiler/CLI compilation and workspace formatting passed.
- **Runtime profile selection, decompilation, regression tests, execution parity
  and resource isolation were not performed in this step.** No such results
  should be inferred from compilation success or the new API's existence.

This is not migration of the existing `.opinion/.ldefs` corpus. These are
self-authored rules for the existing bounded x86 package, not new architectures.
The current ABI is unselected; general function recovery and product cutover
remain incomplete. The preceding [owned ELF isolation evidence](../../pipeline/owned-elf/README.md)
uses its earlier pinned route and does not validate this new catalog path.

## Recreate the catalog

Build the pinned native revision, then from this repository root:

```sh
/path/to/Fission/target/debug/fsl-x86 compile-profiles experiments/migration/loader-profiles/elf.fslprofiles artifacts/elf.fslpc
```

The compiler accepts a bounded version-one text grammar and produces binary
`FSLPROF1` records; JSON is only used for this experiment's report/lock. See the
[native contract](https://github.com/fission-systems/Fission/blob/b8114a927/docs/research/fsl-loader-profiles.md)
for binary layout, grammar limits and entry points. The following are available
commands, **not recorded runtime validation results**:

```sh
fsl-x86 inspect-profiles CATALOG.fslpc
fsl-x86 select-profile CATALOG.fslpc INPUT.elf
fsl-x86 decompile-profiled CATALOG.fslpc INPUT.elf ADDRESS SIZE c NEW_DIRECTORY
```

Next: import and resolve actual loader/profile assets, extend selection evidence
and ABI contracts, exercise the new route on the fixed binary corpus and
validate product consumers before switching them. The
[staged migration plan](../../../docs/sleigh-asset-migration-plan.md) remains the
retirement gate.

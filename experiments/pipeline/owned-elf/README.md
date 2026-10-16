# Asset-independent ELF -> FSL -> FIR -> source — 2026-10-16

Native pin: `bbf6a1992bba2a32aa4a0499ee59c03fdc76b222`. Experimental branch `codex/fsl-jvm-iadd-parity`, PR #176.
The target is a complete SLEIGH/SLA-independent pipeline. This slice establishes
a selected ELF span route; it does not complete general function recovery.

## What changed

The old owned instruction frontend still called a loader that resolved ELF
architecture through Ghidra `.opinion`/`.ldefs`. Absence of a Sleigh crate alone
was not sufficient evidence of asset independence. The new opt-in loader route
uses canonical ELF mapping/relocation/symbol code and explicit machine/class/
endian facts for i386/x86-64. ABI is unselected; no BinaryLoadSpec or fake Ghidra
language ID is created. The legacy default loader route remains separate.

`decompile-owned` compiles the embedded owned x86 v2 FSL profile in memory, binds
canonical FIR and emits checked C/Rust/Go. No package argument, legacy spec file,
Sleigh runtime, P-code conversion or legacy fallback is used in this route.
The profile remains 48 rules / 150 width-specific bodies.

```sh
fsl-x86 decompile-owned INPUT.elf ADDRESS SIZE c|rust|go NEW_DIRECTORY
```

Six files: source, diagnostic FIR, portable `profile.fslxc`, `pipeline.txt`,
`projection.txt`, `build.txt`. The directory must be new. An I/O failure can leave
a partial directory. Source still uses explicit state; function boundaries and
source signatures are not inferred. Unsupported format/encoding/backend refuses.

## Evidence and scope

The gate checks nine C/Rust/Go bundles from three locked actual AMD64 immediate
store ELF spans. All package, FIR and source bytes must match previous locks;
those source outputs have separate execution evidence. Nine sources compile,
nine existing-directory writes refuse unchanged, and unsupported opcode/backend
refuse without creating outputs: 11 refusal checks. This gate does not rerun
original/recompiled execution and does not claim new instruction coverage.

Dependency closure refuses fission-sleigh, fission-pcode, fission-decompiler,
iced-x86, Capstone and Zydis. Local mode copies only executable/inputs and uses an
empty cwd, resource roots, HOME and PATH; other host files remain accessible.
The local report is not filesystem isolation evidence.

Dedicated Linux CI fetches `crates`/`.cargo` without utils/vendor or legacy
asset extensions, builds there, then traces the executable in a chroot containing
only its system libraries and input ELF files. It rejects attempted legacy file
accesses, including failed opens. This is a resource closure experiment, not a
security sandbox. CI completion and its report are recorded separately.

```sh
python3 tools/owned_pipeline_reproduce.py --compiler-root /absolute/compiler \
  --fsl-x86 /absolute/compiler/target/debug/fsl-x86 --cc clang-18 \
  --cargo 'rustup run 1.98.1 cargo' --rustc 'rustup run 1.98.1 rustc'
# On Linux with sudo/strace/chroot: add --isolate
```

## Remaining target

The product decompiler still uses SLEIGH/NIR/HIR. The owned pipeline currently
supports only caller-selected executable ELF spans and bounded explicit state.
Next: FSL-owned profile/ABI contracts, CALL/callee state, reliable function CFG/
entry/return recovery, then projections with evidence-backed source prototypes.
PE/Mach-O and other ISAs, full x86 coverage, guest fault/concurrency semantics,
whole Python/JVM/WASM methods and full-product replacement remain incomplete.
The research/SLA importer and independent legacy comparison gates remain offline
references; they are not required to run this new entry point.

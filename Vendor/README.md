# GPU source references

Captured 2026-10-01 for independent FSL/FIR research. These are local upstream
checkouts, not linked runtime dependencies. The exact revisions, license-file
hashes, working-tree status, and AMD XML hashes are in
[`references.lock.toml`](references.lock.toml). Large checkouts and downloads are
ignored by the parent repository; this index and the lock file remain trackable.

| Vendor | Checkout | Role | First source locations |
|---|---|---|---|
| NVIDIA | [envytools](https://github.com/envytools/envytools) | Table-driven assembler/disassembler and hardware documentation | `envydis/dis-intern.h`, `envydis/gm107.c`, `envydis/gk110.c`, `docs/` |
| NVIDIA | [CuAssembler](https://github.com/cloudcores/CuAssembler) | SASS assembler, encoding repositories, cubin and control-code handling | `CuAsm/CuSMVersion.py`, `CuAsm/CuControlCode.py`, `CuAsm/CuInsAssembler.py`, `CuAsm/InsAsmRepos/` |
| AMD | [isa_spec_manager](https://github.com/GPUOpen-Tools/isa_spec_manager) | Official XML-based ISA decoder and explorer | `include/amdisa/isa_decoder.h`, `source/common/isa_xml_reader.cpp`, `source/isa_decoder/` |
| AMD | [radeon_gpu_analyzer](https://github.com/GPUOpen-Tools/radeon_gpu_analyzer) | Offline compilation and code analysis; ISA parsers and program graphs | `source/radeon_gpu_analyzer_backend/emulator/parser/`, `source/radeon_gpu_analyzer_cli/kc_utils_binary_parser.cpp` |
| Intel | [intel-graphics-compiler](https://github.com/intel/intel-graphics-compiler) | Compiler plus IGA assembler/disassembler and GED encoding tables | `visa/iga/IGALibrary/Models/`, `visa/iga/IGALibrary/Backend/`, `visa/iga/GEDLibrary/` |

These references primarily expose encoding, decoding, assembly, and analysis.
They do not establish that full high-level decompilation or executable semantic
recovery is available. A decodable instruction is not automatically a validated
FIR instruction.

## Official AMD ISA snapshot

`amd-machine-readable-isa/specs.zip` was downloaded from
[AMD's machine-readable ISA page](https://gpuopen.com/machine-readable-isa/),
using its `https://gpuopen.com/download/machine-readable-isa/latest/` link.
The extracted directory contains 10 XML specifications: CDNA 1–5 and RDNA 1,
2, 3, 3.5, and 4. Each document declares its license and schema version;
individual metadata and counts are recorded in the lock file. This archive does
not supply the existing GFX900/Vega profile. GFX900 and RDNA must remain separate.

The `latest` URL is mutable. Reproduction requires matching the recorded SHA-256;
a different archive is a new snapshot, not the same input.

## Checkout and regeneration

Each repository was cloned with `git clone --depth 1 URL Vendor/NAME`, without
recursive submodule initialization. RGA's installed Git LFS filter fetched its
large binary assets during checkout. The clones have not been built or installed.
For each revision in the lock file, use `git fetch --depth 1 origin COMMIT` and
`git checkout --detach COMMIT` after cloning to select that snapshot.

Generate a fresh inventory without importing upstream Python modules:

```sh
python3 tools/gpu_reference_inventory.py > Vendor/references.lock.toml
```

Compare revisions and hashes before accepting an updated inventory.

### macOS checkout limitation

envytools contains both `nvbios/D.c` and `nvbios/d.c`. On this workspace's
case-insensitive filesystem they collide; Git reports `M nvbios/D.c` immediately
after cloning. Both original blobs remain available through `git show HEAD:path`.
The inspected `envydis` sources are outside that collision. This snapshot is not
a complete faithful filesystem checkout of the VBIOS directory; use a
case-sensitive volume before researching or building that directory.

## License provenance

The inspected root licenses of these five projects are MIT notices; individual
files, bundled dependencies, and data must retain their own notices. The lock
file identifies the exact inspected license files. Encoding facts, descriptive
text, source code, and generated datasets retain distinct provenance. Imported
rules will identify their upstream commit and source path rather than silently
copying a project's code or instruction databases into FSL.

See [GPU FSL reference design](../docs/gpu-fsl-reference-design.md) for the
source-backed compiler requirements and implementation order.

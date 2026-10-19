# SLEIGH asset migration and staged replacement

Decision: **2026-10-19**. Status: accepted migration direction, not completed
implementation. New computation-domain expansion is paused. Work now focuses
on migrating the existing Ghidra/Fission asset corpus and the consumers that
depend on it.

## Transition contract

Keep the existing product SLEIGH path operational while owned specifications,
their compiler and FIR consumers are developed alongside it. Import and validate
the existing asset corpus before retiring the corresponding legacy capabilities.
Remove SLEIGH from normal product builds and runtime only after the full
replacement and consumer migration gates pass.

```text
Pinned Ghidra/Fission assets ── existing SLEIGH/product path
             │                           │
       offline import              comparison results
             │                           │
    reviewable owned sources             │
             │                           │
        FSL compiler                     │
             │                           │
    owned packages / catalogs            │
             │                           │
    common decoder + FIR ───── profile/consumer validation
             │
       explicit cutover
             │
    final legacy retirement
```

The existing asset-independent ELF experiment remains a bounded opt-in route.
It is not evidence that all product consumers can already abandon SLEIGH.
Legacy execution and owned execution must retain separate identities and
diagnostics. Unsupported owned behavior must not be reported as an owned success
by silently using the legacy engine.

## Replace responsibilities, not just extensions

SLEIGH provides instruction decoding and semantic construction. Some surrounding
responsibilities belong to Ghidra's loader, processor/compiler models, analysis
or type/signature services. Their contracts are part of the migration even when
their implementation is outside the SLEIGH engine itself.

| Source family / responsibility | Owned destination and required preservation |
|---|---|
| `.slaspec` / `.sinc` | Reviewable text FSL modules: preprocessing, includes, tokens, constructors/subtables, context, operand rules, display, semantic bodies and user-operation declarations. |
| `.sla` | Validated owned compiled packages: decode decisions, symbol/operand bindings, context actions and executable FIR meanings. Parsing the packed tree alone is not semantic migration. |
| `.pspec` | Register/context and processor-policy contracts: aliases, program counter, defaults, symbols, address-related policies and referenced behavior. Layout alone is insufficient. |
| `.cspec` | ABI/compiler contracts: data organization, parameter/return allocation, stack behavior, register preservation/clobbers, calling conventions and fixup/injection semantics where present. Metadata alone is insufficient. |
| `.ldefs` | Owned profile catalog: language/variant/version, size/endian, package, processor and compiler-profile references. Preserve explicit identities and selection constraints. |
| `.opinion` | Owned loader-to-profile selection rules, including format/machine/compiler constraints. Unknown or ambiguous evidence must not silently select an ABI. |
| Userops, callfixups and other injected behavior | Executable FIR contracts with effects and state dependencies, or explicit unsupported records. A stored name or opaque P-code body is not a migrated implementation. |
| Additional referenced assets / implementation hooks | Resolve dependencies and identify the actual consumer. Record missing or code-backed behavior rather than declaring a file-only import complete. |
| Fission `.fpk` and adjacent type/signature corpora | Separate family-specific migrations. FPK is Fission's container, not a Ghidra SLEIGH format; prototype, type, ordinal and signature payloads have different contracts. |

The existing proposed `.fslregs`, `.fslabi`, `.fslib` and `.fsldb` destinations
remain described in [the owned asset design](owned-assets-and-structured-fir.md).
Profile/catalog formats and broader policy schemas are still design work.

## Inventory boundary and a concrete gap

The [existing inventory](../experiments/migration/asset-replacement/legacy-assets.json)
is pinned to Fission `96fc71f75cecdee305faf9497561c577a8955468`:

| Family | Files |
|---|---:|
| `.slaspec` / `.sinc` | 146 / 204 |
| `.sla` | 133 |
| `.cspec` | 110 |
| `.pspec` | 83 |
| `.ldefs` | 51 |
| `.fpk` | 261 |
| **Existing inventory total** | **988** |

This inventory counts seven selected extensions under `utils`; it is not the
complete dependency closure of all Ghidra processor definitions. A read-only
inspection on 2026-10-19 found **59 `.opinion` files** under the same pinned
checkout's `utils`, absent from that extension-filtered inventory. This is a
file count, not a migration or validation result. Other referenced files and
code-backed hooks still require a dependency audit.

Preserve the historical inventory and its hashes. The next inventory revision
must add source identity/license, referenced includes and profile relationships,
loader selection assets, unresolved references and consumer ownership. Count
source and compiled counterparts, duplicates and shared includes explicitly;
file counts must not become percentages of semantic support. New source
snapshots must be named and pinned rather than silently expanding the baseline.

## Common decoder direction

FSL must describe variable-length token consumption, conditional fields,
constructor/subtable composition, context updates, operand/address expressions
and rule selection. Its compiler should produce a common executable decode
plan plus FIR templates. x86 prefix, ModRM and SIB rules should become
specification content instead of permanent architecture branches in Rust.

The current `x86_decode.rs` is a bounded bootstrap: opcode choices are
declarative, while significant prefix/operand/length logic remains handwritten.
Migrate that behavior through existing x86 cases before claiming a generic
decoder replacement. Decoded instruction records carry length, operands,
constructor identity and origins; they are not a second semantic IR.

Import encoding and context structure from source or compiled assets while
retaining provenance. Semantic import must map to owned FIR contracts and
preserve unsupported cases. Information already lost during lowering cannot
be assumed recoverable. Final owned sources must compile without the original
SLEIGH compiler or `.sla` inputs; offline import tools remain migration aids.

## Gates and progress accounting

Track each asset/profile and capability separately:

1. **Inventoried:** identity, source hash, license and dependencies recorded.
2. **Represented:** required syntax/metadata/behavior has an owned contract;
   unsupported constructs remain explicit.
3. **Imported:** reviewable owned source is generated and compiles independently.
4. **Validated:** the declared profile coverage passes the relevant comparisons
   and independent semantic checks.
5. **Consumer migrated:** each relying product service uses the owned API/assets
   and its integration checks pass.
6. **Retired:** the legacy product dependency is removed after the complete
   shipping profile/consumer set satisfies the transition gate.

Partial decoding, ABI or semantic progress must not promote an entire profile
to validated. Source and SLA imports can cross-check structure; agreement
between two translations of one source is not an independent semantic oracle.

Validation needs named corpora and coverage contracts for:

- Instruction boundaries, modes, prefixes, context, operands and invalid input.
- Register views, flags, memory, control flow, exceptions and user operations.
- Loader/profile selection and ABI allocation, preservation and injected effects.
- Disassembly, analysis, emulation, decompilation and recompilation consumers.
- Standalone owned builds/installations with legacy resource-access tracing.

Use legacy results as a compatibility baseline and independent ISA references,
execution oracles and scoped proofs to adjudicate differences. Retain old
evidence and provenance as permitted when retiring the product dependency.

## Immediate work order

1. Extend the inventory to referenced assets and consumer dependencies, starting
   with the missing loader/profile selection layer.
2. Define common decoder tokens, context and operand rules; migrate existing
   x86 forms while retaining the existing product route.
3. Extend source/SLA import beyond the current eBPF leaf, including symbol,
   constructor, template and context dependencies with explicit refusals.
4. Implement profile, register/policy, ABI and injected-effect contracts needed
   by the same corpus; validate and migrate consumers incrementally.
5. Retire SLEIGH only after the complete migration and cutover gates pass.

No new migration coverage, runtime switch or deletion is established by this
decision. Current implementation evidence remains in [research status](research-status.md).

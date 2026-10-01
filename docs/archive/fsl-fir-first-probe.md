# Archived: P-code boundary probe

> Superseded as the active research direction. This is a main-Fission engineering question; the research project now focuses on rebuilding the SLEIGH/FSL and FIR stack independently.

Archived on 2026-10-01. References to PreHIR/NIR/HIR below describe the inspected
legacy Fission pipeline, not the accepted single-FIR successor design.

Date: 2026-09-30

Fission checkout: `Fission/` at `96fc71f75cecdee305faf9497561c577a8955468` (`main`, aligned with `origin/main`)

## Question

Does collapsing `IntDiv`, `IntSDiv`, and `FloatDiv` to one PreHIR `Div` lose correctness-critical numeric semantics, or does the existing type evidence preserve what downstream passes need?

## Baseline observed in source

- P-code and the SLEIGH compiler retain distinct unsigned, signed, and floating-point division opcodes.
- `fission-pcode::midend::support::pcode_util::map_binary_op` maps all three opcodes to `PreHirBinaryOp::Div`.
- The expression's result type still comes from the original opcode: floating division yields a float, signed integer division yields a signed integer, and unsigned integer division yields an unsigned integer.
- Operand metatypes are recorded separately for plain variable operands and later used to refine parameter, local, and temporary binding types. This evidence is conservative: it does not replace stronger pointer/aggregate types or change integer width.
- If one lowered variable name is used by operations with conflicting metatypes, the builder keeps the first observation. The source comment calls the value ambiguous and avoids making the result depend on lowering order.

Relevant source locations:

- `crates/fission-pcode/src/midend/support/pcode_util.rs`: opcode mapping, result typing, and `pcode_input_metatype`.
- `crates/fission-pcode/src/midend/builder/expr/op_lowering.rs`: expression lowering and operand evidence collection.
- `crates/fission-pcode/src/midend/builder/state.rs`: per-function operand evidence.
- `crates/fission-pcode/src/midend/builder/mod.rs`: evidence application to bindings.
- `crates/fission-pcode/src/midend/builder/type_hints.rs`: conservative type refinement.

## Initial conclusion

This is not a simple case where numeric-domain information disappears at the P-code-to-PreHIR boundary. Some information is encoded in the result type, and operand-side evidence is carried out-of-band. That may be enough for C-like output, but it does not yet establish that every normalization or analysis consumer preserves the same operation contract. Adding a second explicit division-kind field before checking those consumers risks duplicating information the current type system already carries.

## Smallest useful experiment

1. Trace unsigned, signed, and floating division through P-code, PreHIR, normalization, and rendered NIR/HIR; record which layer owns the operation kind, result type, and operand types.
2. Inspect transformations that consume `PreHirBinaryOp::Div` and determine whether legality depends on the original numeric domain or only on the typed operands/result.
3. Look for cases where one variable receives conflicting operand metatypes, and determine whether the current first-observation policy drops a fact needed by a consumer.
4. Only if a correctness-relevant distinction is missing, prototype an explicit semantic contract and compare it with the existing type-evidence path on the same real corpus rows.

Synthetic coverage can establish representation invariants. Any claim about decompilation quality needs before/after measurements on real corpus binaries.

## Notion sources

- [FSL/FIR design rationale](https://app.notion.com/p/3c2744e97b6f816a91bcf90b62db1a96)
- [FIR semantic preservation and IR boundaries](https://app.notion.com/p/3c2744e97b6f81c8a46cc07f50bd05e7)
- [P-code, P-code+, and FIR compatibility strategy](https://app.notion.com/p/3c2744e97b6f8144b498d4bf6edbe2f6)
- [Migration and experiment plan](https://app.notion.com/p/3c2744e97b6f81ea8ddfe39b6b4cfc79)

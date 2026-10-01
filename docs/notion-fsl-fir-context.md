# Notion context: FSL/FIR and the evidence boundary

Read from the connected Notion workspace on 2026-09-30. The source pages below were marked `unverified` by Notion where verification metadata was available. Treat them as design notes, not a settled architecture or a claim about the current Fission implementation.

## What the notes propose

- [FSL: external architecture specification system](https://app.notion.com/p/3c2744e97b6f81f8bbebc6b482178962) proposes a new source-to-package pipeline inspired by SLEIGH's declarative decoding and compiled architecture package model. It explicitly does not aim for source compatibility with SLEIGH. Its central hypothesis is that ordinary architecture additions should be data/spec work rather than Fission-core code changes.
- [FIR: semantic preservation and IR boundaries](https://app.notion.com/p/3c2744e97b6f81c8a46cc07f50bd05e7) proposes shared infrastructure with multiple semantic domains rather than one flat universal vocabulary. It calls out semantic, structural, and transformation-legality preservation, and proposes Reconstruction Cost as a way to measure how much useful structure lowering forces later passes to rediscover.
- [Why FSL/FIR emerged](https://app.notion.com/p/3c2744e97b6f816a91bcf90b62db1a96) frames the work as a response to the long-term role of static semantic infrastructure, not as a desire to rewrite SLEIGH for its own sake. It names provenance, effects, control/concurrency, validation, and explicit uncertainty as useful outputs for both traditional analysis and AI consumers.
- [Migration and experimental plan](https://app.notion.com/p/3c2744e97b6f8171b962c6b88d1d74b7) puts evidence before broad migration: establish parity and quality baselines, measure semantic-identity experiments, then prototype small architecture slices. Its 2026-08-22 alignment note specifically says FSL/FIR remains a research hypothesis and P-code+ evidence should precede main-project adoption.

## How this research repository uses that context

This repository is explicitly a separate, open-ended research project. It can explore larger targets—including GPU native code, VM bytecode, runtime/driver paths, and a new specification/compiler stack—in parallel with the narrower evidence-first sequence recommended for changes to the main Fission project. Findings here do not imply that the main project has adopted FSL/FIR or that a prototype is ready to migrate.

The local experiments keep four claims separate:

1. **Decode:** a pattern matches bytes and extracts fields.
2. **Semantic candidate:** a source or tool suggests an operation/effect.
3. **Validated semantics:** independent evidence supports the operation over a stated profile and version range.
4. **System behavior:** runtime, driver, firmware, or hardware behavior is separately observed or source-traced.

The GFX900 decoder is at the decode level for four patterns, and its FIR-like effects remain candidates. A second slice decodes the JVM SE 26 `iadd` opcode and carries a primary-specification-derived FIR candidate through C/Rust, stack IR, analysis graph, and AI-evidence projections. Those source-code strings and graph records are not execution validation or proof that a general FIR contract is complete. The ROCm/KFD document is a pinned source trace, not a hardware execution trace. These experiments are starting points for an evidence model, not proof that FSL/FIR is complete or that GPU/JVM execution models have been captured.

## Design constraints carried into the prototype

- Keep encoding, operand decode, display, semantic claims, and provenance independently inspectable.
- Preserve a compiled package boundary, but keep the authoring syntax explicitly experimental.
- Fail closed on unknown encodings, ambiguous rules, unsupported operand selectors, and unresolved semantic effects.
- Record losses at boundaries; do not silently call a candidate summary executable FIR semantics.
- Use architecture slices to pressure-test the model. A new target that requires new runtime-specific decoding code is evidence that the current FSL abstraction is still incomplete.

## Open research questions

- Can source-level Sleigh constructors and compiled SLA decision trees be represented by one provenance-preserving FSL package model without copying Ghidra's implementation assumptions?
- Which operand transforms can be described declaratively, and which require a narrowly defined extension mechanism?
- Which FIR facts must remain first-class for safe transforms in SIMT, stack-VM, and VLIW domains?
- Can a compact pattern/effect/provenance package measurably improve AI decode accuracy, explanation grounding, and calibrated abstention under a controlled same-model evaluation?
- Which GPU runtime/driver facts are recoverable from public source, and which need a device trace or remain behind firmware/hardware boundaries?

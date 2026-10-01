# SLA corpus scan

Date: 2026-09-30

Reference checkout: `Fission/` at `96fc71f75cecdee305faf9497561c577a8955468`

Spec manifest: `Fission/utils/sleigh-specs/ghidra_language_manifest.json`

## Result

The independent packed-tree probe parsed **133 of 133 compiled `.sla` files** in the snapshot. All were format v4. It visited **13,767,725 elements** across **90,892,867 decompressed bytes**; the `.sla` files total **11,701,978 bytes**. The largest observed tree depth was 27. No sample exceeded the parser's 512 MiB expansion bound or 16,384-level tree bound.

| Largest payloads | Decompressed bytes | Element nodes |
|---|---:|---:|
| x86 `x86-64.sla` | 4,124,687 | 616,833 |
| AArch64 `AARCH64_AppleSilicon.sla` | 4,053,946 | 570,287 |
| AArch64 `AARCH64BE.sla` | 4,045,908 | 568,874 |
| AArch64 `AARCH64.sla` | 4,043,534 | 568,910 |
| x86 `x86.sla` | 3,436,076 | 514,436 |

The source manifest lists **146 variants across 38 processor directories**. JVM and Dalvik have both source specs and compiled SLA artifacts in this snapshot. No Python or GPU SLEIGH language entries appeared in the mirrored source set, so those will need separate specifications and corpus sources.

The JVM sample shows why a useful database needs more than a flat opcode list. Its SLA contains eight named subtables. The `instruction` subtable has 223 constructors and 223 decision-pair references; seven additional one-constructor subtables provide reusable decode pieces. Each pair's constructor index is meaningful within its parent subtable, so the raw pair ID alone is not a globally unique instruction identity. Constructor records also carry source-file index and source line, a print template, and a `ConstructTpl`; the decision tree carries the encoding-side structure. The importer needs to join these structures while retaining subtable scope and source provenance.

The individual file paths, SHA-256 hashes, compressed and decompressed sizes, node counts, and parse status are recorded in [`data/sla-corpus-2026-09-30.json`](../data/sla-corpus-2026-09-30.json). This is a structural inventory, not a decoded instruction-pattern database: constructor-to-pattern-to-semantic relationships still need to be extracted and checked against source.

## What this proves

- The SLA outer layer and generic packed element framing are tractable to parse independently for this snapshot.
- The existing binary contains useful processor and VM language data, not just native CPU ISAs.
- A numeric-ID tree walker alone is insufficient for FSL: the next layer must map versioned elements and attributes, resolve symbols, extract decision patterns, and connect constructors to ConstructTpl semantics and source provenance.

## Reproduction

From the research workspace root:

```sh
python3 tools/sla_corpus_scan.py Fission/utils/sleigh-specs/compiled \
  --output data/sla-corpus-2026-09-30.json
```

This command scans research inputs and writes the structural inventory. It does not modify the Fission checkout.

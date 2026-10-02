# Register layout and ABI linking slice

Input: Fission/Ghidra mirror snapshot
`96fc71f75cecdee305faf9497561c577a8955468`. This directory records independently
generated FSL text, source hashes, overlapping views and attribution. Native
model/parser/storage/linker live in the Fission experimental branch.

| Profile | Spaces | Views | Overlapping pairs | Strict ABI result |
|---|---:|---:|---:|---|
| BPF LE | 4 | 15 | 15 | Refused: RS=4 bytes, cspec pointer_size=8 |
| eBPF LE | 3 | 12 | 0 | Linked |
| eBPF BE | 3 | 12 | 0 | Linked |

The importer preserves byte offsets, placeholders/holes, widths, space address
sizes, byte order and default memory. Only the unconditional declaration prefix
is admitted; constructors are not lowered here. No BPF BE entry exists in this
input corpus. BPF BE alias behavior is tested only as a synthetic layout.

eBPF ABI resolution retains ordered R1..R5 input entries, R0 output and R6..R10
preserved effects. R10 resolves to register offset 80, width 8. Byte ranges and
unknown register/space names are checked; conflicting preserved/clobbered views
are refused. BPF metadata remains unchanged. Its strict stack-width refusal is
a supported-contract boundary, not a general assertion about all ABI models.

Native byte storage shares overlapping views. Partial writes preserve other
bytes; architectural zero extension/read-only rules are not inferred. An
explicit slot adapter executes existing FIR and commits bytes only after
success. Bound slots must be disjoint and exactly match integer widths. Same
operand selector aliasing is supported; inter-slot view aliasing is refused.

Validation: seven new native tests, 968 synthetic byte-storage comparisons,
three layout parses, two ABI links, one expected ABI refusal and two CLI leaf
executions. The 968 comparisons use the LE instruction profile with two storage
byte orders (484 each); they do not establish BE instruction decoding. Existing
C/Rust recompilation gates are rerun separately. The new storage adapter has
reference execution only. The synthetic flag binding gate checks carry and
invalid u1 storage without claiming an imported GPU register layout.

```sh
make layout-reproduce
python3 tools/register_layout_reproduce.py --fslc /absolute/path/to/fslc
```

Golden sources and `layout-migration.json` must reproduce exactly. Native
observations are emitted to `artifacts/register-layout.json`; a captured local
validation record documents scope and results. No Vendor runtime dependency,
binary layout/ABI package, parameter allocator, call execution, GPU lane layout,
kernel ABI, hardware execution or direct SLA-to-FIR semantic conversion exists
in this slice.

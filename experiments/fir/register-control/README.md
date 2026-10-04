# Integer conversion and register-state semantic-body CFG

Date: 2026-10-04. Native owner: Fission `fission-fsl` on
`codex/fsl-jvm-iadd-parity`, compiler [`7f7b22a34`](https://github.com/fission-systems/Fission/commit/7f7b22a344851aa6a5abcd3738fac979202f20eb), [PR #176](https://github.com/fission-systems/Fission/pull/176).
This repository stores the self-authored input and reproducible outputs.

The same canonical FIR now has strict `int.zext`/`int.sext`/`int.trunc` and
acyclic register/flag block execution. Widths are 1..64; extension is strictly
wider, truncation strictly narrower, signedness must match (zext unsigned,
sext signed). No second IR or P-code lowering is involved. `.fslc` v7 adds one
conversion op; previous versions and locked artifacts stay byte compatible.

The fixture captures an i8/u8 register input, zero extends it to an auxiliary
slot, sign extends and compares it, then writes only the chosen branch. A join
reads the destination after that write and observes branch-written flags. Edge
arguments carry SSA snapshots; the one mutable register/flag context retains
ordered effects. This is not first-class effect SSA or memory state threading.
Writes replace a logical slot with the raw result; the mixed widths are not a
partial byte-view write or proof of register-layout adapter compatibility.

| Native gate | Inputs | C/Rust O0/O2 comparisons |
|---|---:|---:|
| 24 conversion profiles, signed boundaries and unusual widths | 3,072 reference/oracle states | 12,288 |
| Register CFG, 256 inputs × 27 alias placements + eight failures | 6,920 reference/oracle states | 27,680 |
| Constructed carry CFG at 32/64 bits | 2,048 reference/oracle states + 12 source ABI failures | 8,240 |

There is also a separate 6,912-case exhaustive register reference gate, package
compatibility/validation, cycle refusal and native CLI testing. These counts
are not independent hardware evidence. C/Rust builds deny warnings. Failure
comparisons include full backing storage, including outside supplied slices.

Preflight includes selectors/effects in untaken branches. Invalid raw fields,
short banks, non-u1 flags and cyclic execution refuse before any writes. This
is a conservative backend ABI constraint, not an architecture trap model.

```sh
python3 tools/register_fir_reproduce.py --fslc /absolute/path/to/fslc
# In the native experimental worktree:
cargo nextest run --locked -p fission-fsl -j 1
```

`register.lock.toml` pins source, 803-byte package, and FIR/C/Rust hashes. The
Python reproducer checks 44 independent native CLI states and three failures.
CI rebuilds the compiler from its pinned commit and runs the native gates plus
this reproducer. `validation-2026-10-04.json` records the observed local gates.

**Limits:** validation is based on self-authored specifications. Real binary
function lifting, loop execution, memory/calls/exceptions, GPU CFG/divergence,
GPU hardware execution and structured native JIT/AOT are unsupported. CUDA/PTX
backends refuse these bodies. The next bounded step is multi-instruction
register-state composition with explicit origin and state contracts before
attempting binary function lifting.

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="image/fission-research-logo-dark.svg" />
  <img src="image/fission-research-logo.svg" alt="Fission Research — semantics, evidence and experiments" width="880" />
</picture>

[![Research reproduction](https://github.com/fission-systems/fission-research/actions/workflows/reproduce.yml/badge.svg)](https://github.com/fission-systems/fission-research/actions/workflows/reproduce.yml) [![Stage: experimental](https://img.shields.io/badge/stage-experimental-7B61FF)](#current-scope) [![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**[Architecture](#one-semantic-core) · [Current scope](#current-scope) · [Evidence](#evidence) · [Reproduce](#getting-started) · [Documentation](#documentation)**

</div>

---

# Fission Research

Research toward recovering program semantics, preserving behavior, and rebuilding
executable programs across different computational models.

We are developing **FSL**, an architecture description language, and **FIR**, a
single semantic intermediate representation, for the [Fission ecosystem](https://github.com/fission-systems/Fission).
The long-term goal is an owned pipeline for decoding, analysis, decompilation
and recompilation that no longer requires SLEIGH, SLA or P-code. **Correctness
comes before readability.**

This is an experimental research repository. Selected instruction windows,
circuits and authored kernels work today; general function recovery and a
complete replacement of the product decompiler remain open work.

## What we are investigating

- **An owned specification language.** Describe encodings, operands, context,
  types and instruction effects in text FSL; compile them to binary packages.
- **One semantic owner.** Preserve values, control flow, machine state and ordered
  effects in FIR; derive different outputs from the same representation.
- **Evidence that travels with the program.** Retain source provenance, byte
  origins, architecture/version scope, validation results and unsupported cases.
- **Behavior-preserving reconstruction.** Compare original execution, reference
  semantics and recompiled output; use formal checks where their scope is precise.
- **Different models of computation.** Investigate CPU, GPU, VM, quantum and
  reconfigurable hardware without assuming that every domain behaves like a CPU.

Whether a richer semantic representation improves recovery is a research
question. A larger IR, a successful decode or a passing fixture is not enough
to establish that result.

## One semantic core

The intended structure is:

```text
Instruction bytes / bytecode / circuit descriptions / authored kernels
                                │
                      FSL specifications
                                │
                validated decode + semantic bodies
                                │
                               FIR
                   values · blocks · state · effects
                         origins · provenance
                                │
         ┌──────────────────────┼──────────────────────┐
    C / Rust / Go        CUDA C++ / PTX         Verilog / graphs
         │                      │                      │
    recompilation        GPU projection         circuit synthesis
```

Each path has its own admission rules and implementation limits. FIR owns the
semantics; outputs are projections of it. This research does not introduce a
separate NIR/HIR semantic hierarchy.

| Component | Responsibility |
|---|---|
| **FSL** | Encoding rules, operand binding, context and typed semantic definitions. Current native packages are binary `.fslc`, not JSON source specifications. |
| **FIR** | Typed operations, block arguments, explicit state and effects, origins and unsupported semantics. Domain-specific contracts are still being developed. |
| **Semantic corpus** | Connect patterns and semantics to versions, sources and validation evidence. Queryable AI-assisted recovery and its evaluation remain research goals. |

Read the [semantic contract](docs/fir-semantic-contract.md),
[accuracy and evidence rules](docs/fir-evidence-and-accuracy.md), and
[computational domain contracts](docs/computational-domains.md).

## Migration strategy

Keep the existing SLEIGH product path operational while migrating the complete
existing Ghidra/Fission asset corpus into owned specifications. This includes
decoding and semantics, register/context policies, ABI/compiler models,
loader/profile selection and injected behavior. Importing `.sla` files alone
does not replace these responsibilities.

The transition is **inventory → import → validate → migrate consumers → retire
SLEIGH**. Final owned builds must compile and run without legacy tools or assets;
legacy removal comes after the full migration and cutover gates pass.
New computation-domain expansion is paused. See the
[asset migration and replacement plan](docs/sleigh-asset-migration-plan.md).

## Current scope

Snapshot: **2026-10-19**. These are bounded implementations, not complete
architecture or device support. Detailed observations and revisions are in
[research status](docs/research-status.md).

| Area | Implemented slice | Still open |
|---|---|---|
| **Owned x86 pipeline** | 48 encoding rules / 150 width-specific FIR bodies; selected ELF i386/x86-64 spans; register, flag, bounded memory and stack effects. No external instruction decoder or SLEIGH/P-code fallback in this route. | Full x86 coverage, function CFG discovery, calls and general source ABI recovery. |
| **Loader profiles** | An opt-in owned catalog separates ELF header facts, profile selection and mapping; two authored rules compile to `.fslpc` and pin the encoding/FIR package. Runtime selection and package binding are exercised by the scalar-function experiment. | opinion/ldefs corpus import, general compiler/ABI policy and product consumer migration. |
| **Scalar C functions** | Owned ELF catalog → FIR CFG/dependency/ABI checks → C; three authored functions × O1/O2, 24,576 recompiled execution comparisons. | Calls, loops, data memory, source types and general function recovery. |
| **GPU** | GFX900 encoding experiments; SGPR/SCC scalar add/carry and wave64 `v_add_u32` with masked lane writes; limited CUDA C++/PTX projections. | Kernel ABI/layout integration, memory, divergence and hardware execution validation. |
| **VM** | JVM `iadd` decode and multiple FIR projections. | Complete JVM methods, CPython and WASM frontends. |
| **Quantum** | Small reference circuits, declared noise channels, bounded control flow, limited OpenQASM and reference QISA words; one actual IBM Bell-circuit observation. | General QPU binaries, current device calibration correction and general quantum programs. |
| **FPGA** | Eight authored FIR functions through Verilog, iCE40 synthesis, placement/routing and HX8K/CT256 bitstream generation. | Board pin/electrical contracts, clocked runtime, board execution and formal bitstream semantics. |
| **Other computational models** | DSP saturation, scalar tensor dot, MAC, discrete LIF/RC steps, PIM placement metadata and a dataflow DAG. The same kernels can be mapped to FPGA. | Device ISAs/runtimes, tensor storage/layout, event timing, PIM memory effects, continuous dynamics and CGRA scheduling. |
| **Output backends** | Checked C, Rust and Go state-code projections; bounded GPU and HDL outputs; ordinary C machine-word functions for an explicit x86-64 integer leaf contract. | Original source prototypes, general ABI recovery and complete Python/Java output. |
| **Legacy asset migration** | SLA structural parsing, one eBPF semantic leaf, register/ABI metadata and library candidate migration. | Complete replacement of SLEIGH/SLA/cspec and product integration. |
| **DecBench** | Sample-set static coverage adapter and 250 measured entry addresses. | Submission-ready function C output and scored evaluation. Current eligible output: **0 / 250**. |

## Evidence

The [scalar-function experiment](experiments/pipeline/scalar-functions/README.md)
connects the owned loader catalog to ordinary C machine-word functions. Its
compiler-constrained authored corpus is separate from DecBench eligibility.

Experiments retain inputs, compiler pins, hashes, tool versions, outcomes and
limitations. These results measure different contracts and are not a single
project-wide correctness score.

| Experiment | Recorded result | What it establishes |
|---|---|---|
| [Owned ELF isolation](experiments/pipeline/owned-elf/README.md) | Nine C/Rust/Go bundles; 20 Linux traces with zero attempted legacy asset accesses. | A selected-span pipeline can run without legacy specification assets. General function recovery is not established. |
| [Initial fabric slices](experiments/fabric/initial-slices/README.md) | 184,424 FIR/oracle/RTL cases; 737,696 C/Rust executions. | Agreement on authored bit-vector functions and the recorded test inputs. |
| [iCE40 synthesis and proofs](experiments/fabric/ice40-hx8k/README.md) | Eight RTL/formula SAT proofs, eight mutation counterexamples, 145,336 mapped-netlist cases and eight generated bitstreams. | RTL agrees with the authored formulas for all two-valued input slots. Synthesis/routing/bitstream semantics are not formally proved; no board ran. |
| [IBM QPU observation](experiments/quantum/ibm-hardware-bell-xx/README.md) | One Bell XX circuit; 1,024 shots; 6.54% total variation distance from the ideal distribution. | A physical QPU observation. The recorded ideal-distribution comparison criterion **did not pass**; this is not equivalence evidence. |
| [DecBench sample-set baseline](experiments/decbench/sample-set/README.md) | 250 entries attempted; all refused at current support boundaries; zero eligible function outputs. | Static coverage and refusal evidence. No benchmark score was produced. |

Unsupported semantics must be reported explicitly. An encoding match does not
establish execution semantics; sampled agreement does not establish a proof;
a proof of an authored model does not establish correctness on real binaries.

## Getting started

This repository contains research tools and artifacts. The native Rust compiler
lives in the separate [Fission experimental branch](https://github.com/fission-systems/Fission/tree/codex/fsl-jvm-iadd-parity)
and [PR #176 — Project Fission: A Unified Semantic Engine](https://github.com/fission-systems/Fission/pull/176).
Each experiment pins the compiler revision it uses.

To clone the research repository and inspect the frozen fabric evidence with
Python 3.12+:

```sh
git clone https://github.com/fission-systems/fission-research.git
cd fission-research
python3 tools/fabric_capture_check.py
python3 tools/fabric_ice40_capture_check.py
```

These commands check archived file integrity; they do not rerun the experiments.
For actual regeneration, follow the experiment's prerequisites and commands:

- [Owned ELF → FSL → FIR → source](experiments/pipeline/owned-elf/README.md)
- [Owned loader profile catalog](experiments/migration/loader-profiles/README.md)
- [Owned ELF → FIR → scalar C functions](experiments/pipeline/scalar-functions/README.md)
- [FIR → RTL → iCE40 bitstream](experiments/fabric/ice40-hx8k/README.md)
- [C/Rust/Go output contracts](experiments/output/backend-contract/README.md)
- [Historical artifact reproduction](docs/reproduction.md), including `make reproduce`
  and its pinned SLA comparison inputs

[GitHub Actions](.github/workflows/reproduce.yml) is the executable reproduction
workflow. Historical import/comparison jobs and the owned pipeline have different
input dependencies; consult their individual contracts.

## Repository map

| Path | Contents |
|---|---|
| [`experiments/`](experiments/) | Bounded experiments, fixtures, measured reports, source locks and reproduction instructions. |
| [`tools/`](tools/) | Independent probes, importers, execution comparisons and capture checkers. |
| [`docs/`](docs/) | Semantic contracts, architecture, research status and handoff notes. |
| [`specs/`](specs/) | Research specifications, including historical TOML probes alongside later text FSL examples. |
| [`data/`](data/) | Structural inventories and historical pattern artifacts. |
| [`Vendor/`](Vendor/README.md) | Reference source inventory and pinned provenance; local clones are not committed. |
| [`image/`](image/README.md) | SVG wordmarks and the research mark, following the Fission visual family. |

Rust compiler implementation stays in Fission. Reference sources are for
inspection and independent comparison; they are not production dependencies.
The ignored `Fission/` checkout is used by historical comparison experiments.

## Documentation

| Start with | For |
|---|---|
| [Research status](docs/research-status.md) | Observations, exact revisions, measured results and remaining limits. |
| [FIR semantic contract](docs/fir-semantic-contract.md) | The semantic owner and domain requirements. |
| [Owned assets and structured FIR](docs/owned-assets-and-structured-fir.md) | Replacement paths for legacy specifications and assets. |
| [SLEIGH asset migration plan](docs/sleigh-asset-migration-plan.md) | Existing-path retention, complete asset responsibilities, common decoding and retirement gates. |
| [Computational domains](docs/computational-domains.md) | FPGA, DSP, tensor, ASIC, neuromorphic, PIM, analog and dataflow research contracts. |
| [Semantic pattern database](docs/pattern-database.md) | Provenance, confidence and corpus design. |
| [GPU references](docs/gpu-fsl-reference-design.md) · [reference lock](Vendor/references.lock.toml) | NVIDIA, AMD and Intel source evidence. |
| [Maturity comparison](docs/fsl-fir-maturity-comparison.md) | The dated FSL/FIR versus product SLEIGH/NIR/HIR assessment. |
| [AI handoff](docs/ai-handoff.md) · [x86 handoff](docs/ai-handoff-x86.md) | Working context, ownership and continuation instructions. |

## Next research steps

1. Recover function boundaries, calls and ABI contracts from real binaries.
2. Expand owned instruction semantics and complete legacy asset migration.
3. Connect GPU register layout, memory, control flow and kernel ABI.
4. Add clocked fabric interfaces, board constraints and stronger synthesis verification.
5. Develop tensor layout, event/time, PIM memory and continuous-model error contracts.
6. Measure recompilation and semantic-corpus-assisted recovery on independent corpora.

The intended destination is integration into Fission. Research artifacts must
continue to distinguish implemented behavior, measured evidence and future goals.

## License

[Apache-2.0](LICENSE). Referenced projects and imported data retain their own
licenses and provenance; see the [reference inventory](Vendor/README.md).

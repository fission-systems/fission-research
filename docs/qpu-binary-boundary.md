# QPU binary input: first target investigation — 2026-10-17

The current quantum fixtures select authored logical circuits. Their selector
bytes are not QPU opcodes. OpenQASM is source input; FSLC is our portable package.
Neither establishes physical-device binary support.

## Candidate and provenance

Investigate **a pinned eQASM assembler configuration** as the first quantum-control
binary target. The [CC-Light specification](https://arxiv.org/abs/2006.09294)
describes 32-bit words, timing queues, target registers and configurable quantum
operations. The [upstream assembler](https://github.com/QE-Lab/eQASM_Assembler)
exposes assembly/disassembly and configurable instruction mappings.

Cloned to `Vendor/eqasm-assembler` at
`9b024494558287a937cdd5a8ccd63fcaa784b1c4`, develop at capture. Its Apache-2.0
license, opcode map and driver files are hashed under `quantum_repository` in
`Vendor/references.lock.toml`. Source inspection only: not built, linked or run.
The clone stays outside tracked source, as with GPU references.

## Configuration differences discovered

The paper's section 4.15 displays QWAIT with opcode bits corresponding to 0x20;
this pinned assembler's `qisa-as/qisa_opcodes.qmap` uses QWAIT=0x30,
QWAITR=0x38, SMIS=0x20 and SMIT=0x28. The driver uses opcode offset 25.
Its quantum subinstruction uses an eight-bit opcode plus a conditional bit / target
fields, whereas the paper describes nine-bit quantum opcode fields. Its mask/register
widths also differ. Treat these as **different configurations/revisions**, pending
hardware identification; combining their tables would create incorrect semantics.

Accordingly no generic “CC-Light” FSL profile or default gate mapping was added.
Mnemonic names alone are insufficient evidence for pulse or logical gate identity.
The physical opcode map/control store and target-state contract must agree.

## Next executable slice and admission contract

Start with words assembled by the pinned tool and an archived configuration,
then compare owned FSL decode/re-encoding against that tool's output. First
capture the assembler build/config identity, binary byte order, exact QMAP and
raw words. Generated reference binaries must be labeled as such; a device-captured
binary corpus and hardware execution are separate evidence.

Before connecting any decoded word to executable FIR, require:

1. Exact target and opcode-map identity with hashes, including classical opcodes.
2. Target-register mask state, two-qubit topology and bundle concurrency rules.
3. Logical gate/pulse mapping, timing-label/queue semantics and physical clock units.
4. Measurement availability, feedback protocol and explicit initial-state assumptions.
5. Origin spans and source evidence for every admitted word/effect; missing or
   unknown mappings refuse. Timing or unavailable gates never become no-ops.

QWAIT is not an identity gate: it updates timing state. A bundle cannot be lowered
by discarding ordering/timing or assuming that an arbitrary mapped opcode is X/H.
The present logical-noise executor supplies neither timing state nor calibration.
An idealized projection, if later provided, needs explicit preconditions and loss
reporting; it cannot claim equivalent physical-device execution.

This investigation selects a tractable public target and records blockers. It
does **not** add actual QPU binary decoding, firmware recovery or device support.

# FIR → IBM physical circuit → observed counts — 2026-10-17

This stage implements the source projection and an independent submission tool.
**No account was connected, no QPU job submitted, and no current calibration was
fetched.** All committed snapshots and modeled results are explicitly synthetic.
Live API/parser acceptance and hardware comparison remain unverified.

## Native projection

The single canonical FIR remains the semantic owner. `quantum::ibm::emit` accepts
linear ideal H/X/Z/CX/reset/measurement/bit-controlled X plus u1 constants. Native
output is physical OpenQASM 3 with explicit logical-to-physical mapping, reset/X
basis preparation, RZ/SX/X and CX or CZ, and X/Y/Z terminal observations.
H and Z decompositions preserve the instrument up to global phase. Classical
conditions cannot coherently control that phase. No new FIR operation, FSLC
format, Cargo dependency, SDK, routing or scheduler is introduced.

- CX requires the reported forward edge. CZ may use a reported reverse tuple.
- Measurement `trace[i]` maps to a canonical SSA definition; `out[j]` maps to
  logical qubit j in the requested observation basis. Both registers are kept.
- The wrapper prepares an explicit computational-basis state. It does not claim
  to recover an unknown initial device state.
- Integer arithmetic, all explicit blocks/loops, declared noise and unknown
  effects refuse. ECR-only entangling targets are unsupported.
- Missing per-qubit RZ/SX/X capability or reset/measurement availability refuses.
  This conservative snapshot contract may reject configurations with implicit
  capability declarations; no guessed defaults are supplied.

```sh
fslc emit-ibm PACKAGE bell_coherent 7,3 cz 3:7 0 XX /tmp/bell-xx.qasm
```

Native emission alone does not verify a real backend. Comments retain each FIR
operation index; the package and evidence hashes are preserved in the bundle.

## Separate stdlib adapter

`tools/ibm_quantum.py` imports no third-party library. FSL/FSLC remain source and
package formats; JSON carries provider API data, submission envelopes and
research diagnostics. Credentials are read from local environment variables
`IQP_API_TOKEN` and `IBM_QUANTUM_CRN` and are never written to bundles or reports.
Only explicit us-east CRNs are admitted in this first Open Plan adapter.

1. `snapshot` authenticates via IBM IAM, retrieves the current instance, resolves
   its plan ID through IBM Global Catalog and requires a plan named `open`.
   Backend configuration/properties/status and allowance are captured.
2. `prepare` runs offline using that snapshot. It emits physical QASM with the
   owned compiler, executes FIR from the same explicit basis state, and records
   the expected **joint** measurement-trace/terminal distribution. Source FSLC,
   compiler executable hash, layout, axes, properties timestamp and request are
   bound into a manifest. Snapshot checks do not establish live API acceptance.
3. `submit` rechecks the Open Plan, operational device, unchanged configuration,
   CRN hash and sufficient allowance. Exactly one SamplerV2 PUB/job is submitted.
   Synthetic snapshots refuse. Shots are 1..4096; the requested Runtime cost is
   1..60 seconds, placed in the top-level `cost` field like the inspected SDK.
   Its enforcement is provider-defined; it is not an independent billing/time
   guarantee. Paid and unknown plans refuse. No session or automatic mitigation.
4. `collect` reads one bound job. Pending/failed jobs produce `not-compared` and
   exit 2; only provider-reported completion can fetch results and compare.
   Parsed JSON responses, usage/calibration ID when reported, hashes and the
   pre-submission properties timestamp are retained. That properties snapshot
   need not be the calibration actually used by a queued job.

A receipt is saved **before** the single POST. If its outcome is uncertain, no
automatic retry occurs; inspect the IBM workload list using the retained request
identity before creating any new receipt. Collection has no submission path.
Unknown result encodings refuse after archiving the parsed response. The initial
codec supports one scalar Runtime PrimitiveResult/DataBin with shot-major uint8
BitArrays, zlib/base64 NPY v1/v2, and explicit trace/out widths. Parameter sweeps,
object arrays and guessed register orders refuse. Input/response size is bounded
at 8 MiB. Archived JSON preserves parsed values, not original HTTP framing.

## Account and actual hardware workflow

Create an [IBM Quantum Open Plan instance](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview)
in us-east, then configure the two environment variables locally. Do not put the
API key in a chat, command argument, source file or artifact. The current plan
normally supplies 10 minutes per 28-day rolling window; account eligibility and
any promotional allocation must be checked on the platform.

```sh
python3 tools/ibm_quantum.py snapshot --backend YOUR_BACKEND --output /tmp/ibm-snapshot.json
python3 tools/ibm_quantum.py prepare --fslc /path/to/fslc --package /path/to/circuits.fslc --instruction bell_coherent --snapshot /tmp/ibm-snapshot.json --layout 0,1 --initial-basis 0 --axes XX --shots 1024 --max-seconds 60 --output /tmp/ibm-bundle
python3 tools/ibm_quantum.py submit --bundle /tmp/ibm-bundle --receipt /tmp/ibm-receipt
python3 tools/ibm_quantum.py collect --bundle /tmp/ibm-bundle --receipt /tmp/ibm-receipt --output /tmp/ibm-observed
```

Select a layout from the actual native coupling map; `0,1` above is a placeholder,
not a claim that every backend supports it. Review `request.json`, physical QASM
and manifest before invoking submit. The committed `example-bell-xx/` bundle is
synthetic and cannot be submitted. It provides a concrete offline review example.

## Comparison meaning

Outcome integer = `trace_bits | (terminal_bits << number_of_trace_bits)`, with
logical qubit j at terminal bit j. Shot ordering is preserved across registers;
comparing only separate marginal histograms could miss incorrect feed-forward.
Report total variation distance, maximum bin deviation and a simultaneous
Hoeffding bound with alpha=0.01 over all possible joint bins. Its IID ideal-shot
assumption is explicit. A noisy device may disagree because of physical errors,
calibration drift or the projection; this statistic alone cannot identify the
cause. Reports say `compared`, not proved equivalent. No noise fitting,
mitigation/error correction or independent hardware attestation is claimed.

## Offline reproduction and evidence

```sh
python3 tools/ibm_projection_probe.py --fslc /path/to/fslc --compiler-root /path/to/Fission
FSLC=/path/to/fslc python3 -m unittest discover -s tests -p test_ibm_quantum.py -v
```

Seven existing authored circuits × computational-basis inputs × all X/Y/Z terminal
observations × both CX/CZ bases yield **684 instrument comparisons**. A separate
qualification parser interprets physical instructions with dense matrices and
reset channels; it does not call the FIR interpreter or an IBM parser. Native
branch/reference execution and physical lowering agree within 2e-10. Another
684 comparisons exercise modeled Runtime codec frames and exact joint counts.
These are modeled frames, not captured IBM responses or an SDK roundtrip.

Mock transports cover paid/unknown plans, synthetic input, missing capabilities,
allowance, changed target, one POST, uncertain submission without retry, bound
job identity, joint results, byte/bit order and malformed codecs. SDK source is
inspected only for wire framing/cost placement; no implementation is imported or
linked. `protocol-sources.lock.json` records primary source revisions and hashes.
Original quantum experiment sources and package hashes remain frozen.

Official contracts: [REST setup](https://quantum.cloud.ibm.com/docs/en/guides/cloud-setup-rest-api),
[Jobs API](https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest/tags/jobs),
[Backends API](https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest/tags/backends),
[Instance API](https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest/tags/instances),
[dynamic-circuit restrictions](https://quantum.cloud.ibm.com/docs/en/guides/execute-dynamic-circuits),
[Global Catalog](https://cloud.ibm.com/apidocs/resource-catalog/global-catalog).
Anonymous API/catalog schema retrieval attempts returned HTTP errors in this
session; documentation and pinned SDK sources were used for the adapter contract.
Authenticated live behavior still requires qualification.

## Recorded local result

Native pin `4af9bf84b16d288798bde5794de38da8f50a061e`: full crate with x86
114 passed / 0 skipped, including four new IBM projection tests; strict
Clippy default/x86 and workspace fmt passed. Research Python 85 passed with
FSLC/FSL_X86 integration enabled (0 skips). Adapter-specific suite: 13 passed.
Clean-pin projection/oracle error: 6.661338147750939e-16. Five local reports retain
684 new instrument + 684 modeled codec comparisons and old 308/678/420/1,344
quantum regressions. Original package/source hashes are unchanged.

Pinned research job `ibm-circuit-projection` reruns this stage without legacy
assets or credentials. CI results are separate from these local observations;
no unobserved run or hardware result is certified by this record.

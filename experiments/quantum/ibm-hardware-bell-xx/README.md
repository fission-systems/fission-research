# FIR Bell circuit on IBM hardware — 2026-10-17

One real, non-dry-run SamplerV2 job completed on `ibm_marrakesh`:
`db9m2vvi0auc7390t57g`. The provider reports creation at
2026-10-17 11:52:31 UTC and completion at 11:52:39 UTC. There was one job
submission POST, one PUB, 1,024 shots and a requested maximum execution time of
60 seconds. Reported QPU charge time was **2 seconds**; the instance usage
changed from 0/600 to 2/600 seconds. No paid plan, session, mitigation, twirling,
dynamical decoupling or transpiler was used.

## What ran

```text
ideal-circuits/circuits.fsl: bell_coherent
  -> owned FSL compiler / canonical FIR package
  -> owned physical OpenQASM 3 emitter
  -> official Qiskit OpenQASM parser
  -> official SamplerV2 SDK / QPY wire serialization
  -> IBM physical backend
  -> archived shot data / owned decoder / FIR comparison
```

Native pin: `4af9bf84b16d288798bde5794de38da8f50a061e`.
The two logical qubits start in `|00>`; FIR applies H(0), CX(0,1), and the
observation wrapper measures both in X. The selected physical qubits are
**135, 139**. RZ/SX/X and CZ support and the coupling were explicitly present
in live configuration. At selection, this device had zero pending jobs; the
pair had the lowest reported CZ error on that device (0.0012256471673037783).
This selection is not an estimate of full-circuit fidelity.

The native emitter decomposed H/CX into the device basis. Qiskit parsed its
physical `$135`/`$139` addresses without transpilation or gate rewriting. The
imported circuit has 140 indexed qubits, with operations on only those two;
the device has 156 qubits. The `out` register has two classical bits. Qiskit
2.6.0 and qiskit-ibm-runtime 0.50.0 were installed in a separate Python 3.12.1
environment. Fission core dependencies were unchanged.

## Observation

Bitstrings below use the `out[1] out[0]` display order.

| Outcome | Ideal probability | Observed shots | Observed fraction |
|---|---:|---:|---:|
| `00` | 0.5 | 541 | 0.5283203125 |
| `01` | 0 | 3 | 0.0029296875 |
| `10` | 0 | 35 | 0.0341796875 |
| `11` | 0.5 | 445 | 0.4345703125 |

Total variation distance: **0.0654296875**. Maximum bin deviation is
0.06542968749999989, above the existing simultaneous Hoeffding bound
0.05713116986506013 at alpha=0.01. Consequently
**`ideal_sampling_compatible: false`** is preserved in the report. The owned
result decoder and the official SDK decoder returned exactly the same counts.

This completes one physical execution path and statistical comparison. It does
not establish ideal execution equivalence, identify the cause of the observed
deviation, certify entanglement or perform tomography. Device errors, drift and
projection errors have not been separated. A single XX histogram is insufficient
to distinguish all relevant quantum states. No current-device noise fitting,
error correction, actual QPU binary lifting, general quantum CFG or whole-program
support is claimed.

## Retained evidence and privacy boundary

- `source.fslc`, `circuit.qasm`, `reference.json`, `expected.json`: owned artifacts.
- `native-bundle-manifest.json`: original bundle hash bound by the receipt.
  Its full account-bearing snapshot and modeled QASM request stay local; the
  actual transmitted SDK request is retained separately below.
- `sdk-import.json`: parser operation indices and physical-qubit mapping.
- `sdk-request.json`: the actual SDK request parsed and serialized as JSON.
  This uses QPY transport. The earlier stdlib adapter's modeled QASM request
  envelope was not used for this job.
- `result-raw.json`: exact result response text; compressed shot order retained.
- `job.json`, `metrics.json`, `receipt.json`, `submission-http.json`: provider
  completion, usage and one-POST evidence. Only `user_id` is removed from the
  published job response; its original hash is retained in provider selection.
- `provider-selection.json`: selected plan, configuration and calibration fields.
  Account CRN and unrelated device data are omitted. Full raw preflight snapshots
  remain in ignored local artifacts; the published selection is not submittable.
- `capture.lock.json`: source, compiler and evidence hashes. The wire-body hash
  in the receipt refers to the original transmitted bytes; the capture file hash
  refers to the parsed/pretty-printed `sdk-request.json`. These are distinct.

API keys, bearer tokens and saved account configuration are excluded. This is
provider-reported execution evidence, not independent hardware attestation.
The provider did not report a calibration ID in the retained job response.
The preflight timestamp is not proof of the calibration used by the job.

## Offline replay — no credentials, network or additional QPU usage

```sh
python3 tools/ibm_hardware_replay.py --fslc /path/to/fslc --report artifacts/ibm-hardware-replay.json
```

At the pinned compiler this regenerated the source package and physical QASM
byte-for-byte, reproduced the ideal FIR probabilities, decoded the captured
1,024 shots and reproduced the comparison, including its failed ideal-model
compatibility condition. Omitting `--fslc` only checks the capture and comparison.
A passing replay means capture consistency; it does not turn the hardware
comparison into an equivalence result. CI repeats this replay offline.

In the optional SDK environment, `--sdk-wire` also decoded the actual submitted
QPY and compared every operation, parameter, physical index, classical output
index and global phase with the native QASM parsed locally. They matched.
This check uses the official parser/decoder and is separate from the earlier
independent dense-matrix qualification. It makes no network request:

```sh
/path/to/sdk-venv/bin/python tools/ibm_hardware_replay.py --fslc /path/to/fslc --sdk-wire
```

## Recorded submission method

The separate SDK client used explicit `channel="ibm_quantum_platform"`, API key
and CRN, with no `name=` or account saving. It verified free Open Plan status,
remaining allowance, operational device and unchanged target immediately before
submission. An exclusive receipt directory was created before the POST. The SDK
transport's submission retries were disabled, and a request observer refused a
second job POST. An uncertain submission outcome would have required inspecting
the workload list instead of retrying.

The request used `SamplerV2(mode=backend, options=...)` with
`max_execution_time=60`, classified measurements, all three optional processing
features above disabled, and `.run([parsed_native_qasm], shots=1024, dry_run=False)`.
`sdk-request.json` records the serialized request. The environment lock describes
the local SDK dependencies; it is not a Fission runtime requirement.

The preceding urllib connection attempts received authenticated Cloudflare 1010
JSON responses. The official SDK subsequently succeeded after IAM changes.
Both access configuration and transport changed; this observation does not
isolate the reason for the earlier failures. JSON versus HTML is not a reliable
test for distinguishing IBM authorization errors from Cloudflare blocks.

Official contracts: [SDK account selection](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/qiskit-runtime-service),
[SamplerV2](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/sampler-v2),
[Sampler options](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-sampler-options).

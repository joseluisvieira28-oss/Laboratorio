# DLS_ALTERNATIVE_SOURCE_EQUIVALENCE_RECEIPT_V0.1

Date: 2026-09-30
Branch: dls-field-enrichment-v01
Terminal classification: **ALTERNATIVE_SOURCE_EQUIVALENCE_BLOCKED**
Reason: **ARCHIVAL_RPC_CREDENTIAL_DEPENDENCY**
Science: unchanged. This is not NO_EDGE and is not a tested hypothesis rejection.

## Problem → diagnosis → execution evidence
Route A SQD transport failures are the operator-reported mission premise; no blind SQD rerun was launched in this session.
Inspected branch tree at commit 0587b69c6e78de6acc90af2b66c5d0ce5fe1da8c and all ten mandatory source documents/collector.
Read additional RAW receipt, sample audit, Protected-2025 source authority, Kamino layout and Save11 payload/unit/CPI freezes and current 64-row raw reconciliation.
No protected economic outcome files were opened.

Both local execution variables were absent. A fresh GitHub Actions check then independently tested only empty/nonempty presence under ARCHIVAL_RPC_CREDENTIAL_READINESS_PREFLIGHT_V0.1 semantics:
- workflow: .github/workflows/dls-route-a2-readiness-v01.yml
- implementation commit: cf944139810ba5b5f065ad506da2227ffcaab262
- run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/36779396166
- job: 110105366916
- artifact: 11126673220 / dls-route-a2-readiness-v01
- artifact ZIP SHA256: 6433670353ea3f8233a8e3033d13dc83b0bf16fd456f8151fd08f87a4b379fc2
- artifact member: DLS_ROUTE_A2_CREDENTIAL_READINESS_RECEIPT_V0.1.json
- artifact was downloaded, its ZIP digest independently verified, and its receipt JSON parsed.
- actual receipt classification: ARCHIVAL_RPC_CREDENTIAL_ABSENT
- helius_api_key_present: false
- dls_rpc_url_present: false
- rpc_request_made: false
- secret_values_exposed: false

The workflow success means only that the zero-RPC preflight completed. The absent classification, not the Actions colour, determines this verdict.
This statement is scoped to repository secrets exposed to this job; it does not assert no credential exists on the operator PC or in another environment.

## Source audit findings
The retained 23-signature receipt proves prior BigQuery/Helius status and payload reconciliation, not SQD/RPC census completeness or exact instructionAddress equivalence.
The original ZIP byte-level authority is named and hash-pinned in RAW_RPC_VALIDATION_RECEIPT_V0.1.md:
DLS_RAW_SAMPLE_VERIFY_20260916_221907.zip
SHA256 5e14c1712a97d60983b7321735615681671b76dcb1bce5f973dfdb28f3cfab7f
It is not present as a tracked ZIP in the inspected branch tree. Its original bytes were not retrieved/re-audited in this session. No replacement fixtures were created. Locating the retained original archive is a prerequisite to empirical gate execution.
The 23-signature fixture lacks Kamino and Save0c; it cannot alone validate all four classes.
Current Kamino/Save11 64-row receipt is retained source evidence but records outer/inner class matches, not complete reconstructed CPI paths.

Canonical collector Kamino prefix: b1479abce2854a37.
Older feasibility document prefix: b1479acce2854a37.
Use canonical collector/freeze only; no decoder was changed.

## Equivalence contract and execution status
Contract: DLS_ALTERNATIVE_SOURCE_EQUIVALENCE_GATE_V0.1.md
Contract commit: 95f0516744e388865406d512e3355cbcc8281383

| Test | Status | Evidence limitation |
|---|---|---|
| 1 Transaction census | NOT_RUN / BLOCKED | No archival execution credential; complete paired fixture census unavailable |
| 2 RAW transaction fidelity | NOT_RUN / BLOCKED | Prior receipt preserved; original 23 RAW bytes not retrieved here |
| 3 Versioned transactions / ALT | NOT_RUN / BLOCKED | No new empirical paired comparison |
| 4 CPI tree / instructionAddress | NOT_RUN / BLOCKED | Exact empirical SQD/RPC tree equivalence not established |
| 5 Discriminator / account roles | NOT_RUN / BLOCKED | Frozen rules inspected; no new paired adapter execution |
| 6 Save11 token balances | NOT_RUN / BLOCKED | Frozen primary/optional semantics preserved; no new paired comparison |

expected/observed/intersection/missing/extra/duplicates for a new complete paired census: not measured (null), never zero by assumption.
pagination termination evidence: unavailable.
Adapter implementation and Protected-2025 acquisition were not launched, as the mission explicitly requires correct credential-dependency closeout when the runtime lacks credentials.

## Resume requirements
Expose one existing/free archival credential as HELIUS_API_KEY or DLS_RPC_URL in the source-only execution runtime; never paste it into repository files or receipts.
Rerun zero-RPC preflight; PRESENT only permits source testing, not equivalence PASS.
Retrieve the original hash-pinned RAW archive and existing frozen SQD fixtures, record provenance and coverage before implementing/testing the adapter.
If evidence does not cover all four classes or reconstruct exact CPI identity, remain equivalence BLOCKED. Do not select fixtures after outcomes.
Only after all six gate tests pass may Route A2 acquisition proceed.

## Firewall / final classification
No source RPC calls, SQD reruns, Protected-2025 acquisition, prices/returns/PnL/funding/direction, 2026 outcomes, purchases, science changes, holdout launch, launch-marker mutation, main merge, trading, orders, wallets or exchange mutation.
Route A: scientifically preserved, transport blocked per mission.
Route A2: ALTERNATIVE_SOURCE_EQUIVALENCE_BLOCKED / ARCHIVAL_RPC_CREDENTIAL_DEPENDENCY.
Protected-2025 source authority: no new PASS established.
Scientific hypothesis: not tested by this source-equivalence mission.

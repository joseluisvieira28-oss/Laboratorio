# Radar V0.14.3.2 — live-state reconciliation and hardening

Date: 2026-09-22

## Verdict

The V0.14.3.1 `AUTHENTICATED_PREFLIGHT_PENDING` string is the immutable registry 3.6 deployment baseline. It is not the current authenticated MEXC runtime state. The runtime already consumes sanitized local receipts, but the Control Room displayed the baseline under the ambiguous label `DEPLOYMENT` and did not surface the separated runtime states prominently.

V0.14.3.2 preserves that historical registry value and labels it `DEPLOYMENT BASELINE (HISTORICAL)`. It separately exposes MEXC auth, receipt age/provenance, account risk, candidate capital feasibility, standing route authority, signal state, readiness blockers and micro-live readiness.

## Bugs fixed

| Severity | Finding | Correction |
|---|---|---|
| HIGH | Registry/UI metadata `micro_live_allowed_now=true` could make a card `ARMED` without canonical signal/execution-gate evidence. | Registry metadata can no longer produce `ARMED`. |
| HIGH | CED1D could display `FISHING` from registry `shadow_allowed` even when its external sentinel had no healthy runtime evidence. | CED1D now requires a live sentinel `OK`; absent/unhealthy evidence is blocked. |
| MEDIUM | The historical ETF deployment baseline appeared as current runtime status. | Preserved history, relabelled it, and displayed live execution states separately. |
| MEDIUM | A forward motor could appear healthy without a completed candidate component state. | `FISHING` now requires supervisor health plus completed candidate-specific component evidence. |
| MEDIUM | Future, stale and invalid receipt timestamps collapsed into a generic freshness result. | Explicit fail-closed timestamp reasons were added. |
| MEDIUM | `/api/state` did not make account identity/open position/open order observations explicit. | Added sanitized account fields when supplied by the receipt, plus provenance and age already retained. |
| HIGH (operational) | The onefile executable extracts dependencies dynamically; the observed Windows Code Integrity 3077/3033 policy blocks files that do not satisfy policy. Automatic restart is therefore not proven reliable. | CI now produces a stable `onedir` layout and a hash manifest. This avoids transient onefile extraction paths, but it does not bypass App Control. The installed directory/binaries must still be authorized by the operator's enforced policy or signed by an accepted publisher. |

## Seven-motor truth contract

- ETF, BNB, Options, TFG and EMA6H require a running local forward supervisor, non-fatal shared evidence chain, no candidate error, and a completed candidate component state.
- DH03 requires `COLLECTING`; missing/bootstrap state remains gated and `FAIL_CLOSED` remains blocked.
- CED1D requires the external sentinel to report `OK`; registry state alone is insufficient.
- Tier 3 remains shadow-only.
- Global standing authority does not activate candidate-specific authority.

The operator-reported V0.14.3.1 state (7 FISHING, Options healthy) cannot be independently certified from repository data alone. V0.14.3.2 must be deployed and its live `/api/state` captured after one complete healthy cycle. This is a remaining evidence step, not a scientific failure.

## MEXC state contract

- Authenticated exchange preflight: fresh sanitized receipt only.
- Risk firewall: independent fresh receipt only.
- Standing authority: packaged resource, explicit authority ID and route scope.
- ETF capital: independent candidate state; exchange PASS never overrides venue-minimum incompatibility.
- Current frozen ETF calculation remains blocked: 112.3763 USDT equity × 0.1% = 0.1123763 USDT, below the previously observed 8.66158 USDT venue minimum.
- Signal and candidate-specific immutable authority remain absent; micro-live readiness remains fail-closed.

## Windows App Control verdict

Events 3077 and 3033 are enforcement/block evidence, not ordinary application crashes. V0.14.3.2 does not disable or weaken Windows security. The onedir package is easier to inspect, hash, sign and explicitly authorize, but reliable restart remains blocked until the exact packaged binaries are accepted by the active App Control policy. The operator/IT administrator must use an approved signer, managed installer, or narrowly scoped allow rule appropriate to that policy.

## Validation

- Focused local tests: 45/45 PASS.
- Full local suite: 242/242 PASS.
- Real exchange mutation/order submission: none.
- Science, thresholds, direction, risk and promotion: unchanged.
- Main merge: no.

CI/artifact identifiers are recorded in the repository receipt after the Windows workflow completes.

## Operator deployment

1. Download the V0.14.3.2 artifact; do not reuse the V0.14.3.1 executable.
2. Extract the complete `CryptoEdgeRadarNode` directory to a stable administrator-controlled location. Do not move only the EXE.
3. Have the exact directory/binaries authorized under the active App Control policy, or signed by a publisher already trusted by that policy. Do not disable Smart App Control/App Control.
4. Run `windows/IMPORT_MEXC_RECEIPTS_V0143.ps1 -SourceRoot <sanitized-receipt-folder>` immediately after generating fresh receipts.
5. Run `windows/INSTALL_RADAR_AUTOSTART_V0143.ps1`, then start `windows/RUN_RADAR_24X7_V0143.ps1`.
6. Open `http://127.0.0.1:8787/api/state`; verify build ID, registry 3.6, 7/7 focus motors, receipt ages/hashes, separate MEXC/risk/capital/authority states and zero `ARMED` unless genuine immutable execution evidence exists.
7. Reboot once and verify watchdog restart plus fresh Code Integrity logs. If 3077/3033 names a Radar binary or dependency, stop and authorize/sign that exact artifact; do not weaken the policy.

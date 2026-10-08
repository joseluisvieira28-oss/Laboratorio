# MEXC Triple Fishing Operator V0.3 — Windows handoff

Status: build/deployment package only. Installing the package starts the supervisor **UNARMED**, but an unarmed supervisor might still manage an existing position. It does not authorize a real-money entry. **Do not run Install/Run/Switch/Ready-And-Arm as a diagnostic.** First prove the actual MEXC account position/order/TP-SL state independently, read-only, and reconcile local slots and receipts.

## Lanes

- BNB-LAUNCHPOOL-DEMAND-001 — operator real-money fork, no scientific credit.
- OPTIONS-SPOTPERP-001-V2.1 — 5x Futures operator fork, parent signal/risk weight preserved, no scientific credit.
- HTF-DH03-12H-STANDALONE-FORWARD-V1 — prospective operator fork with Binance receipt-time gate and MEXC exchange-hosted TP/SL, no scientific credit.

All three lanes share one account-wide persistent slot. Maximum simultaneous Futures positions: 1.

## Frozen operator envelope

- initial isolated margin: max 10 USDT per position
- leverage: exactly 5x
- maximum notional: 50 USDT per position
- margin mode: ISOLATED
- Auto Add Margin: OFF
- daily realized-loss kill: 5 USDT
- rolling 7-day realized-loss kill: 5 USDT
- no martingale, averaging, pyramiding, late chase or blind resend

The loss kill blocks new entries after realized losses. It is not a stop-loss on an already-open BNB/OPTIONS position. DH03 separately requires exchange-hosted protective TP/SL.

## Install / handover sequence

1. Verify SHA256SUMS.txt against the EXEs in this bundle.
2. Open PowerShell as Administrator.
3. Install the V0.3 supervisor **UNARMED**:
   `Install_MEXC_Triple_Fishing_V03.ps1`
4. Check:
   `Status_MEXC_Triple_Fishing_V03.ps1`
5. Do not manually create an ARMED marker.
6. Only after the supervisor is healthy and the account is clean, run:
   `Switch_From_BNB_To_Triple_V03.ps1`

The switch first disarms the legacy BNB and legacy OPTIONS entry markers, then performs authenticated read-only readiness. It arms V0.3 only if all gates pass. Legacy supervisors are disabled only after V0.3 readiness succeeds.

If readiness fails, do not bypass the blocker and do not rearm multiple executors simultaneously.

## Historical OPTIONS accounting

The installer copies the legacy OPTIONS receipt tree into an immutable local archive once, then builds a local correction overlay. The overlay binds each of the four known corrections to:

- immutable signal identity;
- entry and exit order identities;
- SHA256 of the original local reconciliation receipt.

Original receipts are not rewritten. An invalid or ambiguous overlay fails closed.

## Controls

- `Status_MEXC_Triple_Fishing_V03.ps1` — local runtime/control status.
- `Disarm_MEXC_Triple_Fishing_V03.ps1` — prevents new V0.3 entries; supervisor remains running.
- `Emergency_Stop_MEXC_Triple_Fishing_V03.ps1` — disarms new entries and sets the kill switch. Do not stop the supervisor while a position may be open.

## Safety

Never stop or replace a supervisor that may still own an open position until the account and local reconciliation prove that the position is closed. Never delete a global-slot reservation merely to make readiness pass. Unknown order acknowledgement, missing protection, receipt corruption, stale source heartbeat or accounting ambiguity remain fail-closed.

## 2026-10-08 launcher-recovery diagnostics

This release adds **only operational observability**, not a new signal, risk or trading authority:

- `Run_MEXC_Triple_Fishing_V03.ps1` writes structured, append-only local diagnostic events to `%LOCALAPPDATA%\\CryptoLab\\TripleFishingV03\\live_state\\launcher_events_v03.jsonl`. Records contain a run GUID, UTC timestamp, a fixed launcher stage, numeric exit classification and marker-existence flags. **Never** raw exception messages, credentials, stdout/stderr, secrets, private account responses or environment dumps.
- Main supervisor fatal Python exceptions write a separate, sanitized `triple_fishing_operator_v03.json.fatal.json` with phase and Python exception type only. Existing heartbeat/state, global slot, order receipts and history are not deleted or overwritten by this diagnostic.
- `Inspect_MEXC_Triple_Fishing_V03_READONLY.ps1` reads Windows task status, supervisor heartbeat, launcher and fatal stages, and marker presence. It performs **no authenticated reads, private API calls, order creation, arming, process launch or task mutation**. Account positions/orders remain `NOT_CHECKED`.
- Failure codes: 11 missing launcher input; 12 input validation exception; 21 overlay returned nonzero; 22 overlay output missing; 23 overlay invocation exception; 31 DPAPI missing/invalid/identity failure; 41 main child nonzero (actual child exit is in diagnostic JSONL); 42 main unexpectedly exited 0; 43 main invocation exception; 90 runtime/log write error; 61 supervisor fatal Python exception recorded by child. This classification only applies to the **new package**, not the Oct 2 legacy code 1.
- Offline Windows release tests use isolated temp `LOCALAPPDATA`, inert synthetic executables, and synthetic DPAPI values. They test fail-closed paths and slot/marker preservation, **without exchange access or live credentials**.

### For the operator: safe, staged recovery

**Stage A — no execution:** download the specific successful CI build artifact from this branch into a **new empty folder**, verify *all* files against its SHA256SUMS and BUILD_INFO source SHA. Do not copy individual newer executables over a prior HOTFIX folder; mixed packages were discovered. Preserve all historical receipt/state folders untouched. Run `Inspect_MEXC_Triple_Fishing_V03_READONLY.ps1` if it can be located in the new verified bundle; it reads the existing local runtime and does not execute the supervisor.

**Stage B — independent account reconciliation:** verify open Futures positions, all open orders (including position TP/SL), account mode, fills, current account fee tier and effective realized-loss usage using authorized **read-only** MEXC account inspection and local immutable receipts under the *exact* Windows Scheduled Task user. Do not display DPAPI values, credentials or unredacted account/transaction records. Do not infer account vacancy from `GLOBAL_POSITION_SLOT_V03.json` absence. Do not stop a supervisor that may own an open position.

**Stage C — controlled installation only after B is independently PASS:** existing installer `Install_MEXC_Triple_Fishing_V03.ps1` registers a logon-only scheduled task and **starts a supervisor even when unarmed**. Consequently, this stage requires a separately authorized maintenance window and clean account reconciliation; it is *not* part of Stage A. Keep unarmed, watch sanitized heartbeat/source states and task exit evidence. Do not run the auto-arm switch before explicit separate trading authorization. A scheduled task in `Ready` is not a running supervisor, and the existing finite retry policy is NOT continuous recovery.

**Watchdog policy:** monitor-only alerting for stale heartbeat and stopped process; do **not** introduce automatic restart or re-arming without proof of account ownership and safe restart/reconciliation. Never delete a slot, receipt, ARMED/kill marker or historical state to make readiness pass. Keep original freezes and fee accounting unchanged.

**Unresolved:** the historical `LastTaskResult=1` happened before this diagnostic existed; cause remains unproven. This patch classifies *future* failures, not old ones. Scientific/micro-live efficacy is not asserted by passing these packaging tests.

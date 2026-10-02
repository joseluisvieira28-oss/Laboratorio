# MEXC Triple Fishing Operator V0.3 — Windows handoff

Status: build/deployment package only. Installing the package starts the supervisor **UNARMED**. It does not authorize a real-money entry.

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


## Meta-Layer V1 shadow recorder

The Meta T0 recorder is observational and **OFF by default**. Normal installation and scheduled-task startup do not enable it.

For a controlled shadow session, the Windows runner accepts `-EnableMetaT0Shadow`. This only adds the local evidence path `data\radar_meta_t0_v1.sqlite3` to the supervisor. The recorder has no credentials, engine, slot, sizing, arbitration, order or exchange-mutation authority.

A recorder exception is contained and reported as `RECORDER_FAIL_CLOSED_PARENT_UNCHANGED`; it must not block, create or modify the parent operational decision. T0 evidence is append-once and retry/restart idempotent.

Enabling this recorder is not a scientific promotion and does not claim Meta-Layer edge. It starts prospective evidence collection only.

# MEXC Triple Fishing V0.4 — Pre-Live Windows Bundle

This bundle is the pre-live package for the frozen three-slot small-fish architecture.

## Frozen execution envelope

- maximum simultaneous positions: 3
- one active position per symbol
- aggregate max notional: 30 USDT
- aggregate max initial isolated margin: 14 USDT
- daily / rolling-7d realized-loss kill: 5 USDT / 5 USDT
- OPTIONS: BTC_USDT, 1x, max 10 USDT notional, one position
- BNB: BNB_USDT, 5x, max 10 USDT notional, one position
- DH03: frozen six-symbol universe, 5x, max 10 USDT notional per position, global three-slot cap
- no late chase
- no blind resend
- isolated only
- Auto Margin Add disabled

If the venue minimum exceeds the 10 USDT lane cap, the signal is blocked. The operator never increases size merely to satisfy the venue minimum.

## Important: this bundle is NOT live-authorized

It contains the executor binary so the exact production entrypoint can be built and smoke-tested, but it intentionally does not contain:

- an ACTIVE V0.4 authority;
- an armed marker;
- any command that automatically arms the executor;
- any automatic replacement of V0.3.

Without those files the executor fails closed before order submission.

## Next operator step

Run:

`Ready_Check_MEXC_Triple_Fishing_V04.ps1`

The Ready Check uses the existing local DPAPI MEXC credentials only for authenticated GET/read-only requests. It does not create, cancel or modify orders and does not alter the exchange account.

Send the resulting `triple_ready_v04.json` / terminal output back for the controlled handover decision.

Do not manually disarm an old executor while it owns an open position. The Ready Check intentionally fails if the account/handover state is not clean.

## Other files

- `Run_MEXC_Triple_Fishing_V04.ps1` — guarded runtime entrypoint. It refuses to run without a separately issued ACTIVE authority, PASS readiness receipt and armed marker.
- `Status_MEXC_Triple_Fishing_V04.ps1` — local state display.
- `Arm_After_Approved_Handover_MEXC_Triple_Fishing_V04.ps1` — creates the armed marker only after a separately issued ACTIVE authority is present and hash-bound to a fresh (<15 min) PASS readiness receipt. The current pre-live bundle contains no ACTIVE authority, so this script cannot arm by itself.
- `OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_DRAFT.json` — draft only, cannot authorize orders.
- `GLOBAL_FISHING_MANIFEST_V04_DRAFT.json` — reconciled three-lane draft manifest.

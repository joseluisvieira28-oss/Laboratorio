# CED1D-0031 MICRO-LIVE V0.2 — SMALL REVIEW CLOSEOUT — 2026-09-18

## Verdict

V0.2 is the deployment-candidate line. V0.1 is preserved but superseded for deployment.

Branch: `crypto-edge-radar-microlive-executor-v0.2-2026-09-18`
Base: `crypto-edge-radar-ops-hardening-v0.9`
Micro-live scientific authority: `b0cea0fb9c47a3178599e93bde70c5e5a0207cc9`

## Important issue found and corrected

The original executor preparation used the older Radar V0.3 development line with local JSONL/SQLite coordination. The current operational Radar is on the V0.9 family with PostgreSQL append-only evidence. That mismatch was material for unattended execution.

V0.2 was rebuilt from the V0.9 ops-hardening line and now uses the current `build_evidence_store` abstraction, so prospective signal, preflight, entry, exit, incident and reconciliation evidence can share the durable PostgreSQL hash chain.

## Reviewed controls

- exact CED1D-0031 / AVAXUSDT / Binance USD-M binding
- 20-calendar-day continuation signal and H1 timing preserved
- first real reference entry remains 2026-09-21T00:01:00Z
- no late-entry rescue/backfill
- one-event-only V0.1 authority preserved
- 25 USDT hard cap with 24 USDT sizing target
- isolated margin and exactly 1x required
- one-way mode required; Hedge Mode fails closed
- account canTrade check
- taker commission <=5 bps/fill
- no pre-existing AVAXUSDT position/open order
- deterministic client-order IDs
- query-before-retry/idempotent recovery after ambiguous submit result
- pre-entry authenticated prepare during 00:00–00:01 UTC
- quick position/order guard at the exact entry window
- actual position quantity used for reduce-only exit
- late exit closes risk and records an incident
- account-trade history must contain expected order IDs before reconciliation is sealed
- commissions are reconciled by asset; exact USDT net is not fabricated if commission asset differs
- second real event remains unauthorized after reconciliation
- evidence-chain verification at startup and periodically thereafter
- adaptive runtime cadence near entry/exit instead of continuous high-rate logging

## Remaining gates before real-money arming

1. Select/confirm the actual deployment workspace/service.
2. Install Binance API key/secret in the runtime secret store only.
3. Run `python -m radar.ced1d0031_preflight` and require PASS.
4. Confirm AVAXUSDT one-way / isolated / 1x / fee <=5 bps / no conflicting position or order.
5. Deploy V0.2 worker with the same durable `RADAR_DATABASE_URL` evidence backend.
6. Verify process restart recovery while real execution remains disabled.
7. Only then set the explicit micro-live arm variables.

## Validation status

An offline CI workflow and focused unit tests are committed. No successful GitHub Actions execution has been observed for the tool-created V0.2 commits yet, so this closeout does not claim CI PASS.

## MEXC

MEXC is not an AVAX20 fallback venue. CED1D-0031 remains Binance USD-M provider-bound. MEXC authenticated trading stays a separate future integration.

## Governance

No credentials committed. No authenticated exchange call made. No order submitted. No exchange mutation. No main merge.
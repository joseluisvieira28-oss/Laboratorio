# CED1D-0031 MICRO-LIVE EXECUTOR V0.2 — REVIEW / RUNTIME ALIGNMENT

Date: 2026-09-18

Status: PREPARED / FAIL-CLOSED / NOT DEPLOYED / NOT ARMED

## Why V0.2 exists

A review found that the first executor preparation branch was based on the older Radar V0.3 development line, while the current always-on operational Radar has moved to the V0.9 family with a durable PostgreSQL evidence backend.

For unattended real-money research, local JSONL/SQLite coordination is not sufficient as the primary state authority on a cloud runtime. V0.2 is therefore based directly on crypto-edge-radar-ops-hardening-v0.9 and uses the existing build_evidence_store(...) abstraction so signal, entry, exit, incident and reconciliation records can live in the same durable PostgreSQL evidence chain.

The older V0.1 executor branch is preserved as historical preparation but is superseded for deployment by V0.2.

## V0.2 architecture

One dedicated process: python -m radar.ced1d0031_microlive

It performs exact public Binance USD-M AVAX daily signal observation; append-once prospective shadow signal receipt; optional authenticated entry only when the separate micro-live runtime arm is present; deterministic client-order-ID recovery after network/process ambiguity; one-event hard cap; reduce-only H1 exit; automatic user-trade/funding reconciliation; append-only incident and reconciliation evidence; and evidence-chain verification.

## Frozen scientific identity

- CED1D-0031 only
- AVAXUSDT Binance USD-M perpetual
- 20 calendar-day momentum
- CONTINUATION
- H1
- completed daily bars only
- prospective shadow completion boundary 2026-09-19T00:00:00Z
- first real-money reference entry 2026-09-21T00:01:00Z
- no late entry/backfill
- no asset/venue/horizon substitution

## Micro-live envelope

- 25 USDT hard maximum notional
- 24 USDT sizing target to leave a small market-movement buffer under the hard cap
- one real event maximum before mandatory review
- isolated margin
- exactly 1x leverage
- one-way position mode
- taker commission <=5 bps/fill
- no existing AVAXUSDT position/order
- MARKET entry
- reduce-only MARKET exit
- deterministic client IDs
- query-before-retry
- no pyramiding / averaging / martingale / scaling

## Safety improvements found during review

Binance documents that a timeout/server error can leave execution status unknown. V0.2 therefore never blindly resubmits an ambiguous order. It first queries the deterministic client-order ID and recovers the accepted order if present.

The review also confirmed that reduceOnly is incompatible with Hedge Mode. V0.2 blocks Hedge Mode before entry and requires one-way mode.

## Credential preflight

After Binance secrets are installed in the runtime secret store, run: python -m radar.ced1d0031_preflight

This performs signed account checks and Binance's test-order endpoint only. It does not submit a real order.

## Runtime secrets

Required later: BINANCE_API_KEY, BINANCE_API_SECRET, RADAR_DATABASE_URL.

Real-money arming additionally requires MICROLIVE_EXECUTION_ENABLED=1, MICROLIVE_ARM_TOKEN=CED1D-0031-MICROLIVE-V0.1-ONE-EVENT, MICROLIVE_VENUE=binance_usdm.

## MEXC

MEXC remains separate. CED1D-0031 is Binance USD-M provider-bound and V0.2 does not permit MEXC fallback execution.

## Deployment boundary

No deployment, secret insertion, authenticated preflight or real order is performed by this review commit.
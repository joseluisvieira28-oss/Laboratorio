# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — CANONICAL 30M DISCOVERY IMPLEMENTATION PREFLIGHT FREEZE V0.1

Date: 2026-09-28
Status: OUTCOME-BLIND IMPLEMENTATION PREFLIGHT / PROTECTED 2025 OUTCOMES LOCKED

Canonical economic authority:
- file: pressure_mining_v0_1/labs/COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md
- commit: 2191bbf741ced5f801d8ae4034bd126c3b91cbc8
- Git blob SHA: d36c24bffd8a0f16787e0b7cf72b2d7b60e2f430

The later 5-minute draft is non-canonical and must never be used by this implementation.

## Allowed preflight actions

1. Verify the exact canonical freeze Git blob identity.
2. Verify public Binance Vision object existence for 2025 monthly 1m archives:
   BTCUSDT, ETHUSDT, LINKUSDT, UNIUSDT, COMPUSDT; January through December 2025.
3. Verify matching .CHECKSUM objects exist and contain a syntactically valid SHA-256 token.
4. Do NOT download or parse kline ZIP content during preflight.
5. Execute synthetic-only tests for:
   - same-tx+asset aggregation;
   - deterministic 30-minute same-asset overlap suppression;
   - first complete 1-minute bar strictly after an Ethereum block timestamp;
   - exact +30 bar exit boundary;
   - relative log-return sign;
   - BASE20 and STRESS30 net transformation;
   - no-rescue and asset-universe constants.
6. Verify that the protected Discovery runner refuses to run unless a separate explicit authorization marker exists.

## PASS

PREOUTCOME_PREFLIGHT_PASS requires:
- canonical blob identity exact;
- 60/60 ZIP objects available;
- 60/60 CHECKSUM objects available;
- 60/60 checksum tokens syntactically valid;
- all synthetic tests PASS;
- protected outcome runner lock PASS;
- no market price row opened.

This preflight does not authorize protected Discovery.

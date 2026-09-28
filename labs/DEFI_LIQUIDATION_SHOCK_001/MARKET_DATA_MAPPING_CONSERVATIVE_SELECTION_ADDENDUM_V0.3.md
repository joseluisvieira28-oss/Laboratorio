# DEFI-LIQUIDATION-SHOCK-001 — MARKET DATA MAPPING CONSERVATIVE SELECTION ADDENDUM V0.3

Date: 2026-09-28
Status: FROZEN / SOURCE-ONLY / OUTCOME-BLIND

## Decision

Before any candle payload, price, return, PnL, direction or economic outcome is opened, V0.3 freezes a conservative registry construction rule.

1. Direct-map only target `mint:So11111111111111111111111111111111111111112` to Binance Spot `SOLUSDT`.
2. Identity authority is the already-frozen native SOL <-> canonical wrapped SOL equivalence in MARKET_DATA_SOURCE_GATE_FREEZE_V0.1 plus the exact source target identity in MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS.
3. Use Binance because it is source precedence priority 1 and SOLUSDT is an exact direct SOL/stable-quote product. The metadata feasibility gate must independently require exact Binance exchangeInfo identity and archive+checksum HEAD coverage for every eligible monthly probe.
4. listing_start_utc is conservatively set to the first source-event calendar boundary for this target, 2021-12-08T00:00:00Z. This does not claim venue inception; it restricts eligibility to the experiment's observed source interval and still requires archive metadata proof.
5. Every other target is MARKET_MAPPING_UNAVAILABLE in V0.3 because no additional exact target-to-venue identity authority is being introduced before outcomes. No correlated proxy, wrapped/staked equivalence, symbol guess, or outcome-based rescue is allowed.
6. The existing frozen post-mapping sample gate remains unchanged: pooled retained Discovery >=1000 and OOS >=500. Subgroup downgrades follow MARKET_DATA_MAPPING_SAMPLE_ADEQUACY_ADDENDUM_V0.2 exactly.
7. If SOL-only retained source clusters fail the frozen sample gate or any required Binance metadata/archive HEAD probe fails, classification must be BLOCKED. No second asset may be added to rescue the gate without a new source-only authority while outcomes remain closed.

## Firewall

archive_payload_downloaded=false
candles_opened=false
prices_opened=false
returns_computed=false
pnl_computed=false
directional_outcomes_opened=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
merge_main=false

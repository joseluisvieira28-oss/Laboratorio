# LIQUIDATION EXHAUSTION — ECONOMIC FORWARD V1
FROZEN: 2026-11-04, prior to collecting any new economic outcomes.
Original LICP-001 PR #107 NO_EDGE intact. PR #332's 12 historical source-qualification children are explicitly excluded from all economics.

## Primary BTC hypothesis
Bybit public allLiquidation.BTCUSDT Buy means long position liquidated, potential candidate LONG reversal; Sell means short position liquidated, potential candidate SHORT. No actual orders, recommendations or automatic execution.

Trigger first as-received event when a 10s rolling window contains >=2 same-position-side positive children, no opposite-side children, summed bankruptcy p*v proxy >= USD100,000. Children must have exchange-event-to-receipt lag 0..2000ms; first trigger only per 120s cooldown. Require valid pre-trigger Bybit reconstructed BBO.

Decision is first market observation received >=5s after trigger; cancel for ANY intervening liquidation. Need causal Bybit book and trade age <=1000ms, spread <=3bps, directional mid rebound >=1.5bps from trigger, sum of top-5 bid/ask quantity >=1.15 LONG or <=1/1.15 SHORT; MEXC BTC_USDT Futures public BBO age <=1500ms, clock age 0..2000ms. Never use future data for decision.

## Primary shadow economic test
Manual delay exactly 15s from decision; primary 60s holding period from entry. Use first MEXC futures BBO received at or after each target within 1500ms: LONG buy ask/sell bid, SHORT sell bid/buy ask. If no eligible quote at entry/exit, count missing outcome. Bybit liquidation bankruptcy price is NEVER an executable quote. MEXC public orderbook snapshots are only quote proxies; do not claim fill certainty. Include spread through bid/ask, plus hypothetical 16bps roundtrip fees and 4bps extra adverse slippage. Stress fee 32bps + 8bps slippage. These are FIXED cost scenarios and NOT the user's account fee. Funding-overlap episodes excluded until timing/cost verified. Diagnostics only: delays 5/30s, horizons 30/120s, not rescue.

Source gate: Bybit snapshot+sequence continuity, timestamp validity and no reconnects, MEXC quote schema validity; on uncertainty SOURCE_BLOCKED. One 420s source run, warm-up 60s and tail 90s unavailable for triggers. No zero-imputation of absent liquidations. No economic conclusions drawn from old April PR #279 or previous 12-event 180s sample.

## Decision
Require >=60 non-overlapping primary episodes on >=14 UTC dates, >=90% valid paired MEXC entry/exit quotes, no leak and adequate pre-hoc power. Positive primary mean, median, stress mean and lower 95% **day-cluster bootstrap CI** plus execution plausibility for SURVIVES_FORWARD_CANDIDATE; otherwise NO_EDGE_AT_FROZEN_HURDLE only at adequate frozen sample. Smaller datasets UNDERPOWERED_FORWARD; invalid transport SOURCE_BLOCKED. Even candidate remains NO_LIVE_GO unless verified fees, broker-native fills, risks and separate operator authorization.

Research only: no authenticated calls, orders, wallet, funds, payments, protected old holdout, scheduler or main merge.
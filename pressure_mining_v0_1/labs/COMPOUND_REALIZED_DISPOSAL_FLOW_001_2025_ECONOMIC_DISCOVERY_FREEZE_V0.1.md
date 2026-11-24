# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — PROTECTED 2025 ECONOMIC DISCOVERY FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / READY-BUT-LOCKED / PROTECTED 2025 MARKET OUTCOMES UNOPENED

## 1. Scientific question

After a directly observed Compound III BuyCollateral disposal event in a liquid non-BTC collateral, does the collateral continue to underperform BTC over the next 30 minutes strongly enough to survive a conservative event-trading cost hurdle?

This is a **new realized-flow child**, not a rescue of COMPOUND-INVENTORY-PERSISTENCE-001.

Expected sign:
**negative collateral-vs-BTC relative return**, equivalent to positive gross PnL for a short-collateral / long-BTC relative trade.

The sign is frozen from the realized-disposal / arbitrage-routing mechanism before protected market outcomes are opened.
It is not inferred from the failed sibling's observed +24h diagnostic.

## 2. Protected evidence block

Economic test block:
2025-01-01T00:00:00Z through 2025-12-31T23:59:59Z only.

Source-only predictor census already completed:
- 1,573 BuyCollateral events;
- 1,470 unique transactions;
- 51 buyers;
- 10 collateral assets;
- 35 ISO weeks;
- top buyer share 26.5734%.

No 2025 price/return/funding/PnL outcome has been opened at freeze time.

## 3. Frozen primary asset population

Primary assets require a direct liquid Binance spot symbol and a non-degenerate BTC-relative outcome.

INCLUDED:
- WETH 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2 -> ETHUSDT
- LINK 0x514910771af9ca656af840dff83e8264ecf986ca -> LINKUSDT
- UNI 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 -> UNIUSDT
- COMP 0xc00e94cb662c3520282e6f5717214004a7f26888 -> COMPUSDT

EXCLUDED A PRIORI FROM PRIMARY:
- WBTC, cbBTC, tBTC: BTC-linked collateral makes BTC-relative outcome degenerate/redundant;
- wstETH: wrapper/staking-basis mapping is not the same instrument as ETH spot;
- deUSD and sdeUSD: no direct like-for-like liquid CEX mapping for this test;
- any later-added collateral not listed above.

No asset may be added or removed after outcomes are opened.

## 4. Frozen event construction

Start from every 2025 BuyCollateral log for the four included collateral contracts.

Within the same Ethereum transaction and collateral asset:
- aggregate all BuyCollateral logs into one event;
- sum baseAmount and collateralAmount;
- T0 is the transaction block timestamp.

Overlap rule:
- sort by mapped asset then T0;
- keep the first qualifying event;
- suppress later same-asset events whose T0 occurs before the kept event's frozen 30-minute exit time;
- resume eligibility at or after that exit time.

Cross-asset events may coexist.
Inference accounts for dependence by clustering bootstrap resamples by ISO week.

No size threshold.
No buyer threshold.
No recipient-routing threshold.
No top-event exclusion.

## 5. Frozen market source and timing

Market source:
Binance public Spot monthly/daily 1-minute kline archives for:
BTCUSDT, ETHUSDT, LINKUSDT, UNIUSDT, COMPUSDT.

For each event:
- entry bar = first complete 1-minute bar whose open timestamp is strictly greater than the Ethereum block timestamp;
- ENTRY = that bar's open;
- EXIT = open exactly 30 one-minute bars after ENTRY.

A market series with a missing required entry/exit bar makes that event invalid; no interpolation.

## 6. Frozen outcome

For each event:

ASSET_LOGRET_30M = ln(ASSET_EXIT / ASSET_ENTRY)

BTC_LOGRET_30M = ln(BTC_EXIT / BTC_ENTRY)

REL_30M_BPS = 10,000 * (ASSET_LOGRET_30M - BTC_LOGRET_30M)

GROSS_SHORT_REL_BPS = -REL_30M_BPS

Expected:
GROSS_SHORT_REL_BPS > 0.

The 30-minute horizon is frozen because the source mechanism is transaction-level realized disposal/routing and any tradable continuation should decay quickly under cross-venue arbitrage.
No 5m/15m/60m/4h/24h alternatives are permitted after outcomes.

## 7. Frozen cost hurdles

These are conservative all-in research hurdles for the two-leg relative trade; they are not a claim about exact future venue fees.

BASE:
20 bps round-trip total.

STRESS:
30 bps round-trip total.

BASE_NET_BPS = GROSS_SHORT_REL_BPS - 20
STRESS_NET_BPS = GROSS_SHORT_REL_BPS - 30

No post-outcome fee reduction or maker-fee rescue.

A later execution/capacity stage must independently verify the actual venue-specific fee/spread/slippage route.

## 8. Frozen inference

Primary independence handling:
ISO-week cluster bootstrap.

Bootstrap:
- 10,000 resamples;
- sample ISO weeks with replacement;
- retain all eligible events from each sampled week;
- seed 20260927;
- percentile 95% interval on pooled BASE_NET mean.

Report:
- N;
- unique ISO weeks;
- N by asset;
- mean/median gross and BASE/STRESS net bps;
- PF under BASE and STRESS;
- win rate;
- bootstrap 95% CI;
- per-asset means/PF;
- per-quarter means;
- leave-one-asset-out pooled means;
- largest single positive event share of total positive BASE net PnL;
- largest ISO-week share of total positive BASE net PnL.

Diagnostics do not create extra selectable hypotheses.

## 9. Frozen PASS gates

A protected Discovery PASS requires all:

SAMPLE:
1. N >= 100 after deterministic overlap suppression;
2. >= 20 unique ISO weeks;
3. all 4 frozen primary assets represented with >= 10 events each.

ECONOMICS:
4. pooled BASE_NET mean > 0;
5. pooled BASE PF > 1.0;
6. pooled STRESS_NET mean > 0;
7. pooled STRESS PF > 1.0.

STATISTICAL / BREADTH:
8. ISO-week cluster-bootstrap lower 95% bound on BASE_NET mean > 0;
9. every frozen primary asset has BASE_NET mean > 0;
10. every leave-one-asset-out pooled BASE_NET mean > 0.

CONCENTRATION:
11. largest single positive event contributes <= 25% of total positive BASE-net PnL;
12. largest ISO week contributes <= 35% of total positive BASE-net PnL.

If any gate fails:
**DISCOVERY_FAIL_NO_PROMOTION — EXACT 30M REALIZED-DISPOSAL CHILD CLOSED / NO RESCUE.**

If all gates pass:
**DISCOVERY_PASS — NOT YET TIER 2.**
A genuinely independent evidence block and execution/capacity evidence are still required under Promotion Policy V3.

## 10. No-rescue firewall

After protected outcomes open, forbidden:
- reverse direction;
- choose another horizon;
- add/remove assets;
- introduce size threshold;
- buyer/recipient subset mining;
- only-routed-event rescue;
- calendar/month/quarter rescue;
- cost reduction;
- post-hoc event clustering;
- alternate benchmark rescue;
- switch to absolute return because relative return failed.

Any materially new hypothesis requires a new LAB_ID, new pre-outcome mechanism argument and new independent evidence.

## 11. Current authority boundary

This document freezes the experiment.
It does **not** authorize opening the protected 2025 market outcomes.

At freeze time:
protected_2025_predictor_source_opened=true
protected_2025_market_outcomes_opened=false
market_prices_opened=false
returns_computed=false
pnl_computed=false
economic_discovery_executed=false
live_trading=false
orders=false
capital=false
main_merge=false

# BNB-LAUNCHPOOL-DEMAND-001 — PROMOTION POLICY V3 RE-ADJUDICATION CLOSEOUT

**Date:** 2026-09-17  
**Policy:** `ND-PROMOTION-POLICY-V3.0-FROZEN`  
**Status:** `TIER_2_PROMOTED_CANDIDATE__QUASE_DIAMANTE__HIGH_TAIL_CONCENTRATION_FRAGILITY`  
**Historical label:** `HISTORICAL VERDICT PRESERVED / RE-ADJUDICATED UNDER PROMOTION POLICY V3`

## Immutable mechanism

No trading-rule change is made by this closeout.

- official Binance Launchpool announcement with explicit BNB staking/locking/farming utility;
- LONG `BNBBTC` spot;
- entry = first 15m open strictly after canonical announcement timestamp;
- hold = 24h;
- BASE round-trip cost = 20 bps;
- STRESS round-trip cost = 30 bps;
- maximum one active trade;
- <=60 minute information clustering;
- no stop, target or leverage.

## Historical verdict preservation

The V2 state remains immutable: `TIER_3_WATCHLIST_REMAINS_HISTORICAL_RESCUE_CLOSED__FORWARD_ONLY` under the V2 policy and its per-replication concentration gate.

V3 does not rewrite that decision. It applies a new globally frozen policy prospectively to the already-opened immutable evidence.

## Existing evidence

### Pre-Discovery historical block
- N = 27
- BASE mean = +76.852622 bps/trade
- BASE PF = 1.392128
- STRESS mean = +66.8526 bps/trade
- max drawdown = 31.56%
- within-block concentration = 48.01%

### Discovery 2022–2024
- N = 31
- BASE mean = +88.866453 bps/trade
- BASE PF = 2.210397
- STRESS mean = +78.8665 bps/trade

### Independent 2025 OOS
- N = 8
- BASE mean = +57.617383 bps/trade
- BASE PF = 2.547753
- compounded BASE = +4.58%
- max drawdown = 2.61%
- within-block concentration = 53.96%

### Immutable three-block pooled diagnostic
- N = 66
- BASE total net = +5290.819896 bps
- BASE mean = +80.163938 bps/trade
- BASE PF = 1.672662
- largest known single positive event share of pooled positive base-net PnL = 26.8815%

### Leave-one-block-out pooled diagnostics
- omit pre-Discovery: N39, +82.456387 bps/trade, PF2.249432
- omit Discovery: N35, +72.455996 bps/trade, PF1.453701
- omit 2025 OOS: N58, +83.273807 bps/trade, PF1.638224

## V3 Rare-Event Replicated Corpus Path

- at least 30 events / 3 disjoint historical blocks: **PASS** — 66 / 3
- at least two blocks genuinely independent from original Discovery selection: **PASS** — pre-Discovery historical + 2025 OOS
- every supporting block positive BASE net and PF>1: **PASS**
- pooled BASE net >0 and PF>1: **PASS**
- every leave-one-block-out pooled result net positive and PF>1: **PASS**
- pooled largest known single positive event <=40% of pooled positive PnL: **PASS** — 26.88%
- no event deletion/filter/horizon/pair/direction/threshold/cost change: **PASS**
- clean authority/provenance and no leakage: **PASS**

## Decision

**TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE — HIGH TAIL/CONCENTRATION FRAGILITY.**

The prior V2 within-block concentration failures remain recorded as fragility. They are not erased. Under the already-frozen global V3 policy, small-block concentration is no longer an automatic veto when replicated-corpus concentration and leave-one-block-out robustness pass.

Mandatory fragility flags:
- 2020 negative inside the older presample;
- 2021 dominated that presample block;
- 48.01% and 53.96% within-block concentration in two small independent blocks;
- rare event frequency;
- no genuinely prospective post-V3 event has resolved yet.

## Execution governance

This closeout does **not** authorize live trading, an order, exchange mutation, leverage, alert/webhook activation, main merge or production capital.

The existing forward watcher remains useful as operational shadow. The old V2 25-forward-event threshold no longer controls Tier-2 promotion under V3.

Before any micro-live research, a separate candidate-specific V3 readiness/authority must be frozen and its execution preflight must pass. Any prospective event that occurs before such authority is valid remains observation-only under the existing shadow rules.

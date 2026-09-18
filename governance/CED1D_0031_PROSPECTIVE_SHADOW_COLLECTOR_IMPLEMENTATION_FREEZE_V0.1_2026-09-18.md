# CED1D-0031 — PROSPECTIVE SHADOW COLLECTOR IMPLEMENTATION FREEZE V0.1 — 2026-09-18

**Status:** IMPLEMENTATION FROZEN BEFORE FIRST ELIGIBLE PROSPECTIVE MARKET OUTCOME  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`  
**Candidate:** `CED1D-0031` — AVAXUSDT Momentum20 CONTINUATION H1D  
**Parent state:** V3 TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE  
**Purpose:** deterministic public/read-only collection of post-freeze shadow evidence only.

## Controlling authority

Activation authority:
- `governance/CED1D_0031_TIER2_SHADOW_ACTIVATION_AUTHORITY_V0.2_2026-09-18.json`
- Git blob SHA: `f524aebd3cbae48b6dd916b1fba87aa88d94d2f4`

Authority precedence:
- `governance/CED1D_0031_SHADOW_AUTHORITY_PRECEDENCE_ACTIVATION_CLOSEOUT_V0.2_2026-09-18.md`
- Git blob SHA: `1bce393ef0ef0751324cd3d3c76724e297a42ae6`

First eligible signal day:
- `2026-09-18`

First eligible signal completion:
- `2026-09-19T00:00:00Z`

First eligible reference entry:
- `2026-09-19T00:01:00Z`

No pre-boundary trade may enter performance evidence.

## Frozen implementation

Collector:
- `Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/ced1d_0031_prospective_shadow_collector_v01.py`
- Git blob SHA: `bb599675431ec516daa5e0a316a202c186e9852e`

Synthetic QA:
- `Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/tests/test_ced1d_0031_prospective_shadow_collector_v01.py`
- Git blob SHA: `1e7a3e4b370fbfb556dd9af8d754c2b1384f1e1c`

Synthetic QA workflow:
- `.github/workflows/ced1d-0031-prospective-shadow-synthetic-qa.yml`
- Git blob SHA: `781baf8d0d0d86197f0fc3565b01d7c9a1a821b5`
- run: `35348150344`
- conclusion: **SUCCESS**
- real market/network access by QA: **false by design**
- prospective 2026 outcomes opened by QA: **false**

Original signal implementation authority remains mandatory:
- runner ZIP SHA256: `df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958`
- `hypotheses.py` SHA256: `dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693`

## Frozen collection behavior

The collector must rebuild the complete eligible post-freeze interval from the first signal day through an explicitly supplied `through_signal_day`.

It may not start from a later winning subperiod.

Source-readiness guard:
- `through_signal_day <= current UTC date - 3 days`

This deliberately allows the required daily public archives to close before scoring a signal. It is a reproducibility delay, not a signal change.

Minimum warm-up:
- exactly the required 20-calendar-day signal lookback plus execution path days;
- warm-up is input-only;
- no pre-boundary trade performance may be scored.

## Public/read-only sources

Price:
- Binance Public Data USD-M daily `klines/AVAXUSDT/1m`
- provider `.CHECKSUM` required.

Funding rate:
- unauthenticated public market-data endpoint on `data-api.binance.vision`;
- canonical response SHA256 recorded.

Funding mark interval:
- Binance Public Data USD-M daily `markPriceKlines/AVAXUSDT/1m`;
- provider `.CHECKSUM` required;
- funding lower/upper construction mirrors the frozen 2025 runner.

Execution proxy:
- Binance Public Data USD-M daily `aggTrades/AVAXUSDT`;
- provider `.CHECKSUM` required;
- 100 USDT/leg;
- same-side observed taker prints;
- 5,000 ms maximum accumulation;
- BASE 4 bps/fill, STRESS 5 bps/fill;
- no maker/VIP/BNB discount.

Capacity:
- Binance Public Data USD-M daily `bookDepth/AVAXUSDT`;
- provider `.CHECKSUM` required;
- BUY uses +1% cumulative band;
- SELL uses -1% cumulative band;
- latest snapshot <= reference timestamp;
- snapshot age <=60 seconds;
- required cumulative notional >=100 USDT.

## Frozen output

Every successful collection emits:
- `CED1D_0031_PROSPECTIVE_SHADOW_LEDGER.csv`
- `CED1D_0031_PROSPECTIVE_SHADOW_RECEIPT_V0.1.json`

A source/processing failure is fail-closed and must emit a failure receipt when the collector has entered the collection phase. No missing event/source may be silently removed.

## Two-stage evidence routing

V0.1 operational checkpoint:
- >=10 resolved shadow trade events;
- >=14 calendar days;
- operational integrity only;
- cannot create Tier 1.

V0.2 Tier-1 evidence minimum:
- >=60 completed prospective shadow trade events;
- >=8 complete Monday-Sunday UTC signal weeks;
- both required;
- >=50 complete aggTrades proxy pairs for execution economics;
- no early Tier-1 adjudication.

The collector may only emit `TIER1_ADJUDICATION_ELIGIBLE` when every prospectively frozen operational/economic/capacity/concentration gate passes after the minimum sample.

That label does **not** automatically create Tier 1. A separate V3 adjudication remains mandatory.

## Firewall

- no authenticated trading endpoint
- no orders
- no exchange mutation
- no wallets
- no leverage
- no real capital
- no auto-execution webhook
- no parameter change
- no pre-boundary performance backfill
- no merge to main

At this freeze point:
- eligible post-freeze events resolved: **0**
- market outcomes opened by this collector: **0**
- Tier 1 claimed: **false**

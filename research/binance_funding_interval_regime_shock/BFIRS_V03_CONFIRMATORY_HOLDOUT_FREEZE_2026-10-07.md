# BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001
## V0.3 CONFIRMATORY HOLDOUT FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY 2026 MARKET OUTCOME

### 1. Discovery authority
V0.2 Discovery survived under its frozen rules.

Discovery run:
- workflow run: 37571323430
- head SHA: e4dd17af54706ba4cc7a46d4b61421705ceeda6d
- artifact ID: 11460975843
- artifact digest: sha256:1a0e290744e58d9a33a7bf34f5742c01ef4291b90e3a4397532bd158ca09dbe5
- verdict: SURVIVES_FUNDING_INTERVAL_DISCOVERY
- 35 analyzable events
- 30 analyzable clusters
- 27 unique contracts
- median C_k = 0.03432798500000001
- sign test: 23/30 positive, p = 0.002611439675092697
- bootstrap median C_k 95% CI = [0.01568033875, 0.062001635]
- both chronological halves positive
- all frozen primary gates passed.

These known 2023-2025 outcomes MUST NOT be used to alter any confirmatory rule below.

### 2. Untouched holdout calendar
Confirmatory source/outcome window:
- 2026-01-01 00:00:00 UTC through 2026-09-30 23:59:59 UTC.

Reason frozen before 2026 outcome access:
- complete months only, so official monthly Binance Data Vision archives can be used consistently;
- October 2026 is excluded entirely;
- no 2026 premium/funding/price outcome has been opened for this family before this freeze.

### 3. Event eligibility
Use the SAME economic event definition as V0.1.

An asset-event qualifies only if ALL:
1. USDⓈ-M USDT perpetual contract explicitly identified;
2. already live before the change;
3. official Binance publication precedes effective timestamp;
4. exact effective UTC timestamp explicit;
5. old and new funding settlement intervals explicit;
6. new interval is SHORTER than old interval;
7. fixed named-contract transition, not only a generic future automatic rule;
8. not an initial listing/launch specification;
9. not a delisting/automatic-settlement bundle;
10. official monthly premiumIndexKlines 1m and fundingRate archive capability exists for event month.

Same explicit exclusions as V0.1:
- interval lengthening/reversion events;
- generic dynamic-rule-only announcements;
- launch terms;
- COIN-M only;
- BUSD-only;
- delisting/settlement bundles;
- outcome-selected events.

### 4. Confirmatory source gate
HOLDOUT_SOURCE_PASS requires ALL:
- >=12 independent eligible shock clusters;
- >=20 eligible asset-events;
- >=8 unique contracts;
- no single shock cluster >35% of eligible events;
- all required source/archive capabilities pass.

If complete 2026-01 through 2026-09 enumeration fails the minimum:
VERDICT = HOLDOUT_INSUFFICIENT_SAMPLE.

If provenance/enumeration cannot be demonstrated:
VERDICT = HOLDOUT_SOURCE_BLOCKED.

No 2026 market values may be opened unless HOLDOUT_SOURCE_PASS.

### 5. Confirmatory analysis rules
If HOLDOUT_SOURCE_PASS, the V0.2 analysis specification is replicated WITHOUT CHANGE.

Primary information timestamp:
- T0 = official publication timestamp.
- Tm = first whole minute strictly after T0.

Windows:
- baseline: [Tm-65m, Tm-5m)
- post-announcement: [Tm+5m, Tm+65m)

Controls:
- BTCUSDT
- ETHUSDT
- BNBUSDT
Remove a control only if it is treated in the same cluster.
Require >=2 remaining valid controls.
No replacement controls.

Data validity:
- >=54/60 bars per window;
- finite premium closes;
- no interpolation/fill;
- same Binance Data Vision premiumIndexKlines source only.

Endpoint:
B(s,W) = median(abs(premium_index_close))
C_raw(s) = B(s,baseline) - B(s,post)
C_e = C_raw(treated) - median(C_raw(valid controls))
C_k = median(C_e within shock cluster)

Primary unit = independent shock cluster.

### 6. Confirmatory sample gates after missingness
Require ALL:
- >=12 analyzable clusters;
- >=20 analyzable asset-events;
- >=8 unique analyzable contracts;
- no single cluster >35% of analyzable events;
- >=80% of source-gate events remain analyzable.

Failure of any gate:
VERDICT = FAILS_CONFIRMATION.

### 7. Confirmatory statistical gates
Replicate V0.2 exactly:
- median C_k >= 0.00020 (2 bps)
- exact one-sided sign test H1: P(C_k>0)>0.5, alpha=0.05, zeros fail
- 10,000 cluster bootstrap resamples
- RNG seed = 26061007
- 95% percentile lower bound of median C_k > 0
- split clusters chronologically into two halves;
- median C_k >0 in BOTH halves.

No changed seed, floor, horizon, controls, missingness, endpoint, or aggregation.

### 8. Confirmatory verdict
If ALL source, sample, economic, statistical and temporal gates pass:
VERDICT = CONFIRMED_FUNDING_INTERVAL_EDGE

Otherwise after lawful 2026 outcome opening:
VERDICT = FAILS_CONFIRMATION

If source gate fails before outcomes:
- HOLDOUT_INSUFFICIENT_SAMPLE
or
- HOLDOUT_SOURCE_BLOCKED

### 9. Tradeability boundary
Even CONFIRMED_FUNDING_INTERVAL_EDGE is NOT authorization to trade.

If confirmed:
- stop;
- preserve 2026 holdout receipt;
- create a separate pre-PnL / tradeability freeze;
- define executable entry/exit, hedge leg, fees, slippage, borrow/capital assumptions and venue constraints BEFORE opening PnL.

### 10. Governance
- research-only;
- fail-closed;
- no main merge;
- no live trading;
- no orders;
- no wallets;
- no account reads;
- no authenticated/private endpoints;
- no exchange mutation;
- no spending;
- no post-outcome tuning.

### 11. Outcome-access declaration
At the time this freeze is committed, no 2026 premium, funding, price, return, volume, volatility, liquidation, OI or PnL outcome from this family has been opened.

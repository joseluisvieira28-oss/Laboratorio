# BNB-LAUNCHPOOL-DEMAND-001 — OFFICIAL DISCOVERY CLOSEOUT

MVE: `BLP-BNBBTC-24H-001`  
Date: `2026-09-16`  
Canonical Discovery run: `35131509738`  
Canonical Discovery artifact: `10461432431`  
Artifact ZIP SHA256: `2eacf1493bc564159a193380084334b22ca71461a2d6bfcc61ff07b4d6fe0b11`  
Ledger SHA256: `a380d7e185f9e354b6d04824e52208fef1d3e391318d07d9f34ef32b63b384cc`  
Final classification: **DISCOVERY_FAIL_NO_PROMOTION**  
Promotion: **FALSE**

## Frozen mechanism

Official Binance Launchpool announcements with explicit BNB staking/locking were treated as exogenous public BNB-utility shocks. The frozen executable mechanism tested LONG `BNBBTC` at the first 15-minute Spot open strictly after the canonical Binance CMS publication timestamp, held exactly 24 hours, one active trade at a time. Adjacent announcements within 60 minutes were clustered as one information shock. Round-trip costs were 20 bps BASE and 30 bps STRESS.

The pre-outcome source population contained Launchpool project numbers 31 through 63. Thirty-three official events became 32 source-only information clusters; one later overlapping cluster was suppressed under the frozen one-active-trade rule, leaving 31 selected trades.

## Source integrity

Official Binance Support CMS source gate: `SOURCE_DATA_PASS`, 33 canonical events.  
Canonical event manifest SHA256: `f0bd730090c09d59e8ef6b558cc923fcface3c5568e44f7765a67181b2fe43d1`.

Binance Data Vision BNBBTC 15m source gate: `MARKET_SOURCE_DATA_PASS`, 27 monthly archives from 2022-10 through 2024-12, all pinned to official checksums with zero selected execution-path failures.  
Market archive manifest SHA256: `da0f1928b40e2185dfd2cefe09654d2c90be6b0ca1964e6e3b80fe25431d4fc4`.

Only timestamp and required BNBBTC open values were parsed during Discovery. High, low, close and volume were not parsed. 2025 and 2026 were not requested or opened.

## Frozen Discovery result

- Resolved selected trades: `31`
- Gross mean: `+108.8664527105 bps/trade`
- BASE mean NET20: `+88.8664527105 bps/trade`
- BASE median NET20: `+12.9405802610 bps/trade`
- BASE profit factor: `2.2103965202`
- BASE win rate: `51.6129032258%`
- BASE total: `+2754.8600340259 bps`
- STRESS mean NET30: `+78.8664527105 bps/trade`
- STRESS profit factor: `2.0077749672`
- STRESS total: `+2444.8600340259 bps`
- Maximum single-trade share of positive BASE contribution: `14.7907549426%`

Calendar BASE results:

- 2022 partial: N=`1`, mean `+12.9405802610 bps/trade` — diagnostic only.
- 2023: N=`10`, mean `+184.5282910227 bps/trade` — PASS.
- 2024: N=`20`, mean `+44.8318271769 bps/trade` — PASS.

Frozen event-level nonparametric bootstrap, 5,000 replications, seed 160916:

- 95% CI for BASE mean: `[-11.1865348146, +196.9682140910] bps/trade`
- bootstrap median mean: `+88.7204136614 bps/trade`

## Promotion gates

All frozen gates passed except one:

**FAIL — bootstrap 95% CI lower bound > 0.**

Observed lower bound was `-11.1865348146 bps/trade`.

Therefore the all-required promotion contract fails even though point economics, stress economics, median, profit factor, both full calendar years, concentration, sample size, source integrity and execution-path integrity all passed.

## Scientific decision

The exact MVE is classified **DISCOVERY_FAIL_NO_PROMOTION**. This is not relabeled `NO_EDGE`: the observed effect is economically positive but uncertainty remains too large under the prospectively frozen bootstrap gate. The exact MVE is not eligible for 2025 OOS opening, forward promotion, paper-production promotion, or live trading under this lineage.

No post-outcome direction inversion, hold-period change, cluster-window change, cost change, event deletion, pair substitution, stop/target overlay, favorable subperiod selection, or 2025/2026 rescue is permitted under this MVE ID.

## Governance

- 2025 accessed: **NO**
- 2026 accessed: **NO**
- live trading: **NO**
- exchange mutation: **NO**
- orders: **NO**
- merge to main: **NO**
- deployment: **NO**
- post-outcome rescue: **NO**

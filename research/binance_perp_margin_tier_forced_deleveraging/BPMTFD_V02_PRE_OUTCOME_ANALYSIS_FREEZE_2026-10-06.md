# BINANCE-PERP-MARGIN-TIER-FORCED-DELEVERAGING-001
## V0.2 PRE-OUTCOME ANALYSIS FREEZE
Date: 2026-10-06
Status: FROZEN BEFORE ANY V0.2 MARKET OUTCOME

### 1. Authority and pinned source universe
This V0.2 consumes ONLY the eligible event universe already frozen by the corrected V0.1 source gate.

Pinned source receipt:
- workflow run: 37498232442
- head SHA: 62b5844d1855bc673f304538e8ff14d7654a59d1
- artifact ID: 11428188696
- artifact name: bpmtfd-v01-corrected-source-gate-receipt
- artifact digest: sha256:01798375ed49565b04275b73f01e2d68e7804c7232f8d6a445b0eba9889eb9ab
- source-gate verdict: SOURCE_GATE_PASS
- eligible asset-events: 98
- independent shock clusters: as contained in the pinned artifact
- unique contracts: 89
- calendar years: 2023, 2024, 2025
- 2026 remains CLOSED.

The Development runner MUST NOT re-enumerate Binance announcements, add events, remove events based on outcomes, substitute article codes, alter effective timestamps, or source a different eligible universe.

### 2. Scientific hypothesis
The source freeze asks whether an effective Binance USDⓈ-M margin-tier tightening that explicitly affects existing positions creates direction-agnostic forced risk adjustment.

Primary causal signature:
- abnormal volatility rises around the exact effective timestamp; AND
- abnormal trading activity rises around the exact effective timestamp.

This is NOT a signed-return hypothesis.
No long/short directional claim is permitted in V0.2.

### 3. Market source
Frozen outcome source:
- Binance Public Data / Data Vision USDⓈ-M futures 1-minute klines.
- Exact contract symbol from the pinned source receipt.
- Monthly 1-minute kline archive for the event month and, only when required by the frozen window, adjacent month(s).
- No exchange API substitution.
- No alternate venue substitution.
- No trades/aggTrades/funding/liquidation/OI source may rescue a failed V0.2.

Kline fields used:
- open time
- open/high/low/close
- quote asset volume
- number of trades (descriptive only)

### 4. Frozen timestamp alignment and windows
For each eligible asset-event, let T be the exact effective UTC timestamp from the pinned source receipt.

All windows are half-open and aligned to Binance 1-minute open times.

Baseline window:
- [T - 120 minutes, T - 60 minutes)
- 60 expected one-minute bars.

Primary event window:
- [T - 30 minutes, T + 30 minutes)
- 60 expected one-minute bars.

Reason fixed before outcome access:
the mechanism can generate anticipatory deleveraging immediately before the effective timestamp as well as forced adjustment immediately after it. A symmetric window captures the effective-time shock without allowing post-outcome horizon selection.

No alternate primary horizon is allowed after outcomes.
No post-only horizon can rescue a failure.

### 5. Predefined unaffected-contract controls
Frozen control panel:
- BTCUSDT
- ETHUSDT
- BNBUSDT

For each shock cluster:
1. remove any control symbol that is itself a treated contract in that same article/effective-time cluster;
2. require at least TWO remaining control symbols with valid data;
3. no replacement or fallback control symbol is allowed.

Controls use the exact same source, baseline window, event window, data validation, and metric formulas as treated contracts.

### 6. Data validity and missingness
A treated asset-event is analyzable only if:
- no duplicate open-time bars exist in either primary window;
- >=54 of 60 expected bars are present in BOTH baseline and event windows for the treated contract;
- each required control also has >=54 of 60 expected bars in BOTH windows;
- every used OHLC value is finite and strictly positive;
- quote asset volume is finite and >=0;
- event timestamp is inside 2023-2025;
- at least two valid predefined controls remain.

No interpolation.
No forward/back fill.
No manual bar repair.
No symbol substitution.
No venue substitution.
No event-time movement.

If an archive is unavailable/corrupt, the event is excluded under this pre-frozen missingness rule.

### 7. Frozen volatility endpoint
For any symbol-window W, compute one-minute close-to-close log returns using only consecutive available one-minute closes whose timestamps differ by exactly 60 seconds.

Define:
RV(W) = sum(r_i^2)

Require at least 53 valid one-minute returns in the 60-minute window.

For symbol s:
V_raw(s) = ln( RV_event(s) / RV_baseline(s) )

If either RV is <=0, the symbol-window is invalid.

For each treated asset-event e, with valid controls C:
V_e = V_raw(treated) - median_{c in C}(V_raw(c))

Interpretation:
V_e > 0 means the treated contract's event-window realized variance increased more than contemporaneous unaffected controls.

### 8. Frozen activity endpoint
For symbol-window W:
QV(W) = mean one-minute quote asset volume over available valid bars.

Require >=54 valid bars and QV(W) > 0.

For symbol s:
A_raw(s) = ln( QV_event(s) / QV_baseline(s) )

For each treated asset-event e:
A_e = A_raw(treated) - median_{c in C}(A_raw(c))

Interpretation:
A_e > 0 means the treated contract's event-window quote-volume activity increased more than contemporaneous unaffected controls.

Number of trades is descriptive only and may not affect the verdict.

### 9. Shock-cluster aggregation
An independent shock cluster is exactly:
article_code + effective_utc

For each analyzable cluster k:
- V_k = median V_e across analyzable treated asset-events in that cluster
- A_k = median A_e across analyzable treated asset-events in that cluster
- J_k = min(V_k, A_k)

J_k is the frozen PRIMARY joint mechanism score.
A positive J_k requires BOTH volatility and activity to be positive at the cluster level.

No weighting by number of affected contracts.
No asset-level pseudo-replication in the primary statistical test.

### 10. Development sample gates
Development is scientifically valid only if ALL hold after pre-frozen missingness:
- >=12 analyzable independent shock clusters;
- >=20 analyzable treated asset-events;
- >=8 unique treated contracts;
- >=2 calendar years represented;
- no single shock cluster >35% of analyzable treated asset-events;
- no single calendar year >70% of analyzable independent clusters.

If any sample gate fails:
VERDICT = NO_EDGE_DISCOVERY.

This failure may not be rescued with alternate controls, horizons, assets, subsets, or missingness thresholds.

### 11. Exact primary statistical test
Primary unit: shock cluster.

For J_k:
- H0: P(J_k > 0) <= 0.5
- H1: P(J_k > 0) > 0.5
- exact one-sided sign test;
- zeros count as failures;
- alpha = 0.05.

Bootstrap:
- 10,000 cluster-level resamples with replacement;
- RNG seed = 26061006;
- statistic = median J_k;
- percentile 95% confidence interval;
- require lower bound > 0.

### 12. Frozen economic-effect floors
To avoid surviving on a statistically positive but tiny joint effect, ALL must hold:
1. median(V_k) >= ln(1.10)
2. median(A_k) >= ln(1.10)
3. median(J_k) > 0
4. exact one-sided sign-test p(J_k>0) < 0.05
5. bootstrap 95% lower bound for median(J_k) > 0

ln(1.10) is frozen as a 10% median abnormal uplift floor for each mechanism endpoint.

### 13. Primary verdict
If ALL sample gates and ALL five primary gates pass:
VERDICT = SURVIVES_MARGIN_TIER_DISCOVERY

Otherwise:
VERDICT = NO_EDGE_DISCOVERY

No partial pass.
No rescue subset.
No alternate horizon resurrection.
No directional inversion.
No changing controls.
No threshold changes after outcome access.

### 14. Descriptive diagnostics
Allowed but NON-RESCUING:
- median treated raw event/baseline RV ratio;
- median treated raw event/baseline quote-volume ratio;
- median V_k, A_k, J_k;
- per-year descriptive medians;
- descriptive number-of-trades uplift using the same windows;
- exclusions by missingness reason.

These diagnostics may explain the result but may not alter the verdict.

### 15. Tradeability
V0.2 is a mechanism discovery test, not a tradable directional strategy.
No fee/slippage/PnL gate is primary here because no execution rule is defined.
If V0.2 survives, a later confirmatory freeze must define any monetization route before opening confirmatory outcomes.

### 16. One-shot rule
Development outcomes may be opened ONCE after this freeze.

Purely technical deterministic failures may be repaired only if:
- the scientific freeze remains byte-for-byte unchanged;
- the failed run is preserved;
- no scientific threshold, window, control, endpoint, sample rule, or verdict rule changes.

### 17. Governance
- research-only;
- fail-closed;
- no main merge;
- no live trading;
- no orders;
- no wallets;
- no account reads;
- no authenticated/private exchange endpoints;
- no exchange mutation;
- no spending;
- no 2026 outcomes;
- no post-outcome tuning.

### 18. Outcome-access declaration
At the time this freeze is committed, no V0.2 market outcome value has been opened for the pinned 98-event universe.

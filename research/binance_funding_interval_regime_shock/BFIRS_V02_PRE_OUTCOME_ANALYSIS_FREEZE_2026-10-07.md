# BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001
## V0.2 PRE-OUTCOME ANALYSIS FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY V0.2 MARKET OUTCOME

### 1. Authority and pinned source universe
This V0.2 consumes ONLY the eligible event universe from the frozen V0.1 source gate.

Pinned source receipt:
- workflow run: 37570814145
- head SHA: 71c3a50722f8c9d231f052dda2e550ec56cf9947
- artifact ID: 11460134993
- artifact name: bfirs-v01-source-gate-receipt
- artifact digest: sha256:ffb8dc3d9ddcd70e71fd65b26f5be2163ddc9d15a041231f10338019fec5a4fb
- source verdict: SOURCE_GATE_PASS
- eligible asset-events: 35
- independent shock clusters: 30
- unique contracts: 27
- years: 2023, 2024, 2025
- max cluster concentration: 11.43%
- 2026 remains CLOSED.

The Development runner MUST NOT re-enumerate announcements, add/remove events based on outcomes, alter publication/effective timestamps, or substitute a different eligible universe.

### 2. Scientific hypothesis
A pre-announced increase in funding settlement frequency changes the carry cadence of an already-live USDⓈ-M perpetual contract.

Primary hypothesis:
after the public announcement becomes tradable information, the affected contract's absolute premium index should compress toward zero more than contemporaneous unaffected controls.

This is a basis/premium normalization hypothesis.
It is NOT a signed outright-price return hypothesis.

### 3. Primary information timestamp
Primary T0 = official Binance article publication timestamp from the pinned source receipt.

Because publication times can include seconds while the outcome archive is 1-minute:
- Tm = first whole-minute timestamp strictly AFTER T0.

All outcome windows are defined relative to Tm.
This avoids using the partially formed publication minute.

### 4. Frozen outcome source
Primary market outcome:
- Binance Public Data / Data Vision USDⓈ-M 1-minute premiumIndexKlines.
- exact treated symbol from pinned source receipt.
- monthly archive for the publication month and adjacent month only if a frozen window crosses a month boundary.

No alternate venue.
No mark-price or last-price substitution.
No spot/perp reconstructed basis may rescue a failure.
FundingRate values may be opened only as descriptive diagnostics and cannot affect the primary verdict.

### 5. Frozen windows
Baseline window:
- [Tm - 65 minutes, Tm - 5 minutes)
- 60 expected one-minute bars.

Post-announcement window:
- [Tm + 5 minutes, Tm + 65 minutes)
- 60 expected one-minute bars.

The 5-minute gap before and after Tm is frozen to avoid timestamp ambiguity and non-executable reaction in the publication minute.

No alternate primary horizon after outcome access.

### 6. Frozen untreated controls
Control panel:
- BTCUSDT
- ETHUSDT
- BNBUSDT

For each shock cluster:
1. remove any control symbol that is itself treated in that cluster;
2. require at least TWO remaining valid controls;
3. no replacement control is allowed.

Controls use the same Data Vision source, windows, validation and metric formula.

### 7. Data validity / missingness
For every symbol-window:
- no duplicate open-time bars;
- >=54 of 60 expected bars;
- every used premium close is finite;
- no interpolation;
- no forward/back fill;
- no alternate venue;
- no timestamp movement.

A treated asset-event is analyzable only if its two windows and at least two control panels satisfy the rule.

### 8. Frozen premium-compression endpoint
For symbol s and window W:
B(s,W) = median( abs(premium_index_close) )

For symbol s:
C_raw(s) = B(s,baseline) - B(s,post)

Positive C_raw means absolute premium compressed toward zero after publication.

For treated event e with valid control set C:
C_e = C_raw(treated) - median_{c in C}(C_raw(c))

Positive C_e means the treated contract compressed more than contemporaneous unaffected controls.

### 9. Shock-cluster aggregation
Independent cluster key:
article_code + effective_utc + old_interval_hours + new_interval_hours

For each analyzable cluster k:
C_k = median C_e across analyzable treated contracts in that cluster.

Each cluster receives equal weight regardless of number of treated contracts.
No asset-level pseudo-replication in the primary test.

### 10. Development sample gates
Development is scientifically valid only if ALL hold:
- >=12 analyzable independent clusters;
- >=20 analyzable asset-events;
- >=8 unique analyzable contracts;
- >=2 calendar years represented;
- no single cluster >35% of analyzable events;
- >=80% of the 35 pinned source events remain analyzable.

If any sample gate fails:
VERDICT = NO_EDGE_DISCOVERY.

No rescue by changing controls, missingness rules, windows, or assets.

### 11. Primary statistical test
Primary unit: shock cluster.

For C_k:
- H0: P(C_k > 0) <= 0.5
- H1: P(C_k > 0) > 0.5
- exact one-sided sign test;
- zeros count as failures;
- alpha = 0.05.

Bootstrap:
- 10,000 cluster-level resamples with replacement;
- RNG seed = 26061007;
- statistic = median C_k;
- percentile 95% confidence interval;
- require lower bound > 0.

### 12. Frozen economic-effect floor
Primary economic floor:
median(C_k) >= 0.00020

This equals 2 basis points of abnormal absolute-premium compression.

### 13. Frozen temporal robustness
Split analyzable shock clusters chronologically into two halves by T0.
If odd, the earlier half contains one fewer cluster.

Require:
- median C_k > 0 in BOTH chronological halves.

This is primary and non-rescuable.

### 14. Primary verdict
SURVIVES_FUNDING_INTERVAL_DISCOVERY requires ALL:
1. every Development sample gate passes;
2. median C_k >= 0.00020;
3. exact one-sided sign-test p < 0.05;
4. bootstrap 95% lower bound for median C_k > 0;
5. median C_k > 0 in both chronological halves.

Otherwise:
NO_EDGE_DISCOVERY.

No partial pass.
No alternate horizon resurrection.
No directional inversion.
No subset rescue.
No threshold relaxation.

### 15. Non-promotional diagnostics
Allowed after outcome access but cannot rescue:
- median treated raw C_raw;
- distribution of C_k by old->new interval;
- per-year medians;
- sign of last funding settlement before T0;
- analogous compression around the effective timestamp using the SAME 60m/5m-gap windows;
- event exclusions.

### 16. Tradeability
V0.2 is a mechanism-discovery test.
It does not authorize or define a trade.

If V0.2 survives:
- do not call it a diamond;
- do not open 2026;
- create a new confirmatory/tradeability freeze before any PnL or execution rule.

### 17. One-shot rule
Development outcomes may be opened ONCE after this freeze.

Purely technical deterministic fixes are allowed only if:
- this scientific freeze remains byte-for-byte unchanged;
- failed run is preserved;
- no scientific rule, window, control, endpoint, threshold or verdict gate changes.

### 18. Governance
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

### 19. Outcome-access declaration
At the time this freeze is committed, no V0.2 premium, funding, price, return, volume, volatility, liquidation, OI or PnL value has been opened for the pinned 35-event universe.

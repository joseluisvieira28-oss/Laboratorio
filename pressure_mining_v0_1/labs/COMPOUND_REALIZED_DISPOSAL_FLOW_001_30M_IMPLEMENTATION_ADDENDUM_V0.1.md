# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — CANONICAL 30M IMPLEMENTATION ADDENDUM V0.1

Date: 2026-09-28
Status: PRE-OUTCOME IMPLEMENTATION DETAIL / CANONICAL SCIENCE UNCHANGED

Authority:
COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md
commit 2191bbf741ced5f801d8ae4034bd126c3b91cbc8.

No protected market outcome has been opened.

## 1. Protected-year boundary

The canonical event window is calendar 2025 and 2026 remains protected.

Therefore an otherwise eligible 2025 event is marked PROTECTED_BOUNDARY_EXCLUSION if its required 30-minute EXIT timestamp is >= 2026-01-01T00:00:00Z.

This test uses only event timestamps.
It occurs before any market archive is opened.
No 2026 market archive may be requested.

This is a governance firewall, not a strategy filter.

## 2. Exact PF implementation

For a vector of net event returns:
- positive_sum = sum(x for x > 0)
- loss_sum_abs = abs(sum(x for x < 0))
- PF = positive_sum / loss_sum_abs when loss_sum_abs > 0
- if loss_sum_abs == 0 and positive_sum > 0, PF is treated as +infinity for the >1 gate and serialized as the string INF.

## 3. Exact concentration implementation

Largest positive event share:
max positive BASE_NET event / sum of all positive BASE_NET events.

Largest ISO-week positive contribution share:
for every event, take max(BASE_NET, 0);
sum those positive contributions inside each UTC ISO week;
largest weekly positive contribution / total positive BASE_NET contribution.

If total positive BASE_NET contribution is zero, both concentration gates fail.

## 4. Bootstrap percentile implementation

- UTC ISO weeks are the resampling clusters.
- Draw exactly K weeks with replacement, where K is the number of unique eligible weeks.
- A drawn week contributes all of its eligible events; repeated drawn weeks contribute repeated copies.
- Statistic = pooled mean BASE_NET_BPS across the resampled events.
- 10,000 replicates, Python Random seed 20260927.
- 95% percentile interval uses sorted bootstrap means at floor-index positions corresponding to 2.5% and 97.5% of N-1.

## 5. Source fingerprint firewall

Before opening any Binance kline ZIP:
- reconstruct the canonical four-asset 2025 predictor population;
- aggregate by (collateral asset, transaction hash);
- apply 30m same-asset overlap suppression;
- apply protected-year boundary exclusion;
- compare source-only population counts against the pre-outcome readiness receipt.

Any unexplained source drift causes fail-closed before market-price access.

## 6. No scientific changes

Unchanged:
direction, assets, BTC benchmark, 30m horizon, entry/exit rule, BASE20, STRESS30, sample gates, inference, concentration gates, no-rescue rule.

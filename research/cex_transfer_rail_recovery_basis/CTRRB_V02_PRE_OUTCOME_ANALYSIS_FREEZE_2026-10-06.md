# CEX-TRANSFER-RAIL-RECOVERY-BASIS-001
## V0.2 PRE-OUTCOME ANALYSIS FREEZE
Date: 2026-10-06
Status: FROZEN BEFORE ANY MARKET OUTCOME
Parent source receipt: CTRRB_V011_SOURCE_GATE_PASS_RECEIPT_2026-10-06.md

### 1. Pinned Development universe
Development consumes ONLY the 136 events in `eligible_events` from:
- workflow run 37487514764
- artifact ID 11424097342
- artifact digest sha256:464c3d35924ac525e15ec08dc2a620ad111cbf6c49254294f98afd1307dab54d
- head SHA e28223e0beb9f3613e735eeb350e20164dc11b55

Do not re-enumerate live status history to change event membership.
2026 remains CLOSED.

### 2. Market series
Affected venue:
- Coinbase Exchange spot `{SYMBOL}-USD`, 1-minute candles, public unauthenticated endpoint.

Reference venue:
- Binance spot `{SYMBOL}USDT`, 1-minute klines from the exact monthly public archive on data.binance.vision identified during SOURCE GATE.

No OKX, no second reference, no venue substitution after outcomes.

Price field:
- 1-minute close on both venues.

Time convention:
- UTC.
- Candle time is the minute-open timestamp.

### 3. Frozen event boundaries
For each pinned event:
- `T_isolation` = source-gate `start_utc`.
- `T_recovery` = source-gate `end_utc`.

These are the official incident-history start/end boundaries already pinned before outcomes.

### 4. Normalized cross-venue basis
The USD/USDT level difference is removed by anchoring each venue to the same pre-isolation minute.

Anchor:
- target = `T_isolation - 1 minute`;
- use the latest synchronized minute at or before target with both venues present;
- maximum backward tolerance = 2 minutes;
- if unavailable, event is MISSING and excluded under the frozen missingness rule.

For synchronized minute t:

`r_CB(t) = ln(P_CB(t) / P_CB(anchor))`

`r_BN(t) = ln(P_BN(t) / P_BN(anchor))`

`B(t) = 10,000 * [r_CB(t) - r_BN(t)]` basis points.

The sign is descriptive only. Primary mechanism uses absolute basis.

### 5. Primary horizon and within-event control
Required recovery-relative points:
- `t_pre30 = T_recovery - 31 minutes`
- `t_pre1  = T_recovery - 1 minute`
- `t_post30 = T_recovery + 30 minutes`

For each target, use the closest synchronized minute with absolute timestamp error <= 2 minutes. Ties choose the earlier minute.

Define:
- pre-recovery compression: `C_pre = |B(t_pre30)| - |B(t_pre1)|`
- post-recovery compression: `C_post = |B(t_pre1)| - |B(t_post30)|`
- primary causal contrast: `A = C_post - C_pre`

Economic hypothesis:
rail restoration should make basis compress more in the 30 minutes AFTER recovery than in the immediately preceding 30 minutes, therefore `A > 0`.

Primary horizon = 30 minutes. It cannot be changed after outcomes.

Secondary diagnostic horizons:
5m, 15m, 60m after T_recovery.
They are descriptive only and CANNOT rescue a failed primary.

### 6. Liquidity minimum — frozen before outcomes
Liquidity is measured only in the pre-recovery window `[T_recovery-120m, T_recovery-60m]`.

For each venue:
- require >= 90% of expected 1-minute bars;
- Coinbase minute quote-notional = close * base volume;
- Binance minute quote-notional = quote-asset volume;
- median minute quote-notional must be >= USD/USDT 25,000 on EACH venue.

If either venue fails, exclude the event as PRE-FROZEN LIQUIDITY_FAIL.
No alternative threshold may be tried.

### 7. Missingness / data quality
An event is analyzable only if:
- anchor exists within frozen tolerance;
- t_pre30, t_pre1, t_post30 exist within frozen tolerance;
- liquidity window completeness passes;
- no duplicate timestamps after normalization;
- all used prices are finite and >0.

No interpolation.
No forward-filling.
No venue substitution.
No manually repairing individual events.

### 8. Event clustering / independence
To reduce common-outage pseudo-replication:
- sort analyzable events by T_recovery;
- create transitive recovery clusters where adjacent recovery times are <= 60 minutes apart, regardless of asset;
- cluster-level primary value = median A of events in that cluster;
- cluster-level C_post = median C_post in that cluster.

Statistical inference is performed on recovery clusters, not raw events.

Minimum Development sample:
- >=12 analyzable recovery clusters;
- >=4 unique assets after all frozen exclusions;
- no single asset >40% of analyzable raw events;
- no single calendar year >70% of analyzable raw events.

Failure of any minimum/concentration gate => NO_EDGE_DISCOVERY. No threshold rescue.

### 9. Exact primary statistical test
Primary observations = cluster-level A values.

Test:
- one-sided exact sign test of P(A_cluster > 0) > 0.5;
- zero A values count as failures/non-positive;
- alpha = 0.05.

Effect gates:
1. median cluster-level A > 0 bps;
2. median cluster-level A >= 5 bps;
3. one-sided exact sign-test p < 0.05;
4. nonparametric cluster bootstrap (10,000 resamples, RNG seed 26061006) 95% percentile CI lower bound for median A > 0;
5. median cluster-level C_post > 0 bps.

ALL five must pass for SURVIVES_RAIL_RECOVERY_DISCOVERY.

If any primary gate fails => NO_EDGE_DISCOVERY.
No rescue subsets or alternate test.

### 10. Robustness diagnostics — non-rescuing
Report but do not change verdict:
- 5m / 15m / 60m post-recovery compression;
- raw-event versus cluster-level summaries;
- leave-one-recovery-cluster-out distribution of median A;
- leave-one-asset-out median A for assets with >=5 analyzable events;
- per-year medians;
- distribution of |B(t_pre1)|;
- sign of B at recovery;
- incident duration versus A.

These diagnostics cannot promote a failed primary.

### 11. Calendar/project concentration
Primary verdict also requires the frozen concentration gates in section 8.
No project/token subgroup may be selected after outcomes.

### 12. Fees and slippage
The scientific primary asks whether the rail-restoration mechanism causes relative-basis convergence. It is NOT a live-trading GO.

A pre-frozen execution-friction diagnostic will also be reported:
- 4 taker fills total for an entry+exit two-venue hedge;
- fixed fee allowance = 10 bps per fill = 40 bps;
- fixed slippage allowance = 5 bps per fill = 20 bps;
- total round-trip friction diagnostic = 60 bps.

Define `net_C_post_60 = C_post - 60 bps`.
Report its median and fraction >0.

This 60-bps diagnostic does NOT rescue or overturn the primary scientific verdict. A surviving scientific result with negative friction-adjusted economics is explicitly NOT trade-ready.

### 13. One-shot Development rule
After this freeze is committed:
- Development may open 2022-2025 price/volume outcomes ONCE.
- No methodology changes after outcome access.
- No re-running with different horizons, thresholds, assets, fees, clustering, venue, quote, or tests.
- A purely technical deterministic bug may be repaired only if it does not alter scientific rules; repair must be documented before any corrected rerun and the first broken run preserved.

### 14. Verdict taxonomy
After the one-shot Development:
- NO_EDGE_DISCOVERY
- SURVIVES_RAIL_RECOVERY_DISCOVERY

SOURCE_BLOCKED / INSUFFICIENT_SAMPLE remain source-stage verdicts and are no longer applicable because V0.1.1 passed.

If SURVIVES:
- do NOT call it a diamond;
- do NOT trade;
- do NOT open 2026;
- stop and require a new confirmatory freeze.

### 15. Governance
No main merge/change.
No trading/orders.
No wallets/account reads.
No private/authenticated exchange endpoints.
No exchange mutation/spending.
No post-outcome tuning.
No reuse to rescue other families.

### 16. Outcome-access declaration
At the time this freeze is committed, no historical market value from the pinned Development universe has been opened by this family.

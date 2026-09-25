# CMM-002 — FUNDING-CONDITIONED CROSS-MARKET DIVERGENCE
## PRE-OOS AUTHORITY V0.1

Status: FROZEN BEFORE ANY CMM-002 2025 OUTCOME ACCESS
Governing policy: ND-PROMOTION-POLICY-V3.0-FROZEN
Parent hypothesis-generation lab: CMM-001-V01
Parent terminal state: INSUFFICIENT_SAMPLE
Parent immutable closeout commit: 18c261dc7bd3f47086240b0435738837b2aad9d1

## 1. Why this is a NEW candidate
CMM-001 tested unconditional fading of extreme disagreement between BTC spot and a non-spot consensus state.

Its funding diagnostic was prospectively frozen as descriptive-only and produced strong heterogeneity:
- non-extreme funding |F_z| < 1.5: N=25, mean NET10 +50.1987 bps, PF 1.3513;
- extreme-negative funding: N=6, mean -329.5647 bps, PF 0.0232;
- extreme-positive funding: N=4, mean -106.5692 bps, PF 0.4703.

Those 2021-2024 observations are POST-HOC HYPOTHESIS-GENERATION for CMM-002.
They provide ZERO validation credit and may not be pooled into any CMM-002 promotion evidence.

CMM-002 asks a narrower mechanism question:
Does spot/non-spot disagreement revert only when perpetual-futures funding is NOT already in an extreme crowding/deleveraging regime?

## 2. Candidate identity
Candidate ID: CMM-002-V01
Primary family: RV — Relative Value / Convergence
Secondary family: CARRY / crowding state
Payoff shape: conditional convergence
Mechanism: when funding is extreme, spot/non-spot disagreement may be part of an active leverage/crowding regime rather than a temporary mispricing. When funding is non-extreme, the same disagreement may be more likely to close.

This mechanism was formulated AFTER observing the CMM-001 diagnostic. Therefore only untouched data after the CMM-001 development corpus can validate it.

## 3. Untouched validation block
ONLY authorized economic outcome block:
2025-01-01 through 2025-12-31.

Signals whose exact 72h exit would require any 2026 price are mechanically excluded before outcome access.

2026: LOCKED / NOT FETCHED.

No 2021-2024 CMM-002 return, PnL, PF or promotion statistic may be recomputed or claimed as validation evidence.

## 4. Parent state definition — unchanged
Decision frequency: one candidate decision per UTC calendar day.

Options window: 15:00:00 <= timestamp < 17:00:00 UTC.
Decision timestamp: 17:05 UTC.
BTC spot state: exact Binance Spot BTCUSDT 17:00 UTC hourly OPEN.
Entry: exact BTCUSDT 18:00 UTC hourly OPEN.
Exit: exact BTCUSDT 18:00 UTC hourly OPEN exactly 3 calendar days later.

Rates and stablecoin states use the same one-calendar-day information lag as CMM-001.

Options trade proxy is unchanged:
- Deribit BTC option trades only;
- 7 <= DTE <= 45;
- calls strike/index in [1.05, 1.20];
- puts strike/index in [0.80, 0.95];
- >=5 eligible calls and >=5 eligible puts;
- O_raw = -(median put IV - median call IV);
- this is a trade-implied skew proxy, not a quoted 25-delta risk reversal.

Raw core states unchanged:
S_raw(d) = ln(BTC17[d] / BTC17[d-7 calendar days]).
R_raw(d) = -(latest DGS2 dated <=d-1 minus five prior valid Treasury observations).
L_raw(d) = ln(stablecoin supply <=d-1 / stablecoin supply <=d-31).

Robust normalization unchanged:
exactly prior 180 valid observations, current excluded;
center = median;
scale = 1.4826 * MAD;
clip z to [-5,+5].

N(d) = median of available O_z, R_z, L_z requiring at least 2 of 3.
G(d) = S_z - N.

Parent gap threshold unchanged:
q95(d) = linear-interpolated expanding 95th percentile of ALL prior valid |G| values.
At least 180 prior valid G values required.
Parent gap condition: |G(d)| > q95(d).

Direction unchanged:
G>0 => SHORT-aligned.
G<0 => LONG-aligned.

## 5. NEW frozen funding condition
F_raw(d) = arithmetic mean of Binance BTCUSDT USD-M perpetual funding prints on calendar day d that are timestamped at or before 17:05 UTC.

F_z(d) uses exactly the prior 180 valid F_raw daily observations:
median center;
1.4826 * MAD scale;
current excluded;
clip to [-5,+5].

CMM-002 funding gate:
ABS(F_z(d)) < 1.5.

The threshold 1.5 is not claimed to have been independently discovered. It is explicitly inherited from the CMM-001 diagnostic that generated this new hypothesis.

A CMM-002 event requires BOTH:
1. parent gap condition |G| > expanding q95;
2. |F_z| < 1.5.

Cooldown:
72 hours between CMM-002 entries.
Only CMM-002-eligible events start the CMM-002 cooldown.

To avoid an artificial OOS-boundary reset, the runner must reconstruct candidate eligibility during 2024 WITHOUT computing 2024 CMM-002 outcomes and carry any live cooldown state across the 2025-01-01 boundary.

## 6. Frozen economic outcome
BASE round-trip cost = 10 bps.
STRESS diagnostic = 20 bps.
Primary horizon = exactly 72h.
No stop.
No target.
No leverage.
No alternate asset.
No direction flip.

gross_bps = direction * ((exit / entry) - 1) * 10000.
NET10 = gross_bps - 10.
STRESS20 = gross_bps - 20.

## 7. Source / integrity gate BEFORE 2025 outcomes
The CMM-002 runner MUST fail closed before computing any 2025 event return unless ALL are true:

1. Parent CMM-001 immutable daily-state ledger exists and its SHA256 is exactly:
   8c79b4287d5a0bc7ab263b856b56bded638d75e2ea14c25434156a4eb20909d8 applies to EVENT ledger; the daily-state ledger must be separately hashed and recorded before use.
2. Parent source report is readable and confirms 2025 and 2026 were LOCKED_NOT_FETCHED in CMM-001.
3. Binance Spot BTCUSDT 1h archives required for 2024-12 and 2025 pass provider SHA256 checksums.
4. Exact 17:00/18:00 hourly spot observations required by eligible 2025 dates have >=99.5% availability.
5. Deribit 2025 options requests have zero transport/parse errors, zero has_more truncation and valid O_raw coverage >=75%.
6. Binance funding monthly archives required for 2023-2025 pass provider SHA256 checksums, allowing a clean 180-day funding normalization and 2024 boundary-state reconstruction.
7. FRED DGS2 2024-2025 provides >=450 numeric observations.
8. DefiLlama aggregate stablecoin history 2024-2025 provides >=700 dated positive peggedUSD observations.
9. NO 2026 source or price is fetched.

Any failure => SOURCE_INADEQUATE / TECHNICAL_FAILURE, outside the tier ladder, with 2025 outcomes not opened.

## 8. Frozen 2025 OOS statistics
Report:
- N;
- mean/median NET10;
- PF NET10;
- positive fraction;
- mean STRESS20;
- largest single positive NET10 contribution to total positive NET10;
- 10,000 event-bootstrap resamples of mean NET10, seed 20260925;
- bootstrap P(mean<=0), p05, p50, p95.

Also report counts:
- parent gap-condition days;
- funding-gate pass/fail among those days;
- CMM-002 events after cooldown.

No unfiltered CMM-001 2025 return/PnL may be computed as a comparator.

## 9. Frozen adjudication
Minimum evaluable OOS sample:
N >= 8.

If N < 8:
INSUFFICIENT_SAMPLE. No scientific tier.

If N >= 8 and:
- mean NET10 > 0;
- PF NET10 > 1;
- largest single positive NET10 share <=50%;
then:
OOS_SUPPORTIVE / TIER3_HIGH_WATCHLIST.
Tier 2 is explicitly impossible from this single 2025 test because CMM-002 was generated post-hoc from the 2021-2024 CMM-001 diagnostic.

If N >= 8 and EITHER:
A. mean NET10 <= -10 bps AND PF <=0.90; OR
B. mean NET10 <0 AND PF<1 AND bootstrap p95 <0;
then:
TIER4_REJECTED for CMM-002-V01.

Otherwise:
OOS_MIXED / TIER3_WATCHLIST.

A supportive 2025 result authorizes only drafting a separate genuinely prospective forward-shadow authority beginning strictly after its freeze. It does not authorize 2026 historical backfill, Tier 2, micro-live or capital.

## 10. No rescue
After the first 2025 CMM-002 outcome is opened:
- no funding threshold change;
- no asymmetric positive/negative funding thresholds;
- no q95 change;
- no normalization-window change;
- no options DTE/moneyness/window change;
- no horizon/cost/direction change;
- no favorable 2025 subperiod selection;
- no event deletion;
- no BTC venue substitution;
- no 2026 historical opening to rescue the result.

## 11. Safety
Research only.
No live trading.
No orders.
No authenticated exchange mutation.
No wallet.
No alerts/webhooks.
No Render deployment.
No merge to main.

END OF CMM-002 PRE-OOS AUTHORITY V0.1

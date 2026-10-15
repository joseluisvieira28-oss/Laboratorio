# CMM-DRV-001 — DYNAMIC CROSS-MARKET RESOLUTION
## 2025 ONE-SHOT PROTECTED HOLDOUT AUTHORITY V0.1

Status: FROZEN BEFORE CMM-DRV-001 2025 OUTCOMES
Policy: ND-PROMOTION-POLICY-V3.0-FROZEN
Parent scientific state: CMM-001-V01 = INSUFFICIENT_SAMPLE
Parent exploratory map: CMM-RM-001 = HYPOTHESIS-GENERATION ONLY
New candidate identity: CMM-DRV-001-V01

## 1. Why this is a new hypothesis, not a rescue
CMM-001 tested an immediate 72-hour fade of an extreme cross-market state gap.
CMM-DRV-001 tests a materially different conditional mechanism:

1. observe an extreme gap;
2. do NOT trade immediately;
3. wait exactly one calendar day;
4. require evidence that the gap has already begun to close;
5. require that BTC spot, not the non-spot consensus, is the larger contributor to that first-day closure;
6. only then test continuation of the same spot adjustment over the following 48 hours.

CMM-001's verdict is immutable and cannot be upgraded by this child.

## 2. Holdout status
Authorized candidate-specific historical holdout: calendar year 2025 only.
This 2025 CMM-DRV-001 outcome has not been used in the CMM-001 or CMM-RM-001 calculations that generated this rule.

This is not claimed to be globally pristine market-blind evidence because other Crypto Lab families have used 2025 for unrelated hypotheses.
It is a one-shot candidate-specific holdout.

2026 remains LOCKED and must not be fetched for this run.
Any initial event whose frozen exit would require a 2026 price is excluded before outcomes.

## 3. State construction — unchanged parent semantics
The daily decision clock and raw state definitions remain exactly those of CMM-001:

- Options window: 15:00 <= timestamp < 17:00 UTC.
- State decision timestamp: 17:05 UTC.
- BTC spot state observation: exact Binance Spot BTCUSDT 17:00 UTC hourly OPEN.
- Rates and stablecoin inputs use one-calendar-day information lag.
- O_raw = negative of Deribit trade-implied OTM put-minus-call IV skew.
- S_raw = ln(BTC 17:00 open[d] / BTC 17:00 open[d-7]).
- R_raw = negative 5-valid-observation change in DGS2 using latest observation dated <=d-1.
- L_raw = ln(stablecoin supply lag[d] / lag[d-30]).
- Each S/O/R/L raw state is robust-normalized against exactly its prior 180 valid raw observations, current excluded, median/MAD*1.4826, clipped [-5,+5].
- N(d) = median of available O_z/R_z/L_z, requiring >=2 of 3.
- G(d) = S_z(d) - N(d).
- q95(d) = 95th percentile of all prior valid |G| values, current excluded.
- Initial extreme-gap trigger iff |G(d)| > q95(d).

The immutable parent daily-state ledger through the end of 2024 may be used only as prior state history for rolling normalization and q95 continuation. Parent event returns/PnL may not be used by this runner.

## 4. Initial event selection
One active candidate cycle at a time.

When no cycle is pending or active:
- earliest day d with a valid extreme-gap trigger becomes G0;
- direction is frozen from G0:
  - G0 > 0 => SHORT-aligned BTC;
  - G0 < 0 => LONG-aligned BTC;
- no trade occurs on day d.

The cycle remains locked until its confirmation decision and, if confirmed, its frozen exit. No overlapping trigger may replace it.

## 5. One-day dynamic confirmation
At day d+1, using the exact 17:05 state:

G1 = G(d+1).
The initial orientation sign is s = sign(G0).

Confirmation requires ALL:
1. G1 is valid and non-zero.
2. sign(G1) == sign(G0); a gap that already crossed zero is considered resolved and is not entered.
3. |G1| < |G0|; the gap has begun to shrink.
4. SC1 = s * (S_z(d) - S_z(d+1)) > 0.
5. NC1 = s * (N(d+1) - N(d)).
6. SC1 > NC1; spot is the larger contributor to first-day gap closure.

There is no additional optimized shrink threshold.
There is no funding/CFTC filter.

If confirmation fails, the cycle closes with NO_ENTRY and the next day may search for a new initial trigger.

## 6. Frozen market outcome
For a confirmed event:
- entry = exact Binance Spot BTCUSDT 18:00 UTC hourly OPEN on d+1;
- exit = exact Binance Spot BTCUSDT 18:00 UTC hourly OPEN on d+3;
- holding period after confirmation = 48 hours;
- direction remains the original G0 convergence direction;
- gross_bps = direction * ((exit/entry)-1) * 10000;
- BASE round-trip cost = 10 bps;
- STRESS diagnostic cost = 20 bps;
- no stop, target, leverage, alternate horizon or alternate asset.

## 7. Full source/integrity firewall — before outcome calculation
The runner MUST construct the complete 2025 state path and event identities before reading entry/exit prices into event PnL.

Required:
1. Binance Spot BTCUSDT 1h archives for 2024-12 plus 2025-01 through 2025-12, every provider CHECKSUM verified.
2. Binance 2025 microsecond timestamps are deterministically normalized to canonical milliseconds when required.
3. Exact required 17:00 and 18:00 observations >=99.5% available.
4. Deribit 15:00-17:00 daily option requests have zero request/parse errors and zero has_more truncation.
5. Valid O_raw coverage >=75% of eligible 2025 state days.
6. FRED DGS2 source readable with sufficient 2024-12/2025 numeric observations.
7. DefiLlama stablecoin source contains valid peggedUSD observations for all required lag calculations.
8. No 2026 source or price is fetched.
9. Parent daily-state warmup ledger hash/identity is preserved and no parent PnL column is read.

Failure before the firewall completes => SOURCE_INADEQUATE or TECHNICAL_FAILURE, not a market verdict.

## 8. Frozen reporting
Report:
- number of initial extreme-gap cycles;
- confirmation rate;
- number of entered trades;
- BASE NET10 mean, median and PF;
- positive fraction;
- STRESS20 mean and PF;
- largest single positive trade share of total positive BASE-net PnL;
- monthly counts and NET10 means;
- long/short counts;
- leave-one-trade-out minimum mean NET10;
- 10,000 event-bootstrap means, seed 20260925.

## 9. Sample adequacy and adjudication
Minimum entered trades for an economic verdict: N >= 8.

If N < 8:
- INSUFFICIENT_SAMPLE.

If N >= 8, classify only this new child:

OOS_SUPPORTIVE / TIER_3_HIGH_RESEARCH_CANDIDATE if ALL:
- mean NET10 > 0;
- PF NET10 > 1.0;
- positive fraction >= 50%;
- mean STRESS20 > 0;
- largest single positive BASE-net contribution <=50%.

OOS_CONTRADICTS if:
- mean NET10 < 0 AND PF NET10 < 1.0.

Otherwise:
- OOS_MIXED / TIER_3_LOW.

Even OOS_SUPPORTIVE cannot earn Tier 2 from this run alone because the rule was generated after inspecting the 2021-2024 parent resolution map.
A second genuinely independent block or prospective forward evidence is mandatory before any Tier-2 adjudication.

## 10. No rescue
After the first 2025 CMM-DRV outcome is opened:
- no confirmation rule change;
- no initial q95 change;
- no options window/DTE/moneyness change;
- no horizon or cost change;
- no component removal/weighting;
- no long-only/short-only rescue;
- no favorable month/subperiod selection;
- no event deletion;
- no 2026 rescue;
- no reinterpretation of NO_ENTRY cycles.

## 11. Safety
Research only.
No live trading.
No micro-live.
No orders.
No exchange mutation.
No wallets.
No alerts/webhooks.
No Render deployment.
No merge to main.

END OF AUTHORITY

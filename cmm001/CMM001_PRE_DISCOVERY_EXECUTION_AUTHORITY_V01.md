# CMM-001 — PRE-DISCOVERY EXECUTION AUTHORITY V0.1

Date: 2026-09-25
Status: FROZEN BEFORE MARKET OUTCOMES
Policy: ND-PROMOTION-POLICY-V3.0-FROZEN
Primary family: RV — Relative Value / Convergence
Secondary family: MACRO
Source-gate lineage: cross-market-mispricing-001-source-gate-v0.2
Source-gate base commit: d3920682d8d20130b49e10b424f7b67a182902ed
Source-gate run: 36107086445
Source-gate result: SOURCE_DATA_PASS — 5/5 core layers
Protected outcomes opened before this authority: FALSE

## 1. Scientific question
Does an extreme disagreement between BTC spot state and an independently constructed non-spot consensus state subsequently resolve through BTC moving against the prior spot/non-spot gap?

No market is presumed correct ex ante. "Mispricing" is shorthand for measurable disagreement, not a claim that spot is objectively wrong.

## 2. Candidate identity
Candidate ID: CMM-001-V01
Mechanism: rare state-event convergence.
Payoff shape: conditional convergence.
Failure mode: non-spot states are contemporaneous/followers, relationships are unstable, or the gap persists rather than closes.

## 3. Outcome firewall and temporal blocks
No outcome may be computed until all feature/source integrity gates in Section 10 pass.

Eligible outcome universe:
- Block A — DISCOVERY: 2021-07-01 through 2022-12-31.
- Block B — INDEPENDENT REPLICATION 1: 2023-01-01 through 2023-12-31.
- Block C — INDEPENDENT REPLICATION 2: 2024-01-01 through 2024-12-31.

All rules in this document are frozen before any A/B/C CMM-001 forward outcome is opened.
2025: LOCKED.
2026: LOCKED.
Any signal whose frozen 72h exit would require a 2025 price is mechanically excluded before outcomes.

## 4. Daily decision clock — point-in-time
One candidate decision per UTC calendar day.

Feature cut:
- Options window: 15:00:00 <= timestamp < 17:00:00 UTC on day d.
- Decision timestamp: 17:05 UTC on day d.
- BTC spot state observation: exact Binance Spot BTCUSDT 17:00 UTC hourly OPEN on day d. This is known before 17:05.
- Entry: exact Binance Spot BTCUSDT 18:00 UTC hourly OPEN on day d.
- Exit: exact Binance Spot BTCUSDT 18:00 UTC hourly OPEN on day d+3.

Rates and stablecoin states use a one-calendar-day information lag:
- at decision d, latest FRED DGS2 observation dated <= d-1, forward-filled across non-business days;
- at decision d, latest DefiLlama aggregate stablecoin observation dated <= d-1.

This conservative lag is part of the candidate identity.

## 5. Options implementation refinement — outcome-blind
The original source freeze described a planned daily trade-IV median. Before any outcome, it is refined to a fixed two-hour liquid-session snapshot to avoid unbounded full-day API volume and time-of-day composition drift.

Source: Deribit history.deribit.com public historical BTC option trades.
For every day d, request only 15:00–17:00 UTC with count=10,000, include_old=true.
If Deribit reports has_more=true for any queried day, that day is SOURCE_TRUNCATED and the run fails closed before outcomes; no silent sampling.

Eligible option trades:
- valid timestamp, instrument_name, index_price and iv;
- expiry parsed from canonical Deribit BTC-DDMMMYY-STRIKE-C/P instrument name;
- exact expiry timestamp = 08:00 UTC on expiry date;
- 7 <= DTE <= 45 at trade timestamp;
- calls: strike/index_price in [1.05, 1.20];
- puts: strike/index_price in [0.80, 0.95].

A daily options raw state is valid only with >=5 eligible call trades AND >=5 eligible put trades.
Raw skew = median(put IV) - median(call IV).
Oriented options state raw O_raw = -raw_skew, so positive means relatively more bullish / less downside-skewed.

This is explicitly a trade-implied skew proxy, NOT a quoted 25-delta risk reversal.

## 6. Frozen raw states
S_raw(d) = ln(BTC 17:00 open[d] / BTC 17:00 open[d-7 calendar days]).

R_raw(d) = -(Y_lag(d) - Y_5obs_before), where Y_lag(d) is the latest DGS2 observation dated <= d-1 and "5obs_before" means five prior valid Treasury observations in the original FRED sequence.

L_raw(d) = ln(StablecoinSupply_lag(d) / StablecoinSupply_lag(d-30 calendar days)).
StablecoinSupply is DefiLlama totalCirculatingUSD.peggedUSD.

F_raw(d), diagnostic only = arithmetic mean of Binance BTCUSDT USD-M funding prints timestamped on d and known by 17:05 UTC.
C_raw(d), diagnostic only = (LeveragedFundsLongAll - LeveragedFundsShortAll) / OpenInterestAll from official CFTC TFF Bitcoin CME code 133741. A Tuesday report becomes eligible only from the following Saturday 00:00 UTC.

## 7. Frozen robust normalization
For each raw core series S/O/R/L:
- current raw value is standardized against exactly the prior 180 valid observations of that same raw series;
- current observation is excluded from its own reference set;
- center = median(prior180);
- scale = 1.4826 * median(|x_i - center|);
- if scale <= 0 or non-finite, component is unavailable;
- z = (current-center)/scale, clipped to [-5,+5].

Funding diagnostic uses the same 180-valid-observation rule.
CFTC diagnostic uses prior 52 valid weekly observations where available.

## 8. Non-spot consensus and gap
N(d) = median of available O_z(d), R_z(d), L_z(d), requiring at least 2 of 3.
G(d) = S_z(d) - N(d).

No funding or CFTC value enters N(d), G(d), the trigger, direction or promotion decision.

## 9. Frozen trigger and direction
A day is eligible only after >=180 prior valid G observations exist.

Threshold q95(d) = linear-interpolated 95th percentile of ALL prior valid |G| values, excluding day d.
Trigger iff |G(d)| > q95(d).

Cooldown = 72 hours from frozen entry timestamp; earliest qualifying event wins. A new event may enter at exactly >=72h after the previous frozen entry.

Direction:
- G(d) > 0 => SHORT-aligned BTC.
- G(d) < 0 => LONG-aligned BTC.
- G(d) == 0 => no event.

No direction flip is permitted after outcomes.

## 10. Full-corpus source/integrity gates — before outcomes
The runner MUST build features first and MUST NOT compute event returns unless all pass:
1. Binance Spot hourly archives 2021-01 through 2024-12: provider SHA256 CHECKSUM pass for every required monthly ZIP.
2. Exact 17:00 state-open and 18:00 entry/exit hourly observations: >=99.5% candidate-day availability.
3. Deribit options window: zero request/parse errors, zero has_more truncation days, and valid O_raw coverage >=75% of candidate days 2021-07-01 through 2024-12-27.
4. FRED DGS2: >=900 numeric 2021-2024 observations.
5. DefiLlama aggregate stablecoin: >=1400 dated 2021-2024 observations and valid totalCirculatingUSD.peggedUSD.
6. Binance funding monthly archives 2021-2024: every required ZIP used for diagnostics passes provider SHA256.
7. CFTC official annual TFF 2021-2024 archives readable with Bitcoin CME code 133741 present.
8. 2025/2026 source/outcome prices are not fetched.

Failure before Section 10 completes => SOURCE_INADEQUATE / TECHNICAL_FAILURE, outside tier ladder.

## 11. Frozen economic outcome
For an eligible event e:
gross_bps(e) = direction * ((exit_price / entry_price) - 1) * 10000.
base_net_bps(e) = gross_bps(e) - 10.

Round-trip BASE cost = 10 bps.
No stress-cost path is used to select or rescue the candidate. A fixed 20 bps stress diagnostic is reported only:
stress_net_bps = gross_bps - 20.

Primary horizon = exactly 72h.
No stop, target, leverage, overlapping alternate horizon, or asset substitution.

## 12. Frozen statistics
Per block and pooled:
- N
- mean/median BASE net bps
- Profit Factor on BASE net event PnL
- positive-event fraction
- mean STRESS20 net bps
- largest single positive BASE-net event share of total positive BASE-net PnL.

Pooled diagnostics:
- leave-one-block-out mean BASE net and PF;
- 10,000 event bootstrap resamples of pooled BASE-net mean, seed 20260925;
- one-sided bootstrap p = fraction(resampled mean <= 0);
- 5th/50th/95th bootstrap mean percentiles.

Funding/CFTC strata are descriptive only and may not determine candidate promotion or rescue.

## 13. Mechanism-aware sample adequacy
CMM-001 is preclassified as a rare state-event convergence mechanism.
Adequate replicated corpus requires:
- pooled N >=30;
- each A/B/C block N >=8.

If not met => INSUFFICIENT_SAMPLE, outside Tier 4.

## 14. Frozen adjudication map under V3
Tier 2 / PROMOTED CANDIDATE / QUASE DIAMANTE only if ALL:
- Section 10 integrity passes;
- sample adequacy passes;
- A, B and C each BASE-net mean >0 and PF>1;
- pooled BASE-net mean >0 and PF>1;
- every leave-one-block-out pooled mean >0 and PF>1;
- largest pooled single positive BASE-net event share <=40%;
- exact expected sign is preserved;
- no rule/cost/event deletion/subperiod selection occurs.

Tier 4 / REJECTED for this exact candidate if sample adequacy passes and EITHER:
A) independent Block B or C has mean BASE net <= -10 bps AND PF <=0.90; OR
B) pooled mean BASE net <0, pooled PF<1, and the frozen 90% bootstrap upper bound (95th percentile) is <0.

Otherwise, with adequate sample and usable positive/mixed evidence => Tier 3 / WATCHLIST.

Tier 1 is impossible from this run alone.
No result authorizes live trading, micro-live, capital, orders, exchange mutation, alerts/webhooks, Render deployment or merge to main.

## 15. No rescue
After the first CMM-001 outcome is opened:
- no threshold change;
- no z-score window change;
- no options window/moneyness/DTE change;
- no horizon/cost change;
- no component deletion or weighting;
- no long-only/short-only selection;
- no favorable year/subperiod selection;
- no event deletion;
- no alternative BTC venue;
- no 2025/2026 opening to rescue a result.

END OF FROZEN AUTHORITY

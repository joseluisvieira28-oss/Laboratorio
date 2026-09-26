# REACTIVE-SHOCK-SCALP-005 — CPI/NFP POST-RELEASE MICROSTRUCTURE
## DISCOVERY MVE — PRE-OUTCOME FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: DISCOVERY ONLY

## Separation from NEWS SHOCK V0.3
This lab does NOT use:
- consensus;
- surprise = actual - consensus;
- Reuters consensus;
- mutable post-release consensus pages;
- any reopening of NEWS SHOCK LAB V0.3.

The prior V0.3 SOURCE_BLOCKED decision remains untouched.

This lab uses only:
1. official BLS scheduled release date/time;
2. historical Bybit BTCUSDT L2;
3. historical Bybit public trades;
4. information observable after release and before entry.

## Hypothesis
Scheduled CPI/NFP releases generate moves large enough that a causal reactive rule, entered after observing the first seconds of price/flow response, may preserve enough continuation to clear transaction costs.

## Deterministic Discovery event selection
Source authority:
U.S. Bureau of Labor Statistics annual release calendar for 2023.

Eligible rows:
- release name begins exactly with Consumer Price Index or Employment Situation;
- official release time = 08:30 AM America/New_York;
- event date after Bybit L2 archive availability begins.

MVE selection rule:
For each quarter of 2023, select the FIRST eligible CPI and FIRST eligible Employment Situation release in that quarter.

Expected MVE:
- 4 CPI events
- 4 NFP events
- 8 total events

No outcome-based event exclusions.

## Event time
T0 = official BLS 08:30 America/New_York converted to UTC with zoneinfo.

## Market source
Bybit linear BTCUSDT:
- historical L2 archive;
- public historical trades.

Historical event windows only.
No 2025 OOS.
No 2026 holdout.
No live trading.

## Causal observation windows
- W1 = T0 to T0+1s
- W2 = T0 to T0+2s
- W5 = T0 to T0+5s

Entry is at the first reconstructed BBO at or after the END of the observation window.
The move inside the observation window is never counted as future profit.

## Pre-release reference
Reference BBO/mid:
last valid reconstructed BBO strictly before T0.

## Trade-flow definition
Public trades with timestamp:
T0 <= trade_time < observation_end

Buy/sell notional:
size * price

normalized flow =
(buy_notional - sell_notional) / (buy_notional + sell_notional)

## Frozen reactive variants

### PRICE_W1
Direction = sign(mid_at_entry - pre_release_mid), observed after 1 second.

### FLOWPRICE_W1
Same as PRICE_W1, but normalized 0-1s trade flow must be nonzero and have the same sign as price displacement.

### FLOWPRICE_W2
Direction = sign(mid_at_2s_entry - pre_release_mid);
0-2s flow must be nonzero and same-sign.

### PERSISTENT_W5
Direction = sign(mid_at_5s_entry - pre_release_mid);
requires:
- normalized flow in 0-2s is nonzero;
- normalized flow in 2-5s is nonzero;
- both flow windows have same sign;
- that sign equals price displacement direction at 5s.

No magnitude thresholds.
No percentile search.
No event-type-specific parameter tuning.

## Future horizons after entry
- +5s
- +15s
- +30s
- +60s

## Economic outputs
For each variant/event/horizon:
- directional future mid return;
- executable BBO taker/taker gross;
- impossible perfect maker/maker BBO ceiling gross.

Cost overlays:
MEXC API:
- maker/maker 12 bps
- taker/taker 16 bps

Bybit VIP0 reference:
- maker/maker 4 bps
- taker/taker 11 bps

No slippage/adverse selection in ceiling calculations.

## MVE survival rule
A variant/horizon is a REACTIVE_CEILING_SURVIVOR only if:
- pooled resolved n >= 6;
- pooled mean MEXC perfect-maker net > 0;
- CPI mean MEXC perfect-maker net > 0 with n>=3;
- NFP mean MEXC perfect-maker net > 0 with n>=3.

This is a discovery screen only.
No OOS or holdout promotion is authorized from this MVE.

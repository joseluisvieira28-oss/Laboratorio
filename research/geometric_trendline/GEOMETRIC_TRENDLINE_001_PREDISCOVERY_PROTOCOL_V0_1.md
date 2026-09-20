# GEOMETRIC-TRENDLINE-001 — PRE-DISCOVERY PROTOCOL V0.1

Status: FROZEN BEFORE MARKET OUTCOME ACCESS
Authority: User instruction on 2026-09-20: "ATACA COM TUDO MANO , dispara tudo !"
Branch: geometric-trendline-v0.1
Parent pre-open closeout: 873647eabaa590d78b2f6224d81e8ab8e3a74007

## Scientific question
Does a causally constructed sloped price boundary, defined only by two already-confirmed pivots, contain directional information at the first subsequent interaction that is not merely a relabelled horizontal Donchian/range breakout?

## MVE identity
Lab: GEOMETRIC-TRENDLINE-001
MVE: GTL-THIRDTOUCH-REJECTION-1H-001
Primary family: TREND
Mathematical engine: projected two-anchor geometry / conditional directional response
Claim tested: an ascending support line should on average produce positive post-interaction response; a descending resistance line should on average produce negative post-interaction response.

## Canonical source
- Binance Data Vision official Spot BTCUSDT monthly 1m archives only.
- Discovery source window: 2021-01 through 2024-12.
- 2025 FORBIDDEN.
- 2026 FORBIDDEN.
- Each monthly ZIP must match its official .CHECKSUM SHA256 binding.
- No alternate vendor or silent gap filling.

## 1H bar construction
- UTC-aligned 1-hour bars aggregated from 1m source.
- An hour is valid only with exactly 60 distinct expected minute open-times.
- OHLC aggregation: open first minute, high max, low min, close last minute, volume sum.
- Any incomplete hour breaks state continuity.
- Pivots, line state and forward outcomes may not cross a continuity break.
- First 14 UTC days of 2021 are warmup only; no event may be accepted before 2021-01-15T00:00:00Z.

## Causal pivots
Window radius k=3 bars.
A pivot low at hour i requires low[i] strictly lower than the lows of all six hours i-3..i-1 and i+1..i+3.
A pivot high at hour i requires high[i] strictly higher than the highs of all six hours i-3..i-1 and i+1..i+3.
A pivot becomes known only at the CLOSE of hour i+3.
No code may expose or use a pivot before that confirmation timestamp.

## Anchor-pair eligibility
Support line:
- use two consecutive confirmed pivot lows;
- second pivot low > first pivot low;
- pivot-time separation >=12h and <=168h.

Resistance line:
- use two consecutive confirmed pivot highs;
- second pivot high < first pivot high;
- pivot-time separation >=12h and <=168h.

The line passes exactly through the two pivot prices as a function of integer UTC hours.
When a new eligible same-side pair confirms, it replaces the previous same-side line.
No search over alternative anchor pairs is permitted.

## Line life
- activation: second pivot confirmation close;
- maximum life: 336h after second pivot confirmation;
- one line may emit at most one accepted interaction event;
- expired or replaced lines never reactivate.

## Interaction band
Fixed tolerance = 10 basis points around the projected line price.
At hour t:
lower = line(t) * 0.999
upper = line(t) * 1.001

Support interaction candidate:
- previous valid hour close > previous projected upper band;
- current hour range intersects [lower, upper].

Resistance interaction candidate:
- previous valid hour close < previous projected lower band;
- current hour range intersects [lower, upper].

No requirement is imposed on the interaction-hour close relative to the line; the test is whether the pre-existing geometric boundary itself contains information.

## Invalidation before interaction
Support line invalidates if a completed valid hour closes below its projected lower band before its first accepted interaction.
Resistance line invalidates if a completed valid hour closes above its projected upper band before its first accepted interaction.
No rescue or reactivation.

## Ambiguity and overlap
- If support and resistance candidates occur on the same hour, classify AMBIGUOUS_BOTH_SIDES and accept neither.
- Primary response horizon = 6h.
- After any accepted event, suppress all new events for the next 6 completed valid hours.
- Forward response must remain in the same contiguous valid-hour segment; otherwise that event is outcome-ineligible.
- A line with an accepted event is consumed even if its 6h outcome later becomes unavailable because of a source gap.

## Direction and primary response
Support direction = +1.
Resistance direction = -1.
Event anchor price = close of the interaction hour.
Primary outcome price = close exactly 6 valid contiguous hours later.
PRIMARY_DIRECTIONAL_RESPONSE_BPS = direction * 10000 * (close_tplus6 / close_event - 1).

Secondary diagnostics, never promotion gates:
- +1h
- +3h
- +12h
- +24h
They use the same event anchor and same-side directional encoding and must not cross continuity breaks.

## Inference
- Unit of observation: accepted, outcome-eligible event.
- Primary point estimate: arithmetic mean of 6h directional response.
- Uncertainty: UTC-week clustered bootstrap, 10,000 resamples, deterministic seed 20260920.
- 95% percentile interval.
- Side-specific and calendar-year means are mandatory diagnostics.
- No winsorization, trimming, volatility filter, regime filter, long-only/short-only selection or post-outcome subgroup rescue.

## Sample viability gate
All must hold:
1. total outcome-eligible accepted events >=200;
2. support events >=75;
3. resistance events >=75;
4. at least 36 distinct UTC calendar months contain >=1 outcome-eligible event.

If source-valid data fail this gate: DISCOVERY_INSUFFICIENT_SAMPLE, not NO_EDGE.

## Frozen Discovery PASS gate
DISCOVERY_MECHANISM_PASS requires ALL:
1. sample viability PASS;
2. global mean 6h directional response > 0 bps;
3. global 95% bootstrap CI lower bound > 0 bps;
4. support mean > 0 bps;
5. resistance mean > 0 bps;
6. at least 3 of the 4 calendar-year means (2021, 2022, 2023, 2024) > 0 bps.

If sample viability passes but any item 2-6 fails:
DISCOVERY_FAIL_NO_PROMOTION.

## Interpretation boundary
A Discovery PASS would establish only that the frozen geometric interaction carries directional information in 2021-2024 BTCUSDT Spot under this exact rule.
It would NOT establish a tradable edge.
Fees, slippage, entry mechanics, stops, targets, leverage, position sizing, Sharpe, execution latency and PnL remain outside this MVE.

## Post-outcome firewall
No changes after outcome access to:
- pivot radius;
- anchor selection;
- 12h/168h separation;
- 336h lifetime;
- 10 bps tolerance;
- 1H timeframe;
- 6h primary horizon;
- sample gates;
- bootstrap method;
- pass gates;
- source;
- asset;
- direction mapping.

No 2025/2026 access.
No live trading.
No exchange mutation.
No wallets.
No orders.
No merge to main.

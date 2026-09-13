# Macro Shock Microstructure State Lab V0.1 — Non-Directional Prospective Measurement Contract

Status: **FROZEN PRE-OBSERVATION / NOT AUTHORIZED TO RUN / NO EDGE HYPOTHESIS**

## Purpose

Measure how scheduled U.S. macro announcements alter BTC/ETH microstructure state without forecasting return direction, testing profitability, or defining a trading rule.

This is a measurement contract only. It does not authorize target-outcome inspection, live trading, exchange mutation, a directional H02, MEXC access, main merge, or Render deployment.

`H02_STATUS = NOT_AUTHORIZED`

## Independent justification

The contract is grounded in independent pre-data evidence, not in favorable target outcomes:

1. Kroner, Mohammed & Vega (2026), *How Do Cryptocurrencies Price Economic News?*, SSRN 6447644, report sharp increases in cryptocurrency volatility, trading volume and bid-ask spreads around U.S. monetary-policy, inflation and labor-market announcements, with effects elevated for up to roughly 30 minutes. Their analysis also treats order flow as part of the price-discovery mechanism.
2. Yang & Wang (2026), *Scheduled FOMC statements and intraday macro event risk in cryptocurrency markets*, Finance Research Letters 101, 110073, document large first-hour post-FOMC increases in absolute returns and volume and use matched-week/hour controls. Their stated object is scheduled event risk rather than directional return predictability.

These sources justify measuring event-time liquidity/activity/volatility state. They do not justify a directional price rule.

## Prospective observation boundary

- No 2026 target observations are authorized by this contract.
- Earliest eligible observation date: **2027-01-01 UTC**.
- Any future run requires a separate explicit observation authorization after the official event calendar has been frozen.
- Only events strictly after that separate authorization may be captured as target observations.

## Venues and markets

Frozen scope:

- Binance Spot public market-data-only paths
  - BTCUSDT
  - ETHUSDT
- Coinbase Advanced Spot public market-data paths
  - BTC-USD
  - ETH-USD

No authenticated endpoint is permitted.

No synthetic USD/USDT FX conversion is permitted.

## Event families

Frozen event families:

- U.S. CPI
- U.S. Employment Situation / NFP
- scheduled FOMC statement releases

Event timestamps must come from official BLS/Federal Reserve calendars frozen before acquisition. UTC conversion must explicitly account for U.S. daylight-saving time.

No event family may be added or removed because observed market behavior looks favorable.

## Event-time windows

Independent rationale: the Fed staff paper reports abnormal volatility/volume/spread conditions for up to about 30 minutes; the FOMC study documents first-hour event risk.

Frozen non-directional windows:

- `PRE_BASELINE`: -30:00 to 00:00 minutes before the official release timestamp
- `PRIMARY_EVENT_STATE`: 00:00 to +30:00 minutes
- `RECOVERY_STATE`: +30:00 to +60:00 minutes

The primary scientific object is the state change in `PRIMARY_EVENT_STATE` relative to `PRE_BASELINE` and independently matched non-event controls.

`RECOVERY_STATE` is descriptive only and cannot alter any primary classification.

No directional post-event return label is defined.

## Raw capture

Capture and preserve raw public read-only stream messages with:

- exact venue;
- exact source-native symbol;
- exchange timestamps when supplied;
- collector wall-clock and monotonic timestamps;
- sequence/update identifiers where available;
- stable source order;
- raw-segment SHA-256;
- parse/reconstruction diagnostics.

Raw messages must be immutable after capture.

## Canonical BBO sampling

For state summaries only:

- canonical grid: **1-second UTC grid**;
- alignment: strictly backward as-of, latest valid synchronized observation at or before the grid timestamp;
- maximum allowed observation skew: **2 seconds**;
- if no valid observation exists within 2 seconds, the grid value is missing;
- no interpolation;
- no forward fill beyond the 2-second bound;
- no future observation may populate an earlier timestamp.

The 1-second grid and 2-second freshness bound are operational measurement choices, not trading thresholds. They are frozen before any target observation.

## Primary non-directional measurements

For each venue × symbol × event:

### Liquidity

- median spread_bps within each frozen window;
- 90th-percentile spread_bps within each frozen window;
- median best-bid quantity;
- median best-ask quantity;
- median absolute top-of-book imbalance, where imbalance is `(bid_qty - ask_qty)/(bid_qty + ask_qty)`.

Absolute imbalance is used to avoid directional interpretation.

### Trading activity

Per frozen window:

- trade count;
- base quantity traded;
- quote/notional quantity where source semantics support it;
- trades per minute;
- notional per minute.

### Volatility state

From valid 1-second mid prices:

- consecutive log returns;
- sum of squared log returns within each frozen window;
- square root of summed squared returns as the non-annualized realized-volatility descriptor.

No sign of return enters the primary measurement object.

### Flow magnitude

Only where source semantics unambiguously support aggressive-side classification:

- buy notional;
- sell notional;
- signed notional;
- total notional;
- **absolute normalized signed flow** = `abs(buy_notional - sell_notional) / total_notional` when total notional > 0.

Only the magnitude enters this non-directional contract. No flow sign may be mapped to future price direction.

## L2 depth

Raw synchronized L2 may be captured for provenance and future method work.

No level-count or price-distance depth aggregate is primary in V0.1 because such a band has not been independently justified tightly enough to freeze without tuning risk.

## Matched non-event controls

For each event timestamp and venue/symbol, candidate controls use the same weekday and same local U.S. release clock time at the following absolute weekly offsets:

- 7 days
- 14 days
- 21 days
- 28 days

Controls must:

- not overlap another frozen CPI/NFP/FOMC target event window;
- use the identical raw-capture, reconstruction, sampling and metric rules;
- satisfy the same data-quality gates;
- be selected without looking at metric values.

At least **3 valid matched controls** are required for an event × venue × symbol case to be considered resolved.

## Descriptive comparison objects

For each resolved case, compute only non-directional state ratios/differences such as:

- event median spread_bps / control median spread_bps;
- event realized-volatility descriptor / control descriptor;
- event trade intensity / control intensity;
- event absolute flow-magnitude descriptor / control descriptor where available.

No future return, continuation, reversal, PnL, win rate, profit factor, Sharpe ratio, stop, target, quantity or entry rule is permitted.

## Minimum prospective corpus

The contract targets one complete calendar year beginning no earlier than 2027-01-01, with the expected scheduled structure:

- at least 12 CPI releases;
- at least 12 NFP releases;
- at least 8 scheduled FOMC statements.

Minimum complete event dates before corpus-level scientific summary:

- CPI: 10
- NFP: 10
- FOMC: 6
- total distinct event dates: at least 26

These thresholds are calendar-coverage requirements, not edge-survival thresholds.

## Data-quality classification only

This contract has no `SURVIVES` / `NO_EDGE` outcome because no edge hypothesis exists.

Permitted terminal statuses:

- `PASS_MEASUREMENT_CORPUS`: integrity gates pass and minimum event coverage is met;
- `INSUFFICIENT_COVERAGE`: integrity is adequate but calendar/data coverage minimum is not met;
- `TECHNICAL_OR_DATA_FAILURE`: acquisition, reconstruction, timestamp, provenance, synchronization or control-construction integrity fails.

A PASS means the microstructure-state corpus is suitable for review. It does not mean a predictive edge exists.

## Primary analysis freeze

Before any target observation is authorized, implementation must deterministically produce:

1. raw immutable segment hashes;
2. reconstruction diagnostics;
3. 1-second backward-as-of BBO grid;
4. frozen window labels;
5. non-directional metric summaries;
6. matched-control eligibility and missingness receipts;
7. data-quality classification only.

No parameter may be changed after target observation because the resulting state ratios look weak or strong.

## Guards

Explicitly forbidden:

- accessing 2026 target observations under this contract;
- using MEXC Sep–Dec 2025;
- selecting only CPI/NFP/FOMC based on realized market results;
- choosing BTC vs ETH or Binance vs Coinbase because one looks better;
- changing the 1-second grid, 2-second skew, event windows, control offsets or minimum coverage after target observation;
- directional return labels;
- continuation/reversal hypotheses;
- PnL simulation or strategy scoring;
- authenticated exchange access;
- POST/PUT/PATCH/DELETE exchange routes;
- live or paper orders;
- merge to main;
- Render deployment.

## Execution authority

**NOT AUTHORIZED TO RUN.**

A future execution requires a separate explicit authorization that references:

- this exact frozen contract;
- a frozen official event calendar;
- the implementation fingerprint;
- the allowed future observation interval.

Until then, only offline/synthetic implementation and tests are authorized.

## Final boundary

`H02_STATUS = NOT_AUTHORIZED`

`TARGET_OUTCOMES = LOCKED`

Final decision: **NON-DIRECTIONAL MEASUREMENT CONTRACT FROZEN. IMPLEMENTATION MAY PROCEED OFFLINE/SYNTHETIC ONLY. STOP BEFORE TARGET OBSERVATION, DIRECTIONAL H02, OR TRADING LOGIC.**

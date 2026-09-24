# TV-FOOTPRINT-CALIBRATION-001 — Prospective Instrument Calibration Protocol

Status: FROZEN / RESEARCH-INSTRUMENT / NO EDGE CLAIM  
Branch: `tradingview-market-microscope-v0.1`

## Purpose

Determine whether TradingView Pine v6 volume-footprint measurements are sufficiently faithful to canonical Binance BTCUSDT aggressor-flow data to be used as a research sensor inside Crypto Lab.

This experiment does **not** test profitability, direction, entry timing, PnL, or promotion to an edge tier. A PASS grants only measurement authority for explicitly named future experiments.

The pre-existing `SRC_Crypto_Lab_Institutional_Flow_V1.pine` mirror is not modified by this work.

## Frozen context

- Lab ID: `TV-FOOTPRINT-CALIBRATION-001`
- Instrument: `BINANCE:BTCUSDT`
- Chart timeframe: 5 minutes
- Intrabar context: 1 minute
- Forward boundary: 2026-09-24 11:00:00 UTC
- TradingView footprint row size: 100 ticks
- Value Area: 70%
- Imbalance threshold: 300%
- Only closed 5-minute bars are evaluable.
- No pre-boundary observations can count toward the prospective gate.
- No parameter adjustment after seeing calibration outcomes. Any changed row size, timeframe, symbol, venue, VA definition, imbalance threshold, or aggregation rule requires a new calibration identity.

## Measurement definitions

### TradingView sensor

The canonical TradingView sensor is `tradingview/SRC_Crypto_Lab_Market_Microscope_V1.pine`.

Primary calibration fields:

- `TVFP_total_volume`
- `TVFP_buy_volume`
- `TVFP_sell_volume`
- `TVFP_delta`
- `TVFP_delta_pct`

Secondary descriptive fields include POC, VAH/VAL, imbalance-row counts, 1-minute path efficiency, 1-minute signed-volume approximation, volume z-score, and cross-asset returns. Secondary fields cannot rescue a failed primary calibration.

### Binance authority

Canonical comparison source: Binance spot BTCUSDT aggregate trades.

For each raw aggTrade:
- quantity = base-asset quantity;
- `isBuyerMaker = false` => aggressive buy quantity;
- `isBuyerMaker = true` => aggressive sell quantity.

For each UTC-aligned 5-minute bar:

`agg_buy_volume = sum(qty where isBuyerMaker=false)`

`agg_sell_volume = sum(qty where isBuyerMaker=true)`

`agg_delta = agg_buy_volume - agg_sell_volume`

`agg_delta_pct = agg_delta / agg_base_volume`

The canonical join key is UTC 5-minute bar-open timestamp.

## Minimum evidence

The first terminal calibration requires at least:

- 2,016 matched closed 5-minute bars (seven complete 24-hour days);
- at least 99% valid Binance bars in the frozen evaluation interval;
- no duplicated join keys;
- no timestamp reconstruction from price outcomes;
- no manual removal of difficult bars.

If the evidence minimum is not reached, state = `INSUFFICIENT_SAMPLE`, not PASS or FAIL.

## Frozen instrument gate

### PASS_STRONG

All must hold:

- matched-bar coverage >= 99%;
- median absolute relative total-volume error <= 1%;
- delta sign agreement >= 70% on non-zero comparable bars;
- Spearman correlation between TradingView delta and Binance aggressor delta >= 0.65;
- Pearson correlation >= 0.60.

Meaning: the footprint sensor may be used as a calibrated measurement feature in separately preregistered research. It still has **zero independent trading authority**.

### PASS_LIMITED

All must hold:

- matched-bar coverage >= 98%;
- median absolute relative total-volume error <= 2%;
- delta sign agreement >= 60%;
- Spearman correlation >= 0.50.

Meaning: the sensor may be used only as descriptive/context evidence. It cannot be treated as a substitute for exchange aggressor flow.

### FAIL_SENSOR

Any terminal sample that satisfies the minimum-evidence requirement but misses PASS_LIMITED.

Meaning: do not use TradingView footprint delta as an aggressor-flow proxy under this exact calibration identity.

## Anti-rescue rules

After outcomes are opened:

- no alternative footprint row size;
- no timeframe swap;
- no long-only/short-only subgroup;
- no volatility/session filter rescue;
- no deleting high-volume or news bars;
- no optimizing VA or imbalance settings;
- no switching from Pearson to another statistic to obtain a PASS;
- no redefining `isBuyerMaker`;
- no post-hoc lag shift.

Any materially different measurement design requires a new ID and prospective freeze.

## Governance

- Research only.
- No `strategy.*` order logic.
- No broker/exchange order route.
- TradingView alert payloads are measurement telemetry only.
- Alerts cannot grant trading authority.
- No main merge under this mission.
- No existing scientific verdict is modified.
- A calibration PASS is not an edge, candidate promotion, or execution authorization.

## External platform constraints

TradingView documents `request.footprint(ticks_per_row, va_percent, imbalance_percent)` as a single-request feature available to Premium and Ultimate accounts. TradingView footprint buy/sell classification is derived from intrabar price action; it is therefore deliberately treated here as a sensor to be calibrated rather than assumed equivalent to Binance aggressor-side flags.

Official references:
- https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
- https://www.tradingview.com/pine-script-docs/language/type-system/
- https://www.tradingview.com/pine-script-docs/concepts/alerts/

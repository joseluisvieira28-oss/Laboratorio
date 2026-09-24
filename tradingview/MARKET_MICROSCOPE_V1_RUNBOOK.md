# Market Microscope V1 — TradingView Runtime Runbook

## Runtime gate

The repository can statically audit the Pine source but cannot run TradingView's proprietary Pine compiler or footprint feed. Runtime acceptance therefore requires an unchanged compile inside TradingView.

TradingView documents footprint requests as available only on Premium and Ultimate plans. If the account cannot execute `request.footprint()`, classify the runtime state as `PLATFORM_PLAN_BLOCKED`. Do not replace the frozen footprint measurement with another proxy under the same calibration ID.

## TradingView setup

1. Open `BINANCE:BTCUSDT`.
2. Set chart timeframe to `5m`.
3. Open Pine Editor.
4. Paste the complete contents of `tradingview/SRC_Crypto_Lab_Market_Microscope_V1.pine`.
5. Compile and add to chart unchanged.
6. Require the dashboard to show:
   - Lab = `TV-FOOTPRINT-CALIBRATION-001`
   - Status = `INSTRUMENT CALIBRATION`
   - Footprint = `AVAILABLE`
   - Trading authority = `NONE`
7. Do not count observations with bar close before `2026-09-24 11:00:00 UTC`.

If Pine compilation fails, record the exact compiler message and line number. Syntax/API compatibility corrections may not alter symbol, timeframe, footprint parameters, forward boundary, measurement definitions, or calibration thresholds.

## Historical/export path

The indicator exposes stable Data Window/export columns:

- `TVFP_total_volume`
- `TVFP_buy_volume`
- `TVFP_sell_volume`
- `TVFP_delta`
- `TVFP_delta_pct`
- `TVFP_poc_mid`
- `TVFP_poc_migration_bps`
- `TVFP_vah`
- `TVFP_val`
- `TVFP_buy_imbalance_rows`
- `TVFP_sell_imbalance_rows`
- `LTF_intrabars`
- `LTF_path_efficiency`
- `LTF_signed_volume_pct`
- `CTX_volume_z`
- `CTX_bar_return_bps`
- cross-asset context fields.

Export chart data with indicator values included. Pre-boundary rows will be discarded by the calibration utility.

Normalize the export:

```bash
python tradingview/tv_footprint_calibration_001.py normalize-tv tradingview_export.csv --out tv_normalized.csv
```

## Binance authority path

Use official BTCUSDT spot aggTrades files. Unzip the CSV files and aggregate them with:

```bash
python tradingview/tv_footprint_calibration_001.py aggregate-binance BTCUSDT-aggTrades-*.csv --out binance_5m.csv
```

The tool freezes aggressive-side semantics:

- `isBuyerMaker=false` = aggressive buy
- `isBuyerMaker=true` = aggressive sell

No lag shifting or side inversion is permitted.

## Terminal calibration

After at least 2,016 matched forward bars:

```bash
python tradingview/tv_footprint_calibration_001.py calibrate --tv tv_normalized.csv --binance binance_5m.csv --out calibration_report.json
```

Valid terminal states:

- `PASS_STRONG`
- `PASS_LIMITED`
- `FAIL_SENSOR`

Before the evidence minimum is satisfied the only valid state is `INSUFFICIENT_SAMPLE`.

## Optional forward telemetry

The Pine script contains `alert()` measurement telemetry. Pine code cannot create a running TradingView alert by itself.

If forward telemetry is activated in TradingView:

- select `Any alert() function call`;
- preserve the script unchanged;
- route only to a research-ingest endpoint;
- never route directly to MEXC or another broker/exchange;
- treat every payload as an observation, not an order;
- persist raw payload + receive timestamp before transformation.

The payload intentionally contains no action, side, order type, quantity, leverage, wallet, or exchange-mutation instruction.

## Stop conditions

Stop and record a blocker instead of modifying science when:

- footprint data is unavailable;
- TradingView plan blocks footprint requests;
- compiler/API semantics differ materially;
- exported timestamps cannot be aligned exactly to UTC 5-minute bars;
- Binance source rows are incomplete;
- duplicate timestamps appear;
- the frozen minimum sample has not yet accrued.

No failed calibration may be rescued inside `TV-FOOTPRINT-CALIBRATION-001`.

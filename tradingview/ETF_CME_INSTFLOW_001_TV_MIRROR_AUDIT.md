# ETF-CME-INSTFLOW-001 — TradingView Mirror Audit

Status: RESEARCH-ONLY / PRE-COMPILE MIRROR
Branch: `tradingview-instflow-v0.1`

## Frozen mechanism preserved

- CFTC report: Legacy Futures Only.
- CFTC Bitcoin CME contract code: `133741`.
- Net non-commercial: `noncommercial_long - noncommercial_short`.
- Delta: current report net minus prior report net.
- Signal: `delta_net_noncommercial / open_interest_current`.
- Direction: LONG when signal > 0; SHORT when signal < 0; FLAT when signal = 0.
- Information-safe time: CFTC as-of date + 8 calendar days at 00:00 UTC.
- Entry: first BTCUSDT 00:00 UTC daily price at/after safe time.
- Exit: entry + 7 calendar days at 00:00 UTC.
- Outcome chart context: `BINANCE:BTCUSDT`, `1D`.
- 2025 OOS entry window: 2025-01-15 through 2025-12-24.
- Expected evaluable weeks: 50.
- Last frozen exit: 2025-12-31 00:00 UTC.
- 2026: hard locked in this visualization.

## TradingView source mapping

The script imports `TradingView/LibraryCOT/6` and requests:

1. Legacy / Futures Only / Noncommercial Positions / Long / All.
2. Legacy / Futures Only / Noncommercial Positions / Short / All.
3. Legacy / Futures Only / Open Interest / No direction / All.

TradingView documents COT as weekly data released Friday and based on Tuesday positions. The mirror delays the Friday-visible COT record by five 24/7 BTC daily bars so it cannot become actionable before the frozen Wednesday (`as-of + 8 days`) timestamp.

## Fail-closed controls

- Runtime error unless chart is `BINANCE:BTCUSDT`.
- Runtime error unless timeframe is `1D`.
- No `strategy.*` calls.
- No `alertcondition()` calls.
- No webhooks or execution hooks.
- No editable signal parameters.
- No thresholds, z-scores, winsorization, regime filters, alternate COT categories, subgroup selection, horizon change, or cost changes.
- Each authorized Wednesday requires non-missing COT inputs and a refreshed delayed COT record. Otherwise it is marked `COT FAIL` and the position is forced flat.
- Dashboard requires 50 authorized 2025 weeks and zero mirror faults for structural `PASS — 50/50`.
- All bars after 2025-12-31 are forced flat and dashboard states `2026 LOCKED — NO SIGNALS`.

## Verification still required inside TradingView

This repository-side audit cannot execute TradingView's Pine compiler or inspect the proprietary COT feed values. Before treating the visualization as an exact mirror, paste/add the script in TradingView and require all of the following:

1. Pine v6 compilation succeeds without edits to signal logic.
2. Chart is `BINANCE:BTCUSDT`, timeframe `1D`.
3. Dashboard shows `PASS — 50/50` and `Mirror faults = 0` after full 2025 history loads.
4. First eligible signal marker occurs on 2025-01-15.
5. Final eligible signal marker occurs on 2025-12-24.
6. No signal is exposed after 2025-12-31.

If any item fails, classify the TradingView mirror as `TECHNICAL/MIRROR FAILURE`; do not tune the mechanism to force agreement.

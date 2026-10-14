# BVOL7D — Operator TradingView UI source-discovery gate (2026-10-14)
Status: SEARCH_UI_NOT_FOUND / PUBLIC_METADATA_ONLY / FRESHNESS_UNVERIFIED / HISTORICAL_PARITY_UNPROVEN.

## Observed, not inferred
- Operator screenshot of TradingView symbol search typed exactly `BITMEX:BVOL7D`, filter Todos, interface says `Nenhum símbolo compatível com seu critério`. Therefore this user UI search did not resolve the specified symbol, as of screenshot. This is NOT proof of a permanent BitMEX delisting, nor that the historical BVOL series never existed, nor exactly when/why live data ceased.
- Public TradingView page https://www.tradingview.com/symbols/BVOL7D/ (also https://in.tradingview.com/symbols/BVOL7D/) still labels BVOL7D as BitMEX Bitcoin Historical Volatility Index, but webpage displayed `Market closed`, `No trades`, key data dashes, no shown fresh timestamp. A preexisting instrument metadata page does not prove present quote availability.
- Direct documented chart navigation from TradingView site's `Full chart` links points to https://www.tradingview.com/chart/?symbol=BITMEX%3ABVOL7D . Do not claim this opens data until operator shows the chart/date.
- Documented Pine `request.security()` `ignore_invalid_symbol` defaults false: when a requested symbol is **invalid** at runtime, the script normally raises an error, rather than quietly producing valid imaginary data. `gaps_off` can carry forward *missing source bars for valid symbols*; it cannot alone prove the script used stale data. See https://www.tradingview.com/pine-script-reference/v6/ and https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/ .

## Narrow no-money operator checks
1. Search `BVOL7D` without exchange prefix, with `Todos`, then optionally `Índices`, in TradingView; record list/no results. Do not substitute different index or synthetic series in original script.
2. Try canonical TradingView symbol overview https://www.tradingview.com/symbols/BVOL7D/ and `Full chart`; if a chart loads, show latest actual bar date/time and chart timeframe 4H or 1D.
3. If both fail, ask for screenshot of chart's strategy status: top-left warning/red exclamation or Pine runtime error; no need to reveal credentials or Pine code changes.
4. Freeze current candidate as SOURCE_BLOCKED_FOR_FRESHNESS pending independently sourced BitMEX published time-indexed BVOL data, market-venue alignment and historical-point-in-time investigation. Keep 4H/1D *retrospective* positive static cost ledger descriptive and intact; do not erase already verified CSV summaries or promote to forward/live.

## Research ethics
No symbol substitution or change to Pine model based on already-seen 2024–2026 outcomes. Any alternative volatility index or custom realized-vol formula is a **new** preregistered family requiring fresh forward validation, not a repair that inherits the 4H/1D returns. No main merge, trading, account access, spending or protected holdout opening.

# OPTIONS MULTI-ASSET — ETH / SOL / XRP SOURCE GATE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN BEFORE SOURCE CENSUS
Mode: SOURCE/DATA ONLY — NO SIGNAL, NO FORWARD RETURN, NO PNL

## Scope

This gate tests whether the free/public Deribit historical option-trade route can defensibly support new OPTIONS research hooks for ETH, SOL and XRP.

BTC is out of scope because the existing OPTIONS-SPOTPERP-001-V2.1 source lineage remains unchanged.

## Source route

Provider: Deribit public history API.
Route family: history.deribit.com / public get_last_trades_by_currency_and_time.
Kind: option.
No authentication.
No account endpoint.
No order endpoint.
No exchange mutation.

## Outcome firewall

The census MUST NOT:
- fetch Binance/MEXC outcome prices;
- compute skew;
- compute positions or signals;
- compute forward returns;
- compute PnL;
- rank assets by performance;
- access any protected scientific holdout outcome.

It may inspect only source-side option trade metadata needed to establish availability and parseability:
timestamp, trade_id, instrument_name, iv, index_price and instrument-derived expiry/strike/type.

## Census windows

ETH:
- target census: 2024-01-01 00:00:00 UTC through 2025-01-01 00:00:00 UTC exclusive.

SOL:
- discovery boundary search: 2024-03-01 through 2024-04-01.
- target census after first observed trade: through 2025-01-01 exclusive.

XRP:
- discovery boundary search: 2024-03-01 through 2024-04-01.
- target census after first observed trade: through 2025-01-01 exclusive.

The source gate may determine the first observed trade timestamp. That boundary discovery is source metadata, not an outcome optimization.

No 2025 option rows are requested by this gate.

## Completeness method

Top-level UTC day windows.
If Deribit reports has_more, split the time window recursively until the response is complete.
All returned trade IDs are globally de-duplicated.
All response windows are disjoint.

## Required audit facts

Per asset:
- source request completion;
- first and last observed trade timestamp;
- total rows;
- unique trade IDs;
- duplicate IDs;
- timestamp-boundary violations;
- instrument parse failures;
- rows missing required fields;
- non-finite/non-positive IV count;
- non-finite/non-positive index price count;
- calendar-month row counts;
- calendar-month distinct instrument counts;
- raw response SHA256 hashes or an equivalent page-hash manifest.

No option premium, return, edge metric or trade profitability is reported.

## Verdicts

SOURCE_GATE_PASS:
- complete requested census;
- at least one observed trade;
- zero timestamp-boundary violations;
- zero unparseable instrument names among rows carrying an instrument_name;
- no missing trade_id/timestamp/instrument_name structural fields;
- every full calendar month after the first full listed month through 2024-12 has option trades;
- invalid IV/index rows are explicitly counted and can be deterministically rejected by a later fail-closed adapter.

SOURCE_GATE_BLOCKED_TRANSPORT:
- the census cannot complete because the free/public source route is unavailable, throttled beyond retries, or otherwise transport-blocked.

SOURCE_GATE_FAIL_DATA:
- the census completes but structural coverage or parseability fails the requirements above.

## Scientific interpretation

SOURCE_GATE_PASS means only that the source is usable enough to design a prospectively frozen experiment.
It does not mean an edge exists.
It does not authorize a backtest.
It does not authorize live or micro-live execution.

After PASS, each asset still requires its own PRE-OUTCOME SCIENCE FREEZE before any outcome is opened.

## Governance

No main merge.
No live trading.
No orders.
No authenticated exchange mutation.
No post-outcome tuning.

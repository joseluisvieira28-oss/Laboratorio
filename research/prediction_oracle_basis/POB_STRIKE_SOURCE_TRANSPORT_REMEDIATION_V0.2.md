# POB-STRIKE-BINANCE-CFRTI-001 — SOURCE TRANSPORT REMEDIATION V0.2

Date: 2026-09-27
Status: FROZEN_TRANSPORT_ONLY / OUTCOME_BLIND
Parent authority: POB_STRIKE_PRE_SOURCE_AUTHORITY_V0.1.md

## Reason

Source probe V0.1 completed safely but returned POLYMARKET_SOURCE_POPULATION_UNAVAILABLE while an independently visible current Polymarket daily BTC threshold market exists.

This is treated as a source-enumeration/transport problem only, not a scientific result.

## Allowed remediation

Replace broad Polymarket keyset scanning with deterministic direct-slug discovery over a fixed forward calendar window:
- local calendar: America/New_York;
- dates: next 7 civil dates after the run date;
- slug template: bitcoin-above-on-<month>-<day>-<year>;
- retain only contracts whose resolution instant is strictly in the future at probe time.

No strike, quote, outcome, profitability or market-implied probability may be used to choose dates.

Kalshi KXBTCD enumeration, pair classification, rule semantics and all outcome firewalls remain unchanged.

## Forbidden

No matured outcomes.
No PnL.
No win rate.
No economic threshold search.
No selection by liquidity or price.
No contract-rule widening.
No live trading.
No main merge.

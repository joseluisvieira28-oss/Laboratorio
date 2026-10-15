# POB-HOURLY-STRIKE — STRIKE FIELD TRANSPORT FIX V0.2

Date: 2026-09-27
Status: FROZEN_TRANSPORT_ONLY / OUTCOME_BLIND
Parent: POB_HOURLY_STRIKE_PRE_SOURCE_AUTHORITY_V0.1.md

## Observed source schema

A source-only diagnostic of the future Polymarket 2PM ET event proved:
- event exists;
- market question is of the form "Bitcoin above 86,000 ...";
- explicit strike is also exposed as groupItemTitle = "86,000";
- rules explicitly identify Binance BTC/USDT 1h Close;
- market endDate is the resolution instant.

The V0.1 parser required a dollar sign when parsing the strike and therefore produced a false source-population negative.

## Authorized fix

Parse the explicit Polymarket strike deterministically from groupItemTitle first, falling back to question/title numeric parsing only when needed.

This changes source transport only.

Unchanged:
- matched time requirement;
- identical nominal strike requirement;
- reference/oracle classification;
- Kalshi 1-cent tie-boundary treatment;
- source window;
- outcome firewall;
- no economics;
- no orders/capital/exchange mutation;
- no main merge.

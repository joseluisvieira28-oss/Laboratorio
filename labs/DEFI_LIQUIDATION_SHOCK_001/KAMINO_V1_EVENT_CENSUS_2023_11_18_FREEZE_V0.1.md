# DEFI-LIQUIDATION-SHOCK-001 — KAMINO V1 DAILY CENSUS 2023-11-18 FREEZE V0.1

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Authority:
- program `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- V1 discriminator `b1479abce2854a37`
- closed first-success boundary `2023-11-17T14:48:24Z`

Frozen half-open window:
`[2023-11-18T00:00:00Z, 2023-11-19T00:00:00Z)`

This is the first full UTC day required by the prospectively frozen daily extension policy. It was selected before viewing this day's event classifications.

Source lineage:
- preserved parent run `35704794316`
- artifact `10686881756`
- artifact SHA256 `15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14`

Completeness hardening:
- the parent signature corpus must contain timestamps at or before the window start and at or after the window end;
- otherwise the day cannot be classified complete;
- zero selected program transactions is allowed only when the parent corpus brackets the complete day.

RAW rules remain identical to the first chunk:
- adjudicate every selected program signature;
- preserve failed attempts separately;
- exact program + V1 discriminator only;
- multiple exact matches, null RAW or metadata mismatch => fail closed;
- no instruction amount decoding;
- no market outcomes.

A valid day may contain zero realized events. That is a source-census fact, not an edge verdict.

Firewalls unchanged: prices=false; returns=false; pnl=false; direction=false; market_outcomes=false; event_size_threshold_tuning=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.

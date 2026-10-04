# MEXC-WTI-EVENT-SHOCK-001 — SOURCE GATE V1.2

Date: 2026-10-04
Status: SOURCE-ONLY / OUTCOMES CLOSED / RESEARCH-ONLY

## Mission

Determine whether MEXC `USOIL_USDT` (displayed as OIL(WTI)) plus the official U.S. EIA Weekly Petroleum Status Report schedule form a defensible public/no-auth source stack for a later event-conditioned WTI shock study.

## Product identity

MEXC public futures documentation identifies `USOIL_USDT` as the WTI-linked perpetual contract. MEXC renamed the UI ticker from `USOILUSDT` to OIL(WTI) in March 2026, while the public contract-detail route remains `USOIL_USDT`.

## Event authority

Primary event authority:
U.S. Energy Information Administration (EIA), Weekly Petroleum Status Report release schedule.

Standard release:
- Wednesday
- 10:30 a.m. U.S. Eastern Time
- holiday weeks may be delayed.

Known 2026 exceptions within the intended historical study period:
- 2026-02-19 Thursday 12:00 ET
- 2026-05-28 Thursday 12:00 ET
- 2026-09-10 Thursday 12:00 ET

The future 2026-10-15 exception is not part of this historical source gate.

## Allowed

Public/no-auth only:
- MEXC futures contract metadata;
- MEXC current index/ticker;
- MEXC small recent 1m kline structure probe;
- EIA public release-schedule HTML;
- SHA-256 preservation of all source payloads.

## Prohibited

- historical return scoring;
- historical WTI kline backtest;
- event-direction performance;
- inventory-surprise modeling;
- consensus/forecast data;
- private endpoints;
- account reads;
- credentials;
- wallets;
- orders;
- exchange mutation;
- live trading.

## PASS requirements

`MEXC_WTI_EIA_SOURCE_PASS` requires:

1. exact MEXC `USOIL_USDT` contract exists;
2. contract is publicly readable and WTI/OIL identity is unambiguous;
3. current public/no-auth index or ticker is positive;
4. public 1m contract klines are available;
5. EIA official schedule page is publicly retrievable;
6. schedule text proves normal Wednesday 10:30 ET release;
7. schedule text proves the relevant 2026 holiday exceptions;
8. zero historical outcomes opened.

A PASS authorizes only a separate pre-outcome freeze.

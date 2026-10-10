# BTC-OPTIONS-VRP-001 V2 — 30D HOLD-TO-EXPIRY LINEAR USDC SOURCE GATE FREEZE V0.1
Date: 2026-10-07
Status: PRE-SOURCE / NO ECONOMIC OUTCOMES

## Economic mechanism
The parent Discovery asks whether 30-day BTC implied volatility exceeds subsequent 30-day realized volatility.
A short approximately 30D straddle held to expiry is a more direct risk-transfer implementation of that phenomenon than the legacy seven-day buyback MVE.

This is a NEW execution MVE. It does not rewrite or rescue the closed seven-day implementations.

## MVE identity
ID: OVRP-USDC-30D-EXPIRY-003

Venue/product:
- Deribit BTC_USDC linear European options;
- 0.01 contract call + 0.01 contract put;
- same expiry, same strike;
- USDC Standard Margin;
- public unauthenticated source only for this gate.

## Candidate entry schedule
Historical candidate anchors are Thursdays 08:00 UTC.
For each anchor, source-only logic may search a fixed four-hour entry window [08:00,12:00 UTC).

Selection is deterministic and outcome-independent:
1. eligible option expiries: 25–35 DTE at anchor;
2. choose expiry minimizing absolute DTE distance from 30; earlier expiry tie-break;
3. same-strike call+put;
4. choose strike minimizing absolute log-moneyness to contemporaneous public index;
5. require a direction=SELL trade of amount >=0.01 in BOTH call and put during the frozen entry window;
6. first qualifying sell trade per leg is the execution proxy;
7. no exit option trade is required: options are held through settlement.

## Source windows
SOURCE GATE only, no economic values retained:
- 2025 calendar year, Thursdays 08:00–12:00 UTC;
- target 52/53 weekly anchors;
- 2026 is not used for historical performance and remains source-health/prospective only.

The probe may retain only:
- anchor;
- expiry/strike/instrument identity;
- trade timestamps;
- direction;
- amount;
- trade IDs;
- instrument metadata needed for DTE/min_trade_amount/settlement identity;
- source hashes.

The probe MUST NOT retain or print option trade price, settlement price, future BTC path, realized variance, PnL, return or expectancy.

## Source feasibility PASS
SOURCE_ENTRY_PASS if:
- >=24 independent 2025 weekly anchors have a deterministic same-strike call+put pair;
- both entry legs have qualifying SELL trade amount >=0.01;
- exact option expiry/strike/type identity and timestamps are defensible;
- required metadata coverage >=95%;
- zero 2026 economic values accessed.

The 24-anchor floor is source feasibility only, not statistical power and not a promotion sample minimum.
If it passes, a separate POWER GATE must derive actual required N before any economic outcome opens.

## Settlement source
Before outcome activation, a separate source-only step must prove authoritative Deribit BTC_USDC settlement/delivery-price semantics for every selected expiry and a defensible BTC_USDC perpetual hedge path if hedging is part of the economic MVE.

No settlement value or hedge return may be opened in this gate.

## Safety
No account/login.
No private/authenticated endpoint.
No order/cancel.
No wallet/payment.
No live trading.
No main merge.
No PnL/outcome.

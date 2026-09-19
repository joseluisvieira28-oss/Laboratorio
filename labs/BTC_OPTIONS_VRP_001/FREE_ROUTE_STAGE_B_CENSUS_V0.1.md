# BTC-OPTIONS-VRP-001 — FREE ROUTE STAGE B CENSUS V0.1

Date: 2026-09-19
Scope: free/near-free route screening, source-only.

## Historical routes still worth pursuing

1. **Cryptarbitrage free 2024H1 parquet** — highest-priority zero-cost payload recovery. Confirmed publicly described; direct object URL remains hidden behind the linked X post.
2. **BRC academic database** — published paper explicitly describes 8,444,664 Deribit order-book snapshots from 2021-04-01 to 2022-04-01 including BTC options and futures. Current BRC catalogue is ambiguous about the options subset. Account creation is described as free, but accreditation is required before database access. User action/identity submission is therefore a gate.
3. **optionsDX free sample** — strongest publicly visible schema match so far: timestamp, instrument, expiry, DTE, strike/right, bid/ask prices and sizes, OI, Greeks and IV. Public sample URL is known; byte retrieval remains runtime-blocked.
4. **CoinAPI signup credits** — potentially zero cash but requires user-controlled account/API key and verified payment method. Hold until public routes above are exhausted.

## Free routes screened out for the exact historical execution need

- Official Deribit expired-instrument mark history: terminal unavailable.
- Official Deribit historical trade archive / public GitHub downloaders: trade prints only; does not solve missing historical BBO.
- UWA Deribit Options Data (CC BY): all BTC option trades 2016-11-29 to 2020-10-05; valuable research data but outside the parent window and trade-based.
- Basis free options dashboard: current/live analytics; not a 2021-2024 historical BBO archive.
- Volar sandbox: free sample/current recent access only; its dense BTC archive is commercial.
- ChainVector historical options: trade history before its 2026 chain recording; not historical BBO for the target window.
- CryptoDataDownload: historical listings visible but payloads require Plus+; not zero-cost.
- Kaiko/Amberdata: structurally suitable commercial data, no zero-cost full historical route established in this screen.

## Commercial fallback observations — NOT a purchase decision

- Tardis remains the strongest proven schema/provider route. Public 2026 pricing is subscription-tier based and materially above a small one-off sample purchase; exact historical-age access must be checked before declaring a final cost.
- optionsDX advertises BTC Deribit monthly chain files 2021-06 through 2024-09 at EOD/30m/15m/5m/1m, with product pricing displayed as USD 0–50 depending on selection. The exact variation price needed for our future MVE is not yet proven.
- Volar advertises a dense BTC archive June 2021 through September 2024 and a full-archive annual plan, but it is held behind the paid lane until free routes are exhausted.

## Parallel zero-cost forward lane

A new source-only collector is frozen as `OVRP-FORWARD-PUBLIC-BBO-COLLECTOR-001`.

It uses only Deribit public unauthenticated endpoints and captures a deliberately broad envelope:
- BTC options 20–45 DTE;
- strikes within +/-25% of contemporaneous BTC index;
- top-of-book price and amount;
- mark IV/Greeks when returned;
- BTC-PERPETUAL BBO reference.

It computes no returns, signals, PnL or future realized variance. Its purpose is to start building our own clean forward BBO archive at zero vendor cost so the lab is less dependent on commercial history over time.

This forward lane does not rescue or alter the historical MVE and does not create a performance verdict.

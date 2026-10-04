# LIGHTER NVDA PORTABILITY — SOURCE GATE V0.1

Date: 2026-10-05
Status: SOURCE-ONLY / PRE-OUTCOME

Objective:
Determine whether Lighter exposes a public/free NVDA market with sufficient identity, fee, market-data and historical-data authority to justify a venue-portability test of the already frozen MEXC lead-lag mechanism.

No return, signal, win/loss or PnL may be computed in V0.1.

Public claims found during feasibility research:
- a third-party Lighter API measurement reported an NVDA tokenized-equity market and market fee fields of 0 maker / 0 taker;
- this is NOT accepted as execution authority until the public Lighter API itself is probed and the market is identified.

V0.1 may:
- query unauthenticated public Lighter endpoints;
- identify NVDA market IDs/symbols;
- record public fee fields;
- test public historical-candle availability;
- record order-book metadata without executing anything.

V0.1 may NOT:
- use authenticated/private endpoints;
- read an account;
- use a wallet;
- place/cancel/modify orders;
- compute historical strategy outcomes;
- trade live.

Any portability outcome study requires a separate pre-outcome freeze after this source gate passes.

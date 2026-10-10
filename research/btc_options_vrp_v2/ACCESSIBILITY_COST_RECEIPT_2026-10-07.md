# BTC-OPTIONS-VRP-001 V2 — ACCESSIBILITY & COST RECEIPT 2026-10-07

Status: **ACCESSIBILITY_UNRESOLVED / UNDERPOWERED_PRE**

## Current public source facts
Official Deribit inverse BTC options:
- contract size: 1 BTC;
- minimum order: 0.1 option contract;
- BTC margin currency;
- Standard Margin short-call and short-put formulas are mark-price/moneyness dependent.

Official Standard fee tier (Deribit fee schedule updated 2026-09-25):
- options maker/taker: 3 bps of underlying per contract, capped at 12.5% of option premium;
- perpetual/futures maker/taker: 1.5 / 3.5 bps.

Switzerland is not listed in Deribit's current Restricted Jurisdictions page, but account-specific onboarding/KYC/eligibility remains outside this source-only research mission.

## Current source-health snapshot
Canonical source-health run: 37659393449
Artifact: 11499987991
Artifact digest: sha256:28ef9900094ef8c21a56d90a6c0e3caf4e219997140a13d67e970bde9f73fee5
Snapshot index: ~83,175.83 USD
Selected V2 ATM pair in source-only audit:
- expiry DTE: ~22.60 days;
- strike: 83,000;
- call bid/ask: 0.036 / 0.037 BTC;
- call mark: 0.0367 BTC;
- put bid/ask: 0.030 / 0.031 BTC;
- put mark: 0.0309 BTC.

Using the official Standard Margin formulas:
- 0.1 short call IM ≈ 0.01867 BTC;
- 0.1 short put IM ≈ 0.01788 BTC;
- option-pair IM ≈ **0.03655 BTC** before the static BTC-PERPETUAL hedge margin.

At the contemporaneous index this is on the order of USD 3k, before account-specific buffers, hedge margin and future mark-price changes.

This is an illustrative causally-observed source calculation, NOT an account preflight and NOT permission to trade.

## Power correction
The old execution artifact has n=19 and stress-PnL SD ≈ 0.00229381 BTC per episode.

The first V2 plan incorrectly treated the old 1 BTC accounting denominator as if it were operator risk capital and concluded N_eff≈30 could be useful. That is withdrawn before any V2 forward outcome.

If current ~0.0367 BTC total initial-risk-capital scale is used only as a planning proxy, the weekly stress-return SD is roughly 6.2%. Distinguishing a 10% annual hurdle from a 20% annual design alternative would require on the order of **8,600 effective weekly observations** under a simple Gaussian planning approximation.

Therefore:
- the N=36 raw / N_eff=30 activation plan is REVOKED pre-outcome;
- no performance opening is authorized;
- the family remains UNDERPOWERED_PRE;
- the next legitimate attack is to redesign the execution question for substantially better information efficiency without using any new forward outcome.

## Scientific implication
The VRP phenomenon remains supported by the historical Discovery.
Executable profitability remains unproven.
Public forward BBO source is healthy.
The current weekly 7-day execution-confirmation design is not a practical powered route for modest capital-normalized returns.

No live trading, account reads, orders, wallets, payment, exchange mutation or main merge.

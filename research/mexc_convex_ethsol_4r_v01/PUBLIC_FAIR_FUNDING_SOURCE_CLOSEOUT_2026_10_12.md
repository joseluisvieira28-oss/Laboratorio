# MEXC-CONVEX-ETHSOL-4R-001 — PUBLIC FAIR/FUNDING SOURCE CLOSEOUT, 2026-10-12

## Verifiable final source verdict
**PUBLIC_FAIR_FUNDING_SOURCE_PASS_DIAGNOSTIC: 2/2 fixed ETH_USDT and SOL_USDT.**
**MAINTENANCE / ACCOUNT-SPECIFIC LIQUIDATION UNRESOLVED / PRIVATE READ NOT AUTHORIZED.**
**FUNDING CASHFLOW COMPLETE FOR FUTURE POSITION: NOT PROVEN.**
**REAL STRATEGY 4R EDGE: NOT TESTED / SCORABLE_ENTRIES=0 / NO TRADING AUTHORITY.**

No scientific strategy or existing frozen outcome changed. This addendum is source-only to `PHASE1_SCIENTIFIC_CLOSEOUT_2026_10_12.md`.

## Pre-observation authority and evidence
- Freeze `PRE_PUBLIC_FAIR_FUNDING_SOURCE_FREEZE_V0_1.md` authored at commit `56cef350b7ce49f063f65b466d0ed7c84b2217bf` BEFORE current live source calls.
- Public-only source probe commit `c37af03990f7466c4fddc354634b5897ae60ca3d`, workflow commit `a6b08948dd9c92d23aa6b71badc19253a8f5f4c4`.
- Authoritative GitHub Actions run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38286921976: SUCCESS as a SOURCE diagnostic, not a trade/backtest result.
- Immutable artifact `11764121138`, https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38286921976/artifacts/11764121138, ZIP digest `sha256:9842d4b6a55f99bd37e9417981f562fac0d73839e146af5972a99b29c74699a3`.

### One-shot public observed source fields
| Frozen instrument | Fair-price public observation age | Current funding metadata age | First funding history page |
|---|---:|---:|---:|
| ETH_USDT | 58 ms | 59 ms | 1000 valid settlement timestamps |
| SOL_USDT | 59 ms | 59 ms | 1000 valid settlement timestamps |

Both passed the frozen current clock/HTTP/schema/timestamp and history page source checks; no errors. Raw public response SHA256 receipts preserved in artifact. These figures are ages of a *single observed response* and do not establish 60-day feed continuity, funding completeness or live execution.

## Hard scientific limitations — cannot waive
- MEXC official public fairPrice and rate are observable, but exchange-specific margin maintenance/risk tiers can be account/position dependent. The documented risk-limit endpoint `/api/v1/private/account/risk_limit` requires permission, and the operator forbids private reads; it was NOT called. No liquidation stop threshold, usable leverage 5x/10x/20x or durable mark-based insolvency economics can be awarded.
- Current fundingRate is NOT future settled or realized funding. First 1000 past settlements are source coverage only; full entries-to-exits event completeness and size/cashflow require a future durable observer.
- This run did not score a market signal, trade or economic result. No real capital, orders, private endpoints, auth, balances, wallets, 2026 holdout opening, Render, trading bots, main merge or scientific tuning.
- Previous capital source-only PASS 2/2 (ETH 25.0625, SOL 21.490 nominal and planned stop-risk 1.041798 and 0.89329632 of a 500 USDT *imaginary* account) is unchanged. It is not real venue order/margin acceptance.

## Actionable next strictly prospective gate
A research-only continuous collector with durable single-writer receipts is required BEFORE any meaningful 4R forward decision:
1. Prove MEXC 1h closed-bar / Parent V5 signal parity, strict <=10min post-close decision, persisted decision before next contemporaneous ask/depth. No next-hour historical open fill.
2. Persistent public BID book/fair-price/funding settlement tracking >= every 30s, freshness <=2s with restart/dedup/gaps; STOP/TARGET/TIMEOUT with no guaranteed fills.
3. Verify maintenance/liquidation model without unauthorized account/private API; if impossible, keep leveraged economics `BLOCKED`. Do not substitute illustrative public maximum leverage for customer-specific tier.
4. Independent future `ACTIVATION_FREEZE` with tested collector code SHA, first future UTC boundary, funding/mark assumptions, freeze version, atomic no-overlap state and durable path; current design alone does NOT activate a shadow position.
5. Forward gate already frozen: >=100 independently credited event clusters, >=30 per ETH/SOL, >=12 UTC weeks, confidence and stress gates. No 2021–2025 or seen 2026 outcome rescue.

**Bottom line**: Public acquisition is no longer the main immediate blocker for these two assets at sampled instants. Continuous causal storage, exact execution/marks and *future independent economics* are.

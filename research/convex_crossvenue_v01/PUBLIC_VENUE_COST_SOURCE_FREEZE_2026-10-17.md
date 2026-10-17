# CRYPTO LAB — CONVEX CROSS-VENUE V0.1 — PUBLIC COST SOURCES & SCIENCE BOUNDARY

Frozen documentation date: **2026-10-17 UTC**. Read-only/offline. No exchange mutation, account reads, spending, deployment, main merge, forward opening, new historical backtest, modified V5 rule, or trading authority.

## Scope and prior evidence

Source parent: PR #216, research/convex-sol1h-bnb4h-economic-source-gates-2026-10-13; separate PR #217 native 5m and PR #242 ten Telegram-lane signal audit. Retain original Binance V5 indicator, timestamp semantics, long stop (-4%), nonlatched +5%-activated/12%-from-peak trail, no fixed TP, venue-independent classification **ONLY** as a hypothesis. Do not transplant 2023-25 Binance return percentages onto futures venue execution or 10x risk.

Historical parent portfolios (each separate 10,000 USDT paper account, 20% account-equity notional, 1x): SOL1h +59.388% BASE / 84 trades and BNB4h +27.378% BASE / 28 trades, in **three cumulative years**, under taker 8 bps/side, adverse slippage 2 bps/side, funding-market-open proxy. No independent OOS, no actual venue fills. Study is already observed retrospective data.

## Public base-tier fee source ledger — per fill, 2026-10-17 check

| Venue | Maker bps | Taker bps | Two-taker fee bps | Source and qualification |
|---|---:|---:|---:|---|
| MEXC Futures **API** | 6 | 8 | 16 | MEXC June 1 2026 change; promotions/app and anonymous contract-detail rates NOT applicable to a verified API rate; https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742 ; https://www.mexc.com/learn/article/mexc-fees-explained-complete-trading-futures-withdrawal-fees-guide/1 |
| Kraken Derivatives | 2 | 5 | 10 | 0-volume published base level (2026-10-08): https://support.kraken.com/articles/360048917612-fee-schedule |
| OKX Futures | 2 | 5 | 10 | regular level 1 illustrative official schedule (updated 2026-08-26): https://www.okx.com/cs/help/how-to-calculate-the-contract-transaction-fee |
| Bybit Global Futures | 2 | 5.5 | 11 | VIP0 published rate, region may differ: https://www.bybit.com/en/help-center/article/Service-Restricted-Countries ; https://www.bybitglobal.com/en/help-center/article/Trading-Fee-Structure |
| Bitget Futures | 2 | 6 | 12 | standard rates published Aug 20 2026: https://www.bitget.com/en-CA/support/articles/12560603892733 |

**Account entitlement, individual tier, symbol availability, derivative-country permission and order-via-API rate all remain UNKNOWN until authenticated by operator and independently documented.** Do not assume promotions, VIP, fee-discount token or maker fill. Neither Kraken nor other venue was authenticated or queried in this audit.

## Geographic/operational screening

- **Kraken Derivatives**: Switzerland absent from explicit published restricted jurisdiction list, BUT fully verified Kraken account and enabled Derivatives product remain a prerequisite. https://support.kraken.com/in/articles/360023786632-kraken-derivatives-eligibility . Check SOL/BNB perp contract listing, API permissions, margin collateral and any Swiss-specific account limitation with operator first.
- Bybit global: Switzerland not explicit on its global excluded list, but derivatives availability is product/account/region conditional. It is NOT evidence of entitlement. https://www.bybit.com/en/help-center/article/Service-Restricted-Countries
- OKX & Bitget: publicly quoted fee scenarios ONLY. Product-specific Switzerland eligibility remains unresolved; no deployment or customer-registration recommendation until confirmed.
- Kraken publishes a futures demo API guide but its July 7 2026 support article ALSO says the older demo endpoint was scheduled for decommissioning July 14, 2026. Do NOT assume the demo environment is operational without a verified fresh availability test. https://support.kraken.com/articles/360024809011-api-testing-environment-derivatives

## Illustrative algebra — NEVER reinterpret as net historical strategy PnL

Two-taker commission-only round trip: MEXC API 16 bps; Kraken 10; OKX 10; Bybit 11; Bitget 12. Kraken-vs-MEXC gap 6 bps per **round trip notional** (0.06%, 37.5% of MEXC commission); no guaranteed net equity benefit or improved win probability. Equal frozen illustration: 2bps adverse slip per side = 4bps total; **exclude spread and funding unless added explicitly**. Under that illustration MEXC 20bps, Kraken 14bps, OKX 14bps, Bybit 15bps, Bitget 16bps before spread/funding/impact. Parent PR #216 MEXC 12-snapshot median spread SOL 0.93127 bps, BNB 1.34571 bps *on 2026-10-13 only*. These figures MUST NOT be used as Kraken/Bybit spread or applied to a different timestamp.

A lower maker fee may be useless without a causal fill probability / queue position / market-adverse-selection model. A LIMIT maker entry changes original next-5m-open taker entry semantics, and therefore must be a **new prospective strategy branch**, not retroactive relief to V5. Never infer that another venue preserved Binance candle signal or funding.

## Mechanical research gate

Script: `research/convex_crossvenue_v01/venue_fee_gate.py`; tests: `test_venue_fee_gate.py`.
Run: `cd research/convex_crossvenue_v01 && python -m unittest discover -v && python venue_fee_gate.py`. Standard library, zero dependencies or network. The optional `--receipts-json` file must contain **sanitized boolean evidence only** (no account IDs, API keys, logs, prices, balances or secret paths). Missing receipts always NO_LIVE_GO. All actual trading authority is absent even if every receipt is true.

Ten independent gates: Swiss residency and Derivatives entitlement; account-specific Futures API maker/taker fee; SOL/BNB contract specs; point-in-time two-sided quotes and depth at entry and exit; Binance V5 signal-vs-execution venue prices; per-venue funding; immutable non-hindsight forward sample; prospective choice and independent testing of risk policy; exchange-hosted stop ACK/recovery; independently net-positive OOS gate.

## Prospective custody plan — NOT ACTIVATED

1. **Operator read-only source witness**: for each V07/V11/V12 lane at an actual newly completed signal close, retain exact Binance V5 source and closed-bar timestamp; for the immediately subsequent scheduled 5m OPEN, capture same-clock venue bid/ask, depth, tick, minimum and public funding; mark any stale/gapped sample INVALID, do not reconstruct after the fact.
2. **Venue execution shadow**: exact-side hypothetical taker executable depth, instrument sizing and quote-age, FX/collateral, expected fee/funding and next causal quoted exit; preserve data-before-outcome cryptographic integrity. Different entries and maker scenarios are separately frozen experiments and NEVER mixed with original parent.
3. **Compare market-venue basis**: predeclare allowed Binance-vs-venue price deviation, quote staleness, invalid source episodes, minimum sample and stress assumptions BEFORE observing eligible market outcomes. No changing boundaries after the data.
4. **Stop and OOS**: original trailing can weaken, 9/77 BTC CONVEX closed trades actually experienced weakened stop (PR #213), and production stop-ACK is unproven (PR #234); no exchange execution until prospective policy + broker ACK, idempotent recovery, fail-closed reconciliation and independent economic gate are separately demonstrated. Default should remain read-only.
5. **Separate risk pool**: SOL 5m/1h/4h/30m simultaneous LONG alerts can represent one correlated exposure. Do not count as four independent trades; collapse overlapping signal families and enforce a single-symbol exposure model for observational risk tests.

Frozen science and 2026 holdout protected. **NO LIVE GO.**

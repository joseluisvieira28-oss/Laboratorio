# KRAKEN — SOL/BNB CONTRACT PRESENCE & THIN-LIQUIDITY SCREEN (17 OCT 2026)

Independent website-only research, no authenticated APIs, no direct order-book API, no account reads, no orders. **These public screen values are ephemeral and NOT a causal, synchronous, verified executable quote.**

## What the official market pages actually show

- Kraken Pro SOL/USD Perpetual exists: https://www.kraken.com/features/futures/solana/usd . Page captured by public search with 2026-10-17 03:18 AM market-stat timestamp: 24h volume ~62.6 million USD, open interest ~24.1 million USD, marker of available market (but not account entitlement).
- Kraken Pro BNB/USD Perpetual exists: https://www.kraken.com/features/futures/bnb/usd and https://www.kraken.com/features/futures/bnb/usdt . BNB/USDT page 2026-10-17 03:08 AM market-stat timestamp showed approximately 764k USD 24h volume and 8m USD open interest.
- Near-time indicative SOL volume / BNB volume was about 82:1 (62.6m / .764m). This is **NOT** a matched orderbook test, not a fair exchange-to-exchange liquidity comparison, not a modelled execution cost and not a guarantee of liquidity at an entry/forced stop. It is a **WARNING** against assuming BNB4h can be moved just because taker fees are lower.
- The product marketing market pages also displayed **Fees -0.006% / +0.02%**, while the generic published no-volume Kraken Derivatives fee schedule (updated 2026-10-08) is maker +0.02%, taker +0.05%: https://support.kraken.com/articles/360048917612-fee-schedule . This unresolved difference could reflect market-specific promotion/display, account/tier details, or other conditions. The cross-venue script deliberately keeps the documented **generic base** 2bps maker, 5bps taker and MUST NOT silently substitute -0.6bps maker/2bps taker. Account-specific effective API fee and contract-specific rate remain UNKNOWN.
- Official Kraken Derivatives geographical restriction list does not list Switzerland, but an individual verified Swiss account's derivatives permission remains UNVERIFIED: https://support.kraken.com/in/articles/360023786632-kraken-derivatives-eligibility .

## Operational consequence

SOL1h is the first **venue-source-screen research candidate** on Kraken, not a live position candidate. BNB4h remains an economically interesting Binance historical hypothesis but its Kraken route must pass an independent, time-matched two-sided book depth and funding comparison versus MEXC/OKX. There is no sound basis yet to say Kraken is the cheapest **all-in** BNB route.

### Missing evidence

- Authoritative instrument-specific Kraken USD / collateral / contract identifier / tick/lot/min order check; no guessing from marketing page.
- 10+ actual time-stamped Kraken SOL and BNB order-book snapshots at separately frozen intervals; both ASK and BID sizes, executable impact for 100 USD **and** risk-exit size, request transport times, public raw content hash.
- Comparable contemporaneous MEXC/OKX two-sided books, identical side/size and time, 2026 source, separate rejection/latency and signed funding.
- First genuine future V5 signal event with Binance candle evidence, venue executable quotes at its causal entry time, and an immutable invalid/missed counter.
- Native broker stop and restart reconciliation proof before any capital authority.

**Verdict: MARKET EXISTENCE PUBLICLY REPORTED / BNB LIQUIDITY CAUTION / ACCOUNT RATE AND EXECUTION UNVERIFIED / NO LIVE GO.**

# PRIOR ART / ANTI-DUPLICATION AUDIT V0.1

Date: 2026-09-24
Purpose: prevent the lab from relabelling established effects as a new mine.

## Established / already materially explored outside this repo

### Spot vs futures / perp price discovery
High-frequency literature already studies BTC price discovery across spot and futures/perpetual venues, including asynchronous-data methods and one-second sampling. Therefore a generic "futures leads spot" hypothesis is NOT novel enough for this lab.

Key references:
- Price discovery in bitcoin spot and futures markets, Journal of International Money and Finance (2025).
- Price Discovery in Bitcoin Spot or Futures? The Jury Is Out, Journal of Futures Markets (2025).

### Options as informed flow
Published work reports evidence that large Deribit option orders can contain information around news/attention events. Therefore "option traders are informed" is not a sufficient hypothesis by itself.

Reference:
- Are Bitcoin option traders speculative or informed? Finance Research Letters (2024).

### Options expiry / gamma
Recent work studies Deribit BTC option expiration, gamma exposure and intraday reversals. This repo also already has multiple options-expiry/gamma branches. Do not reopen as a generic mine.

Reference:
- Bitcoin option expiration, gamma exposure, and intraday price reversals (2026).

### DEX / mempool priority fees
Research documents that high-fee DEX trades and mempool jump-bidding can be associated with informed trading / price discovery. Therefore "high gas means informed" is prior art, not a new edge.

Reference:
- Price Discovery on Decentralized Exchanges, Capponi, Jia, Yu (rev. 2025).

### Stablecoin transfers and BTC
Large stablecoin transfers have been studied for BTC return/volume effects. Therefore generic transfer-event studies are prior art.

Reference:
- The impact of transparent money flows: Effects of stablecoin transfers on the returns and trading volume of Bitcoin (2021).

### Polymarket <-> Binance HFT
OpenMarket (2026) provides a synchronized public BTC/Polymarket corpus and reports a null out-of-sample forecasting result for a 43-feature microstructure model. It also documents clock-offset ambiguity and a synchronization-free Binance->Polymarket response lag.

Reference:
- OpenMarket: A Synchronized Polymarket-Binance Dataset for High-Frequency Prediction-Market Research, arXiv:2607.26245.
- Public source tag v0.5.2; dataset v0.4.3-unified.

Implication:
Do not build a clone of the 43-feature predictive model. OpenMarket can be used as a methods validation / negative-control corpus, with exact version pinning.

## Research space that remains distinct enough to justify this lab

1. Multi-surface state-transition graph:
   OPTIONS_STATE -> PERP_STATE -> MICROSTRUCTURE_STATE -> SPOT_STATE,
   with conditional paths rather than a single unconditional lead-lag coefficient.

2. Incremental information:
   test whether upstream state transitions add information after contemporaneous BTC returns and known price-discovery relationships are controlled.

3. Liquidation convexity + oracle distance:
   model the non-linear amount of collateral that becomes liquidatable as oracle prices cross thresholds, then test interaction with CEX crowding/book depletion.

4. Cross-chain liquidity migration:
   distinguish stablecoin issuance/transfer level from directional movement between chains and subsequent venue-specific liquidity/OI changes.

5. Mempool -> CEX/DEX propagation:
   not "fees predict price", but whether classified pending state-changing transactions produce measurable downstream state transitions before block inclusion / CEX repricing. FORWARD_ONLY unless a defensible historical mempool corpus is found.

## Nulls that must be accepted, not rescued

- Generic futures-leading-spot result.
- Generic options-flow correlation with BTC.
- Generic stablecoin-transfer event effect.
- Generic Polymarket-vs-Binance microstructure model.
- Any sub-second cross-venue lead that disappears under clock-offset/jitter sensitivity.

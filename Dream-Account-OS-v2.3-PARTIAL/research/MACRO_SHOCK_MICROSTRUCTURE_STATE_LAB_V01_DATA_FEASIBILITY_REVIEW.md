# Macro Shock Microstructure State Lab V0.1 — Data Feasibility Review

Status: RESEARCH REVIEW ONLY — NO DIRECTIONAL HYPOTHESIS AUTHORIZED
Date: 2026-09-12
Branch: dream-account-phase-b-signal-research-v0.1

## Executive finding

The strongest externally supported mechanism is not a stable directional return rule. It is a temporary deterioration/reconfiguration of market microstructure around scheduled macro announcements: wider spreads, lower or unstable depth, higher volatility, higher trading intensity, and elevated order-flow price impact for roughly the first 30 minutes after the release.

The current Binance public historical Spot archive is suitable for trades/aggTrades/klines with checksums, but it does not provide a complete public historical Spot L2 archive sufficient to reconstruct historical spread/depth/refill dynamics across prior years. Public Spot REST/WebSocket endpoints provide current/read-only market depth and BBO, not a complete historical L2 archive.

Therefore, the scientifically clean paths are:

1. Prospectively collect read-only Spot L2/BBO/trades from exchange public market-data WebSockets going forward; or
2. Use an archival market-data vendor with documented capture/reconstruction methodology (for example Tardis or Kaiko) only after a separate provenance/coverage gate.

A third path — attempting to infer historical depth from klines or aggTrades — is rejected because it cannot recover the missing state of the order book.

## Literature synthesis

### Crypto-specific evidence

Kroner, Mohammed & Vega (2026), “How Do Cryptocurrencies Price Economic News?” reports that crypto volatility, trading volume and bid-ask spreads rise sharply at U.S. monetary-policy, inflation and labor-market announcement times and remain elevated for up to roughly 30 minutes. The paper also reports that order-flow price impact is consistent with an important role in crypto price discovery.

Yang & Wang (2026), “Scheduled FOMC statements and intraday macro event risk in cryptocurrency markets,” finds large increases in BTC/ETH absolute returns and volume in the post-statement hour, with robustness across matched controls and a second venue. This supports scheduled event-risk timing, not a directional return rule.

Anastasopoulos et al. (2026), “Order flow and cryptocurrency returns,” finds that aggregate world order flow can predict crypto returns at daily/weekly horizons, especially after separating transitory reversal from permanent components. This is supportive of order flow as an information variable in general, but it does not validate the already-tested event-window continuation rule from MSM V0.1.

### Traditional-market microstructure evidence

Order-book research around scheduled macro news consistently documents wider spreads, reduced/unstable depth, elevated volatility and more aggressive order submission near releases. Some studies find that depth is among the most responsive LOB variables and that information exists beyond the best quotes. These mechanisms justify measuring liquidity-state dynamics directly rather than using returns alone.

## Data-source feasibility

### Binance official public data

Binance Public Data / Data Vision provides historical Spot aggTrades and klines with daily/monthly archives and CHECKSUM files. Binance also exposes read-only Spot market-data REST/WebSocket endpoints including depth and bookTicker.

Limitation: the public historical Spot archive does not provide a complete tick-level historical L2 order-book dataset sufficient for reconstructing old spread/depth/refill states.

Conclusion: excellent provenance for trades/aggTrades/klines; insufficient by itself for historical L2 microstructure reconstruction.

### Tardis

Tardis documents historical tick-level trades, incremental L2 updates, order-book snapshots and quotes across exchanges, including Binance Spot and Coinbase. For Binance Spot it documents top-1000 initial snapshot support plus full incremental depth updates at 100 ms, reconstructed from captured exchange feeds with documented snapshot/reconnect behavior.

Scientific use would require a separate provenance/coverage validation before any outcome study.

### Kaiko

Kaiko documents backdated tick-level full order-book bids/asks for CeFi spot markets with daily files and exchange/collection timestamps depending on venue. Scientific use would similarly require a separate provenance/coverage validation.

### Coinbase

Coinbase public WebSocket Level2 provides a snapshot plus all updates and can support prospective collection. It is attractive as a second venue for cross-venue price-discovery timing, but historical L2 backfill still requires an archive/provider or a prospectively maintained collector.

## Recommended measurement families

Priority order:

1. Spread shock and recovery
   - quoted spread in bps vs matched controls
   - time-to-recover to pre-event/control baseline
   - BBO update intensity

2. Depth depletion and refill
   - depth within fixed bps bands around mid
   - imbalance by depth band
   - time-to-refill after initial depletion

3. Volatility expansion and decay
   - realized volatility at fixed post-release intervals
   - decay half-life relative to controls

4. Trade and order-flow intensity
   - trade count
   - signed/aggressive notional
   - price impact per unit signed flow

5. Cross-venue price discovery
   - Binance vs Coinbase timestamped return/BBO innovations
   - lead-lag measured only with synchronized clocks and fixed pre-specified intervals

6. Execution-state proxies
   - simulated market-order cost against contemporaneous book
   - adverse-selection proxy after hypothetical passive fill
   - no claim of executable strategy until fees, latency and fill mechanics are separately validated

## Scientific guardrails

- No H02 directional rule is authorized by this review.
- No subgroup seen in MSM V0.1 may be promoted to a new hypothesis from the holdout outcome.
- No historical L2 state may be inferred from OHLC/aggTrade data.
- No vendor dataset may be used before provenance, coverage, timestamp and gap rules are frozen.
- No live trading or exchange mutation.
- Read-only public market-data collection is scientifically distinct from trading authorization.
- Any future predictive hypothesis must be frozen before its untouched evaluation sample is observed.

## Recommended next gate

`MICROSTRUCTURE_DATA_SOURCE_AND_PROVENANCE_GATE_V0.1`

The gate should compare two routes before any new hypothesis is opened:

A. Prospective read-only collection from Binance Spot + Coinbase Level2/BBO/trades.
B. Historical archival provider (Tardis or Kaiko) with a small provenance-only sample that must not be used to select predictive parameters.

The gate should score:
- timestamp semantics and clock precision
- snapshot + incremental reconstruction method
- gap/reconnect behavior
- checksum/hashability and immutable storage
- symbol/venue coverage
- event-window completeness
- latency/collection timestamp vs exchange timestamp
- licensing/retention constraints
- reproducibility
- cost

Preferred scientific default if budget permits waiting: prospective collection, because it creates truly untouched microstructure data and minimizes retrospective provider-selection bias.

## Key sources

- Kroner, Mohammed & Vega (2026), How Do Cryptocurrencies Price Economic News?, SSRN 6447644 / Federal Reserve authors.
- Yang & Wang (2026), Scheduled FOMC statements and intraday macro event risk in cryptocurrency markets, Finance Research Letters 101, 110073.
- Anastasopoulos, Gradojevic, Liu, Maynard & Tsiakas (2026), Order flow and cryptocurrency returns, Journal of Financial Markets 79, 101047.
- Binance Public Data README and Spot market-data-only documentation.
- Tardis historical data documentation.
- Kaiko Level-2 bids/asks documentation.
- Coinbase Exchange WebSocket Level2 documentation.

## Decision

`DO_NOT_OPEN_H02_YET`

Proceed first to the data-source/provenance gate. If clean microstructure state data can be obtained prospectively or from a fully audited archive, then freeze one mechanism-level hypothesis before evaluating outcomes.

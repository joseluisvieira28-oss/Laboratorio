# CRYPTO LAB — YOUTUBE MECHANISM MINE / SOURCE & NON-DUPLICATION GATE V0.1

Date: 2026-10-09
Authority: RESEARCH_ONLY / PRE-OUTCOME / NO CANDIDATE PROMOTION
Purpose: examine educational channels as *idea origination*, not proof that a strategy is profitable.

## Source selection (direct source evidence)
1. **Robot Wealth (Kris Longmore)** — https://www.youtube.com/@robotwealth
   - Why: explicitly advocates mechanism-first research ("who is on the other side and why are they paying?"), over optimized backtests. Public strategy index https://robotwealth.com/index-of-strategies/ includes crypto perp basis, Hyperliquid funding/carry, short-term crypto reversal, momentum and systematic tools.
   - Caveat: several detailed research notebooks/webinars are RW Pro membership materials, not demonstrated public YouTube instructions or validated trade records. Do not claim to have watched each video.
   - Duplication gate: `funding-cash-carry-v0.1`, `funding-dispersion-deltaneutral-v0.1`, `cross-venue-funding-basis-p0f-final-attack-v0.6`, `funding-squeeze-v0.3-binance-lowcost-confirmatory-2026-10-07`, many venue-specific funding/basis branches. Perp basis **NOT NEW**. Crypto micro-reversion likewise overlaps `EXTREME-FLOW-REVERSION-OOS-001` whose 2025 OOS gross +2.4075bps and net -0.5925bps even at 3bps RT: economically tiny, no untested standalone diamond claim.

2. **Axia Futures** — https://www.youtube.com/@AxiaFutures
   - Public specifically identified video: https://www.youtube.com/watch?v=vVQyQMWDd8A (`Footprint Trading Workshop, Part 2: Market Interaction & Scenario Analysis`, published 2019). Description names differences between absorption/consolidation, volatility vs flow-driven markets, auction imbalance, risk placement, and rule-driven entries. This is **conceptual footage**, NOT a precise ready-made numerical strategy.
   - Public written/video case study: https://axiafutures.com/blog/footprint-strategies-you-can-apply-in-your-trading/ (March 2022). Describes a bid/ask footprint **micro double-distribution** P-shape, distinct zones of transacted volume, and **low-volume ledge** as risk/access level in a market with short covering. It illustrates other volume-at-price footprint clues. Author warns context/other tools are needed.
   - Constraint: predominantly traditional futures; applying directly to BINANCE:BTCUSDT spot is an **untested port**, not a claim of identical market behavior. Course may cost money; no purchase or private content required.

3. **Bookmap** — https://bookmap.com/learning-center/order-flow-phenomena/order-flow-education
   - Public original video: https://www.youtube.com/watch?v=0ClcuPRbNjI (`Layering and Absorption`, 2018); distinction of visible resting liquidity, executed volume and price nonresponse. Mentions order book history/spoofing/icebergs.
   - Duplication risk: high against `ABSORPTION-FAILED-AUCTION-001`, `L2-RESILIENCY-001` and `SWEEP-003`. Some true iceberg order inferences require full order-level data (MBO), not public Binance candle/aggTrade histories.
   - Source gate `ORDERBOOK-RESILIENCE-001` FAILED for historical Binance `bookDepth` in V0.1: 29–30 second granularity and broad percentage-depth bands are NOT valid sub-5-second near-touch queue replenishment. Do not relabel it as true L2 or infer iceberg quantity.

4. **QuantConnect** — https://www.youtube.com/@Quantconnect
   - Public educational channel and open-source LEAN systematic trading/backtesting platform: crypto plus other asset classes, order fee/fill/slippage model APIs. https://www.quantconnect.com/docs/v1/algorithm-reference/trading-and-orders
   - Useful as methodology/engineering control, not inherently a novel edge.

## Anti-duplication (project confirmed)
- `LOR-RF-001` frozen 2024 Discovery NO_EDGE: n=108, gross +11.20bps, net -14.80bps at frozen 26bps RT. No OOS rescue.
- `LOR-RLE-001` n=37 vs frozen 100 min, SOURCE/SAMPLE insufficient; descriptive outcome leak incident documented. Do not tune.
- `L2-RESILIENCY-001` 2025 validation mechanism **PASS** with <~1.2bps weak-strong response contrasts, but standard-base Hyperliquid taker floor 9bps RT and even optimistic maker 1.5bps/fill upper bound **FAILED** (`L2R-EXEC-PASSIVE-001`). Need a distinct causally justified economic mechanism, not changing fee assumptions.
- `ORDERBOOK-RESILIENCE-001` source-only fail for public Binance 30s `bookDepth`.
- `ABSORPTION-FAILED-AUCTION-001`: frozen 5m spot aggTrades q95 aggression + 75th volume; POC migration/path efficiency, 2016-bar causal baseline, distinct groups, 60min cooldown, 100 events EACH across >=30 UTC dates and 99% coverage; currently NO economic result. Source recovery 2026-10-09 classified 20/20 NON_EXTREME, 0 primary events. Existing outcomes stay sealed.
- `funding-cash-carry-v0.1`, `cross-venue-funding-basis-p0f-final-attack-v0.6`, `quarterly-basis-convergence-v0.1`, `funding-squeeze-v0.3-binance-lowcost-confirmatory-2026-10-07`: mechanism families already investigated; YouTube example cannot bypass earlier closeout.

## Priority hypothesis candidate — YT-AXIA-VAP-001 (SOURCE-ONLY, not frozen trading candidate)
**Claim to investigate, not assume:** *Full price-level executed-volume **two-peak / low-volume node structure** within an aggressive flow episode contains incremental, economically relevant information beyond the existing 5m aggregate aggressor-flow and single POC-migration controls.*

Micro double-distribution as publicly described in Axia's case study is an *interpretation* (short covering, two nodes of value) not a ready-made numerical signal.

Potential point-in-time source:
- Official public **Binance SPOT BTCUSDT aggTrades** contain timestamp, price, quantity, aggressor maker flag; signed executed-volume-by-price can be built from raw public trades.
- MM-V1 TradingView footprint has been recovered with genuine SHA256 source evidence 2026-10-02 onwards; held as comparison rather than a required proprietary signal if distinct mechanism can be shown.
- Need ensure tick-size history, exchange price precision, volume-at-price bin convention, exact event clock, causal two-peak definition, 100+ count-only events, and no future shape leakage. Raw aggTrades can provide executed traded volume by PRICE, not true resting order liquidity, L2 replenishment, authenticated hidden orders or queue position.
- Source hypothesis distinguishing evidence: conditional incremental predictive information of *bimodality / volume-at-price structure* after controlling the same time's bar return, realized aggression, volume and POC. This is **high overlap with existing POC studies**. A novelty overlap test is mandatory before any historical/outcome experiment.
- One potential access mechanism is low-volume node revisitation/rotation; precisely define BEFORE outcome (don't pick the best narrative based on historical graphics).
- Do **NOT** invent profit targets, thresholds, session filters, stop distances or cost model from the video: their quantified versions would be new Crypto Lab adaptations and must be explicitly pre-frozen prior to price-outcome access.

### Gate sequence — MUST precede any outcome access
G0. Obtain video/case-study factual source notes with exact timestamp/paragraph and distinguish speaker claims from our inferences. Full YouTube transcript has NOT been reviewed in this first audit; direct video page description + creator's case-study article only.
G1. Compare causally definable event overlap and observables against the actual `ABSORPTION-FAILED-AUCTION-001`, `L2-RESILIENCY-001`, `SWEEP-003`, `LOR-RLE-001` codes/frozen hypotheses. No duplicative relabeling.
G2. Source-only data feasibility and temporal-precision gate: 2022–2024 public Binance *spot* price-level aggTrades, SHA256, tick precision, raw row counts, timestamp coverage and asymmetry; do not download or parse economic outcome prices.
G3. Prospective numerical algorithm freeze + **count-only** source census with immutable sha receipts. If exact sample floor cannot be reached, SOURCE_SAMPLE_INSUFFICIENT; no markouts.
G4. Separate economic pre-outcome freeze: actual exchange fee assumptions/routing evidence, one chosen venue, spread/taker/maker/slippage/gaps/capacity, independent control, OOS boundary and no retuning.
G5. Historical Discovery only with prior G0–G4 accepted; no automatic 2025 or 2026 unlock. At most a prospective shadow if truly distinct and source/time coverage passes.

## Source gate adjudication
- Credible publicly identifiable channels: PASS.
- Educational content as concepts of economic mechanisms: PASS.
- Evidence any channel provides a *proven* crypto net-of-fees edge to us: **NONE VERIFIED**.
- Exact strategy rules in public Axia case study: PARTIAL; discretionary context/shape undefined.
- Historical price-level footprint source feasibility: PROPOSED / NOT YET GATED.
- Novelty of micro double-distribution over current lab: **PENDING / HIGH OVERLAP**.
- Candidate YT-AXIA-VAP-001: **RESEARCH_IDEA_ONLY — NO EDGE, NO CODE, NO BACKTEST, NO ORDERS**.

Rule: a YouTube channel is a lead generator, not evidence of past profits, reproducibility or future capacity. Never buy access, click referral offers or connect trading accounts based on this audit. NO main merge / Render / exchange / live trading.

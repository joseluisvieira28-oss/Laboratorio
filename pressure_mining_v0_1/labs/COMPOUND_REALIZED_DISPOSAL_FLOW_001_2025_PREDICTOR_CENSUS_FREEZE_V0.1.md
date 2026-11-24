# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — 2025 PREDICTOR-ONLY CENSUS FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / SOURCE-ONLY / PROTECTED MARKET OUTCOMES LOCKED

## 1. Purpose

Measure whether untouched calendar-year 2025 contains enough **predictor events** to support a separately authorized economic experiment.

This census may inspect Compound on-chain BuyCollateral events only.
It may not inspect any 2025 market price, return, funding, basis, volatility, PnL, spread, depth or post-event outcome.

## 2. Frozen source

Ethereum mainnet / Compound III USDC Comet:
0xc3d688B66703497DAA19211EEdff47f25384cdc3

Event:
BuyCollateral(address,address,uint256,uint256)
topic0:
0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b

Window:
2025-01-01T00:00:00Z through 2025-12-31T23:59:59Z.

Boundary block numbers must be resolved from public indexed block-by-time data:
- start uses closest=after;
- end uses closest=before.

## 3. Frozen outputs

- boundary blocks;
- BuyCollateral event count;
- unique transaction count;
- unique buyer count;
- unique collateral-asset count;
- counts by asset;
- counts by UTC month;
- number of unique ISO weeks;
- top-buyer concentration.

No external market data may be joined.

## 4. Predictor-viability gate

PREDICTOR_SAMPLE_VIABLE requires all:
1. >= 30 BuyCollateral events;
2. >= 30 unique transactions;
3. >= 3 collateral assets;
4. >= 12 unique ISO weeks;
5. no single event buyer accounts for >=80% of events.

Failure means only that this exact 2025 predictor population is weak for a broad event study.
It is not NO_EDGE.

## 5. Governance

This source census does not authorize:
- market-outcome access;
- direction selection from outcomes;
- horizon selection from outcomes;
- PnL;
- protected 2025 economic testing;
- promotion;
- capital;
- live trading;
- merge to main.

If predictor viability passes, the next lawful step is to freeze the economic contract completely and then obtain explicit authority before opening any protected 2025 market outcome.

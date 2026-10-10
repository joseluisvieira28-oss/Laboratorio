# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-BASKET MECHANISM DIAGNOSTIC V0.1

**Date:** 2026-09-24  
**Role:** POST-OUTCOME FORENSIC DIAGNOSTIC ONLY  
**Promotion credit:** ZERO

## Inputs

Closed authoritative BASE trade ledgers from:
- first untouched basket: ETHUSDT / SOLUSDT / BNBUSDT
- failed expansion basket: XRPUSDT / DOGEUSDT / ADAUSDT / LINKUSDT / AVAXUSDT

No new market outcomes are opened in this diagnostic.

## Core observation

The initial-loss mechanism is almost identical across assets:
- normal loss return clusters near -4.2%;
- the Parent hard-stop architecture therefore does not explain the survivor/failure split.

The split is concentrated in the positive tail.

| Asset | Result class | Win rate | Avg winner | Avg loser | Avg winner/loss payoff | Median winner duration h | Positive years / 5 |
|---|---|---:|---:|---:|---:|---:|---:|
| ETH | Survives | 23.0% | +20.09% | -4.23% | 4.75x | 424.0 | 4 |
| SOL | Survives | 22.7% | +19.47% | -4.28% | 4.55x | 171.0 | 3 |
| BNB | Survives | 27.5% | +18.82% | -4.19% | 4.49x | 365.5 | 2 |
| XRP | Fails | 16.2% | +17.91% | -4.21% | 4.25x | 171.5 | 2 |
| DOGE | Fails | 20.5% | +15.18% | -4.28% | 3.55x | 87.0 | 1 |
| ADA | Fails | 14.5% | +22.87% | -4.30% | 5.32x | 169.0 | 2 |
| LINK | Fails | 19.3% | +13.97% | -4.27% | 3.27x | 176.0 | 0 |
| AVAX | Fails | 20.8% | +13.03% | -4.23% | 3.08x | 124.0 | 0 |

Group averages:
- surviving basket win rate: ~24.4%
- failed basket win rate: ~18.2%
- surviving average winner: ~+19.5%
- failed average winner: ~+16.6%
- surviving average payoff: ~4.60x
- failed average payoff: ~3.89x

## Break-even win-rate margin

Using average winner/loss magnitudes:

| Asset | Actual WR | Approx. break-even WR | Margin |
|---|---:|---:|---:|
| ETH | 23.00% | 17.39% | +5.61 pp |
| SOL | 22.70% | 18.02% | +4.68 pp |
| BNB | 27.45% | 18.21% | +9.24 pp |
| XRP | 16.18% | 19.04% | -2.87 pp |
| DOGE | 20.48% | 21.98% | -1.50 pp |
| ADA | 14.47% | 15.82% | -1.35 pp |
| LINK | 19.25% | 23.43% | -4.18 pp |
| AVAX | 20.81% | 24.52% | -3.72 pp |

All three surviving assets clear their descriptive break-even win rate.
All five failed assets fall below it.

## Funding is not the primary separator

BASE funding per closed trade is approximately:
- ETH: -55.09 USDT
- SOL: -16.28
- BNB: -9.38
- failed basket: roughly -8.4 to -10.7 per trade

ETH survives despite the highest funding drag by a wide margin.

Therefore the survivor/failure split cannot plausibly be attributed primarily to funding.

## Tail structure

Surviving assets do not merely have one lucky trade:
- ETH / SOL / BNB all remain positive after removing their single largest winner.

Failed assets:
- all remain negative after removing the top winner.

This supports a descriptive interpretation that the Parent requires repeated trend persistence / recovery after extreme downside shocks, not merely isolated jackpots.

## Mechanism hypothesis generated

The Parent regime gate is:

`close > SMA200`

This can classify a rebound above a falling long-term average as “bull regime”.

The cross-basket diagnostic motivates a new child hypothesis:

> Require the long-term regime average itself to be rising, in addition to price being above it.

This is a post-outcome hypothesis and has zero credit until tested on untouched evidence.

## Scientific boundary

This document does NOT prove that SMA200 slope is the true causal separator.

Other latent differences may include:
- trend persistence;
- secular drift;
- volatility clustering;
- market structure;
- recovery depth after shocks;
- correlation with BTC / broad crypto beta.

Any new rule must be frozen before opening another untouched basket.

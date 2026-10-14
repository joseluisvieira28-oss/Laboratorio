# CRYPTO-INDEX-REBALANCE-FLOW-001 — PROSPECTIVE AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_PROSPECTIVE / SOURCE_AND_OBSERVATION_ONLY / NO TRADING
Branch: crypto-index-rebalance-flow-v0.1

## Time-sensitive reason for opening
Bitwise published an official rebalance notification dated 2026-09-22 stating constituent changes scheduled for the 2026-09-30 rebalance, including:
- Bitwise 10 Large Cap Crypto Index: UNI and ZEC enter; SUI and LTC exit.
- Bitwise 10 ex Bitcoin Large Cap Crypto Index: UNI and ZEC enter; SUI and LTC exit.
- Bitwise 10 Select Large Cap Crypto Index: UNI enters; SUI exits.
- Bitwise DeFi Crypto Index: SKY enters; CRV exits.

This lab is frozen before the 2026-09-30 implementation event.

## Anti-duplication
Google Drive, GitHub and accessible Library searches found no canonical Crypto Lab focused on index reconstitution / benchmark-tracking forced flow.

## Classification
Primary family: FLOW
Secondary: EVENT / MARKET STRUCTURE

This is NOT a generic "index inclusion => token goes up" test.

## Mechanism
Products and accounts tracking an index must move holdings toward new target constituents/weights in order to control tracking error. Those transactions can be relatively price-insensitive around a scheduled implementation boundary.

The scientific question is whether a pre-announced benchmark change produces a reproducible, signed inventory-pressure fingerprint around implementation, followed by normalization/reversal, after controlling for broad crypto moves.

Potential payer: benchmark-tracking capital prioritizing tracking error over execution price, plus liquidity demand concentrated near implementation.

## Exact distinction from failed ACCESS/event siblings
Failed listing/perpetual-launch/access labs asked whether new market access predicts directional token returns.

This lab instead tests:
official benchmark reconstitution -> constrained tracker flow -> event-time relative price/volume/liquidity pressure.

The observable mechanism must include a causal fingerprint (volume/liquidity/relative-price pressure near implementation), not merely a token return.

## Current event contamination rule
The Sep 22 announcement is already public. Price action from announcement until this freeze date is therefore CONTAMINATED for strategy selection and cannot be used to choose direction, thresholds or windows.

The Sep 30 implementation boundary remains prospective as of this freeze. Only measurements whose definitions are frozen now may count as prospective mechanism evidence.

## Frozen observation objects for Sep 30 pilot
Universe:
ADDS = UNI, ZEC, SKY
REMOVES = SUI, LTC, CRV

Each asset remains labeled only by official add/remove status. No asset may be dropped because of later performance.

Primary mechanism observables:
1. signed relative return vs BTC from T-24h to T0;
2. signed relative return vs BTC from T0 to T+24h;
3. spot volume ratio around T0 versus trailing same-clock baseline;
4. spread/depth state where a reproducible public source is available;
5. perp-spot basis/funding only as contextual diagnostics, not a rescue variable.

Signed convention fixed pre-outcome:
- ADD pressure sign = +1
- REMOVE pressure sign = -1
- signed relative effect = sign * excess return.

Mechanism fingerprint expectation:
positive signed pressure approaching/at implementation, with partial post-implementation normalization.
Failure is allowed and must be preserved.

## T0 rule — SOURCE_TIME_PASS
Official Bitwise Crypto Asset Index Methodology states that, unless otherwise disclaimed, indexes are reconstituted monthly at 4:00 p.m. Eastern Time on the last Business Day of the month.

For the 2026-09-30 event:
- T0 = 2026-09-30 16:00 America/New_York
- T0 = 2026-09-30T20:00:00Z
- T0 = 2026-09-30 22:00 Europe/Zurich

Source-time classification: SOURCE_TIME_PASS.

Do not infer or alter T0 from price, volume, spread, news or later observations.

## Costs and trading
This phase is observational only.
No PnL.
No order simulation presented as executable evidence.
No live/paper order.
No exchange mutation.
No leverage.
No capital.

## Historical extension
No historical backtest may be started until:
- official historical rebalance announcements/results are enumerated source-first;
- exact announcement and implementation timestamps are reproducible;
- index/product identity and constituent changes are captured without looking at market outcomes;
- a separate historical Discovery authority is frozen.

## Failure modes
- too little actual tracking capital;
- traders front-run all predictable flow before T0;
- trackers use OTC/TWAP/derivatives and avoid visible spot impact;
- effect is dominated by idiosyncratic token news;
- one or two tokens drive the entire result;
- costs/slippage exceed any later economic effect.

## Governance
No main merge.
No live trading.
No post-outcome rule edits.
No retrospective deletion of losing constituents.
This pilot can establish a mechanism fingerprint only; it cannot promote an edge by itself.

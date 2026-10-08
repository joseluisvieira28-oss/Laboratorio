# BTC-CONVEX-TREND-CAPTURE-001 — TRAILING FOOTPRINT AUDIT V0.1

**Date:** 2026-09-23  
**Status:** STRONG DESCRIPTIVE FINGERPRINT / EXACT CODE UNPROVEN

## Peak-giveback reconstruction

For each closed winning trade, the favorable peak was reconstructed from:
- entry price;
- reported max favorable excursion in USDT;
- position quantity.

Then:

`peak_giveback = 1 - exit_price / reconstructed_peak`.

Across the supplied exports:

| TF | Closed winners | Winners in 11.8%-12.1% giveback band | Share | Median within band |
|---|---:|---:|---:|---:|
| 5m | 38 | 37 | 97.4% | 11.9301% |
| 15m | 29 | 28 | 96.6% | 11.9336% |
| 4h | 17 | 15 | 88.2% | 11.9284% |
| **Total** | **84** | **80** | **95.2%** | ~**11.93%** |

Within the normal band, dispersion is extremely small (roughly 0.007%-0.010% standard deviation by timeframe).

## Interpretation

This is strong evidence that the profitable-exit engine normally uses a stop approximately **12% below a favorable peak**.

The evidence does not prove the literal Pine implementation:
- it may be a custom percentage trail;
- it may be a dynamically calculated tick offset;
- historical broker-emulator semantics may affect fill price;
- another exit condition may occasionally supersede the normal trail.

## Outliers

Four closed winners do not fall in the normal ~12% peak-giveback band.

Two are short-duration 4h trades where the normal trail fingerprint is not observed.

Two correspond to the 2021-07-26 Binance BTCUSDT perpetual dislocation/wick. Public contemporaneous reports document the Binance USDT perpetual contract briefly reaching approximately 48,168 USDT while spot was around 39-40k. The supplied trade report also records the extreme favorable excursion.

These outliers are preserved; they are not deleted to improve the fingerprint.

## Current reconstruction

Strong:
- initial capital ~10,000 USDT;
- 95% equity allocation;
- 0.10% fee each side;
- 4.00% normal hard stop;
- ~12% normal peak-giveback trailing exit.

Unknown:
- exact entry rule;
- trail activation;
- alternate exit behavior;
- TradingView execution properties.

## Scientific boundary

This audit characterizes the supplied strategy. It does not establish economic edge.

No threshold changes, survivor claim, promotion, live trading, or main merge are authorized.

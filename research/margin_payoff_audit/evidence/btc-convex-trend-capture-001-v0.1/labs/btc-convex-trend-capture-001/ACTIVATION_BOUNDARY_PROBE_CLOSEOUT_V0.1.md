# BTC-CONVEX-TREND-CAPTURE-001 — ACTIVATION BOUNDARY PROBE CLOSEOUT V0.1

**Date:** 2026-09-23  
**Workflow run:** 35895877651  
**Artifact:** 10766772382  
**Artifact SHA-256:** f871a398cbcd31a2df8cedea5e5f130db1c364fbe15fb1e3c3de8246e7ea309d  
**Status:** SOURCE PROBE PASS / SIMPLE FIXED CLOSE-THRESHOLD HYPOTHESIS NOT SUPPORTED

## Purpose

Use public Binance USD-M BTCUSDT klines to inspect six pre-frozen boundary trades:
- for each timeframe, the normal winner with the smallest observed MFE;
- for each timeframe, the eventual loser with the largest observed MFE.

This is forensic reconstruction only. It creates zero promotion credit and does not select a new threshold.

## Result

The Binance source probe completed successfully.

Maximum intratrade close return:

| TF | Boundary winner | Boundary loser | Fixed close-threshold separator? |
|---|---:|---:|---|
| 5m | +16.5207% | +16.7150% | **NO** |
| 15m | +16.6152% | +15.6723% | possible interval only |
| 4h | +14.7657% | +11.8629% | possible interval only |

The 5m loser reached a higher maximum close return than the smallest-MFE normal winner and still ultimately exited through the hard-loss path.

Therefore a single rule of the form:

`activate trailing when close return >= X%`

cannot by itself explain all supplied 5m outcomes.

## Scientific interpretation

This narrows the unknown mechanism but does not identify it.

The activation state may depend on information not present in the trade-list export, for example:
- the original entry/signal state;
- another indicator/state condition;
- time/bar-count logic;
- TradingView strategy order semantics;
- a variable activation level rather than one universal fixed return threshold.

These remain hypotheses, not findings.

The exact Pine/source remains the authoritative blocker for mechanism reproduction.

## Preserved findings

The seed evidence still strongly supports:
- long-only behavior;
- ~4% normal hard price stop;
- ~12% giveback from favorable peak on normal profitable exits;
- ~94.9% account allocation in the original backtest.

What remains unproven:
- exact entry signal;
- exact trailing activation rule;
- repaint/lookahead status;
- exact execution semantics.

## Verdict

**MECHANISM PARTIALLY RECONSTRUCTED / ENTRY + ACTIVATION STILL SOURCE-BLOCKED.**

No parameter rescue, edge claim, promotion, live trading, exchange mutation or main merge is authorized.

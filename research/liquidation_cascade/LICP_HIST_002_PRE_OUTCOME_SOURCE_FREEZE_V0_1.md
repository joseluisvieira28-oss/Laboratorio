# LICP-HIST-002 — HYPERLIQUID IGNITION → BYBIT CROSS-VENUE CONTINUATION
## PRE-OUTCOME SOURCE FREEZE V0.1

Date: 2026-09-26
Status: SOURCE GATE / NO BYBIT OUTCOMES

## Purpose
Use the public external Hyperliquid liquidation-event table only as a causal event-time source, then test price continuation on a DIFFERENT venue (Bybit).

This is a historical cross-venue replication track.
It is NOT MEXC validation and cannot substitute for the canonical MEXC forward study.

## External event-source restrictions
Allowed fields from the public event table:
- t0
- symbol / coin

Forbidden for event selection or triggering:
- klass
- doi_event
- peak_disloc
- ttr_min
- censored
- perm_6h
- perm_24h
- transitory_share
- any other post-event outcome or future-OI classification

The external paper's deleverage/churn class is explicitly NON-CAUSAL for this test because classification uses an OI trough inside t0→t0+2h.

## Trigger-time causality correction
The public event builder:
- resamples liquidation notional into 5-minute bins;
- uses a rolling 15-minute liquidation sum;
- stores the FIRST trigger bin label as t0.

Because a full 5-minute bin is not observable at its left-edge timestamp, LICP-HIST-002 defines:

OBSERVABLE_TRIGGER_TIME = t0 + 5 minutes.

No Bybit entry or outcome before observable_trigger_time is permitted.

## Bybit historical target source
Assets:
- BTCUSDT
- ETHUSDT

Public endpoint:
- Bybit V5 market kline
- category=linear
- interval=1 minute

## Source gate only
Before any external event table is downloaded or any Bybit price is analyzed, prove historical 1-minute timestamp coverage on fixed control dates:
- 2025-08-10
- 2025-10-10
- 2025-12-31

PASS requires non-empty historical timestamps for BTCUSDT and ETHUSDT on all controls.

No OHLC values are analyzed in this gate.

## Future outcome protocol, not yet opened
If source gate passes:
- entry clock = observable_trigger_time
- horizons = 5m / 15m / 30m / 60m
- continuation direction = long-liquidation event implies SELL / SHORT continuation
- use Bybit executable proxy from 1m candles only as coarse historical research, never as fill-perfect microstructure evidence
- fees and execution model must be frozen before outcomes

No live trading.
No merge to main.

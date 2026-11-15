# LICP-HIST-XALT-003 — BTC LIQUIDATION IGNITION → ETH/SOL SECOND-WAVE
## PRE-OUTCOME FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME SOURCE / DISCOVERY FREEZE

## Prior scientific status
The BTC→ALT second-wave mechanism was already predeclared in LICP-001 before any historical Binance outcome was opened.

LICP-HIST-XALT-003 is therefore not a rescue of the failed same-asset LICP-HIST-002 pooled continuation test.

## Event source
Pinned external Hyperliquid event table:
- commit fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04
- allowed fields: t0 and symbol only
- use ONLY rows where symbol == BTC

No external classification, OI outcome, liquidation magnitude or published price outcome is allowed.

## Causal time
observable trigger = t0 + 5 minutes
PRIMARY entry proxy = t0 + 6 minutes
OPTIMISTIC ceiling = t0 + 5 minutes

## Target assets
Official Binance Vision USD-M Futures 1m klines:
- ETHUSDT
- SOLUSDT

The hypothesis is cross-asset continuation:
BTC long-liquidation ignition => SELL / SHORT pressure propagates into ETH and/or SOL.

## Partitions
DISCOVERY:
- 2025-08-10 through 2025-10-31

LOCKED HOLDOUT:
- 2025-11-01 through 2025-12-31

Discovery code MUST NOT download/use holdout months.

## Horizons
5m / 15m / 30m / 60m after entry.

## Outcome
gross_directional_bps = (entry_open - future_open) / entry_open × 10,000

This is a coarse price-continuation measure, NOT executable PnL.

MEXC transfer ceiling:
gross_directional_bps - 16 bps.

No spread/slippage is included, therefore it deliberately favors survival.

## Discovery survivor
A target × horizon survives only when:
- n >= 30 BTC ignition events;
- mean gross > 16 bps;
- median gross > 0;
- at least 2 distinct Discovery months have positive mean gross.

## Candidate selection
If multiple target × horizon pairs survive:
- choose highest PRIMARY mean transfer-ceiling net;
- exact tie => shorter horizon;
- remaining tie => ETH before SOL only as deterministic tie-break.

Selected candidate must be serialized before HOLDOUT.

If none survive:
LICP_HIST_XALT_003_DISCOVERY_NO_EDGE.

No reversal rescue.
No holdout tuning.
No live-trading authority.

# BACKES-005 red-team finding — Initial 50/50 transaction fee undercharged in 004

Discovered by deterministic unit test on 2026-11-24 after the 005 risk-control rules had been frozen, BEFORE accepting any BACKES-005 economic outcome.

## Error reproduced
BACKES-004's `trade_model` computed `traded=max(abs(wb-pb), abs(we-pe))`. At creation of a 50% BTC / 50% ETH basket from 100% cash, this returns 0.5 rather than the 1.0 of NAV purchased (0.5 BTC + 0.5 ETH). That undercharges the initial entry cost by 50% for MIX only.

BACKES-005 uses `max(total_buys, total_sells)` for direct netted spot trading, resulting in 1.0 for initial 50/50 purchase and 1.0 for a full BTC<->ETH swap. Two-hop routing uses `total_buys+total_sells`.

At 10bps per leg over 2018–2026, **with all other rules unchanged**, corrected 50/50 simulated total return is about **+320.6428% Coinbase** vs old reported +320.85333%; **+326.11881% Binance** vs old reported +326.33208%. These changes are exactly the multiplicative adjustment of initial cost: (1−0.001)/(1−0.0005), no change in data, strategy, signal or subsequent trades.

The original FROZEN002, MOM8, BTC and ETH return parities are required unchanged to 0.00015 percentage points.

## Scientific status
This is a pre-result accounting correction discovered by a failing test; **not a parameter improvement, not a new edge and not a reason to loosen 30% drawdown gate**. Original BACKES-004 artefacts remain immutable as historical evidence. Any new backtest must clearly distinguish the fee correction from economic performance of protective overlays.

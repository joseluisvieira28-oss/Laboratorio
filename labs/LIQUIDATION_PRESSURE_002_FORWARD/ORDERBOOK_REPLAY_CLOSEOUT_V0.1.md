# LIQUIDATION-PRESSURE-002-FORWARD — ORDERBOOK REPLAY CLOSEOUT V0.1

**Date:** 2026-09-23  
**Run:** 35823025935  
**Artifact:** 10734600109

## Verdict

**ORDERBOOK_REPLAY_PASS**

A 120-second public Bybit forward capture was replayed through the snapshot/delta book reconstructor for all six frozen symbols.

Across BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT and BNBUSDT:
- at least one snapshot was observed;
- thousands of deltas were replayed per symbol;
- zero pre-snapshot deltas were admitted;
- zero non-monotonic update ids;
- zero non-monotonic sequence ids;
- zero crossed reconstructed books;
- zero parse errors.

No liquidation-return markout, trading outcome or PnL was computed. This closes the L2 reconstruction engineering gate only.

The same capture contained zero liquidation records; that is not negative economic evidence and no canonical q95 threshold was emitted. Calibration remains gated by the prospectively frozen 24-hour and 500-record minimum.

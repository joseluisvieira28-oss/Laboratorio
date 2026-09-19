# BTC-OPTIONS-VRP-BINANCE-001 — GEOMETRY STRIKE NORMALIZATION AMENDMENT V0.1A

Date: 2026-09-19
Parent geometry run: `35461347235`
Structural diagnostic run: `35463137570`
Strike semantics diagnostic run: `35463245436`

## Evidence

The parent geometry gate loaded 147 source days but produced zero structurally complete 08:00 rows.

The frozen zero-row diagnostic proved the single rejection reason on all three fixed dates was strike parsing:
- 2023-05-18: 248/248 rejected at strike parse;
- 2023-07-01: 280/280;
- 2023-10-23: 230/230.

The source-semantics diagnostic then proved Binance's EOH `strike` field is encoded as `YYMMDD-STRIKE`, e.g. `230519-25000`, while the symbol independently encodes the same contract identity as `BTC-230519-25000-P`.

## Authorized technical normalization

Replace direct `float(strike_raw)` with a deterministic structural parser:

1. if `strike_raw` is directly numeric, parse it unchanged;
2. otherwise, if it matches `YYMMDD-NUMERIC_STRIKE`, parse only the numeric strike token after the first hyphen;
3. require the date token in `strike_raw` to equal the already parsed expiry token in the option symbol;
4. otherwise fail closed.

No DTE bin, decision hour, 24h hold geometry, episode threshold, source window or economic rule changes.

No option prices, returns, VRP, future variance, PnL or performance are opened by this correction. The original zero-geometry run remains preserved as non-adjudicative technical parser failure.

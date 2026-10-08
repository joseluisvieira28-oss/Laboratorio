# MLRTS V0.1.1 — HISTORICAL MARKET-DATA REMEDIATION FREEZE
Date: 2026-10-08
Parent run: 37745840540
Parent classification: MARKET_DATA_INSUFFICIENT (4/11 analyzable)
Status: OUTCOME-BLIND TECHNICAL REMEDIATION WITH RESOLVED OUTCOMES FROZEN

## Facts already observed
The first frozen Discovery run resolved only 4/11 events because several reward-token historical symbol/file bindings were unavailable through the current-symbol + daily-history route. One explicit current binding failure was TRN.

The 4 resolved outcomes are preserved exactly and must not influence any scientific-rule change.

## Permitted remediation
Only technical source recovery is allowed:
- recover historical/delisted MEXC spot symbol IDs from official/public MEXC endpoints or official history-file metadata;
- recover official/public MEXC 15m history files for the exact frozen 11 token/USDT markets;
- recover BTC/USDT from the same authoritative public route;
- verify timestamps and file-bucket mapping;
- join only exact entry/+1h/+6h/+24h candles required by the pre-outcome freeze.

## Forbidden
- no event addition/deletion/substitution;
- no T0 change;
- no horizon change;
- no sign inversion;
- no alternate control;
- no nearest-neighbor/interpolation;
- no choosing a different venue for project-token outcomes;
- no parameter/filter rescue;
- no post-outcome exclusion of extreme observations.

## Resolution rule
If >=10/11 frozen events become analyzable, rerun the exact V0.1 statistical adjudication once over all analyzable frozen events.
If fewer than 10 can be recovered from authoritative MEXC public history, final classification is MARKET_DATA_INSUFFICIENT / SOURCE_BLOCKED_FOR_DISCOVERY, not NO_EDGE.

Research only. No trading, orders, accounts, wallets, exchange mutation, spending or main merge.

# MEXC-WTI-EVENT-SHOCK-001 — V1.3 SOURCE COVERAGE CLOSEOUT

Date: 2026-10-04
Run: 37201483278

## Freeze status

V1.3 pre-outcome freeze passed before historical acquisition.

Frozen source resolution:
`Min1`

Frozen event set:
- 30 Discovery releases, February-August 2026;
- 5 September OOS releases.

## Coverage result

The runner failed closed BEFORE scientific scoring.

Coverage:
- total EIA events requested: 35
- usable event windows: 4
- Discovery usable: 0 / 30
- OOS usable: 4 / 5
- September 2 was not recoverable at Min1;
- older February-August Min1 event windows returned zero rows.

The runner emitted source-coverage diagnostics and then raised:
`EVENT_WINDOW_COVERAGE_INCOMPLETE`

No Discovery matrix, p-value, mean return, win rate, Holm selection, OOS result, or WTI edge verdict was produced.

## Verdict

`SOURCE_BLOCKED_WTI_MIN1_HISTORICAL_RETENTION__NO_SCORING`

This is NOT a NO_EDGE verdict.

## Legitimate successor

Because V1.3 opened no performance statistic, a transport-resolution successor may:
- preserve the exact 35 EIA release timestamps;
- preserve thresholds 0/10/20/40 bps;
- preserve CONTINUATION and REVERSAL modes;
- preserve horizons 5/15/30/60m;
- preserve Discovery/OOS partitions and statistical gates;
- replace Min1 with public MEXC Min5 historical candles;
- adopt the corresponding pre-outcome Min5 clock/entry semantics.

No parameter rescue or post-outcome selection occurred.

No accounts, credentials, wallets, orders, mutation, live trading, or main merge.

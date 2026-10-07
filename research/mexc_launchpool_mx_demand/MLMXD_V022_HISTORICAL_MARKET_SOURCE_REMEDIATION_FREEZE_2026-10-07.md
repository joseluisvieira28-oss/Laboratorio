# MLMXD V0.2.2 — HISTORICAL MARKET SOURCE REMEDIATION FREEZE
Date: 2026-10-07
Status: TECHNICAL DATA-COVERAGE REMEDIATION AFTER PARTIAL OUTCOME ACCESS

## Trigger
The frozen 14-event activation pilot opened market data for the first time. Only 2/14 events were analyzable because the current MEXC V3 public kline endpoint returned no 2025 candles.

A raw V3 diagnostic confirmed this is source-retention coverage:
- 2025-01-23 MXUSDT: 0 rows
- 2025-01-23 BTCUSDT: 0 rows
- 2025-08-04 MXUSDT: 0 rows
- 2025-08-04 BTCUSDT: 0 rows
- 2026-05-20 both symbols: 104 rows

## Permitted remediation
For ONLY the already-frozen missing rows, use an official MEXC historical public source capable of returning the exact same instruments and exact required 15-minute timestamps:
1. MEXC historical market-data archive; or
2. legacy official MEXC public spot kline endpoint if it still serves the required history.

## Immutable study rules
No change to:
- the 14 frozen events;
- activation T0;
- MXUSDT and BTCUSDT;
- 15-minute timeframe;
- entry;
- +24h primary exit;
- relative-return formula;
- diagnostics;
- statistical gate.

No existing analyzable row may be replaced merely because another source produces a more favorable result. A remediation source is used only to fill rows missing from the V3 route; overlap may be checked for consistency.

## Interpretation
The V0.2 run's PILOT_NO_SIGNAL label is not an economic verdict because N=2 failed the frozen N>=10 requirement due to data coverage.

Until remediation completes:
DATA_COVERAGE_INSUFFICIENT

## Governance
Public/read-only research only. No authenticated API, account access, orders, exchange mutation, wallet, spending, or main merge.

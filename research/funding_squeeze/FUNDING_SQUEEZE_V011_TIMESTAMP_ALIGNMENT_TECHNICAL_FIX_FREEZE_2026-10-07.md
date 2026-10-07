# FUNDING-SQUEEZE-001
## V0.1.1 TIMESTAMP ALIGNMENT TECHNICAL FIX FREEZE
Date: 2026-10-07
Status: TECHNICAL FIX FROZEN — NO DEVELOPMENT CELL RESULT PRODUCED

### Trigger
Development workflow run 37678863733 failed before producing any grid-cell result.

Observed Binance funding calc_time example:
- 2021-04-11 00:00:00.004 UTC

The 1h kline clock is exactly hourly, so direct lookup by the raw millisecond-offset funding timestamp caused a KeyError.

### Frozen correction
For Development and any later confirmatory implementation using the same Binance archive schema:
1. parse raw funding calc_time;
2. round each funding timestamp to the nearest UTC hour;
3. require absolute raw-to-rounded distance <= 5 seconds;
4. fail closed if any funding timestamp exceeds that tolerance;
5. use the normalized hourly timestamp only for joining funding settlements to 1h spot/perp bars.

No rate, threshold, quantile, hold, exit mode, cost, PnL formula, sample gate or candidate-selection rule changes.

### Outcome state
The failed run produced no CELL result and no scientific verdict.
2025 and 2026 remain unopened.

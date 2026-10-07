# FUNDING-SQUEEZE-001 V0.2.1
## MEXC SPOT KLINE ENUM TECHNICAL FIX FREEZE
Date: 2026-10-07
Status: TECHNICAL SOURCE FIX ONLY

Run 37680029260 returned SOURCE_BLOCKED because the MEXC Spot REST kline endpoint rejected interval=1h with HTTP 400.

Official MEXC Spot API documentation defines the one-hour REST kline enum as 60m.

Frozen correction:
- replace Spot REST interval 1h with 60m only.

No signal, threshold, hold, calendar, cost, PnL, bootstrap, source coverage gate or scientific promotion gate changes.
The failed run did not retrieve any spot kline and did not produce any trade outcome.
2026 remains closed.

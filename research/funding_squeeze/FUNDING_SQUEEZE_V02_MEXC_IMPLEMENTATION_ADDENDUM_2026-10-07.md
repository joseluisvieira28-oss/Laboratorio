# FUNDING-SQUEEZE-001 V0.2
## MEXC TIMESTAMP / SOURCE IMPLEMENTATION ADDENDUM
Date: 2026-10-07
Status: FROZEN BEFORE OUTCOME RUN

- Funding settleTime is preserved raw and normalized to the nearest UTC hour only for joining hourly candles.
- Normalization is allowed only when absolute offset is <= 5 minutes; otherwise SOURCE_BLOCKED.
- Spot /api/v3/klines uses 1h and millisecond startTime/endTime.
- Futures /api/v1/contract/kline/BTC_USDT uses Min60 and second start/end.
- Historical requests are segmented; duplicate open times are deduplicated.
- Source coverage requires >=98% of expected hourly timestamps for BOTH spot and perpetual over 2024-2025 and enough funding history to initialize the frozen 540-settlement rolling threshold.
- Missing required entry/exit/settlement price timestamps invalidate that trade; if analyzable trade coverage falls below 95% of otherwise eligible non-overlapping signals, verdict is SOURCE_BLOCKED.
- No interpolation of prices or funding rates.
- No rule/cost/gate changes.

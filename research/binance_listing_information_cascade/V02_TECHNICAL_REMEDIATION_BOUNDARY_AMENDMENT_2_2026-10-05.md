# V0.2 TECHNICAL REMEDIATION — BOUNDARY AMENDMENT 2
Date: 2026-10-05
Status: LOCKED BEFORE RE-RUN

The first remediation accidentally added a stricter source condition not present in V0.1/V0.2: it required a candle at exactly T-24h. That condition is withdrawn as an implementation artifact.

Scientific rules remain unchanged.

Implementation:
- same 12 observations, T0s, venue hierarchy and symbols;
- retrieve overlapping historical chunks and deduplicate by candle-start timestamp;
- exact P0 = candle start immediately before the T0 minute;
- exact R1/R5/R15/R60 target candle-start timestamps;
- historical coverage witness follows the original freeze tolerance: at least one bar at or before T-24h+10m;
- volume baseline is wall-clock aligned, non-overlapping 5m buckets covering T-24h through T-1h; available 1m volumes are summed into their fixed bucket, so missing no-trade candles contribute zero rather than shifting bucket membership;
- no event filtering, threshold changes, outlier deletion, symbol substitution, endpoint shopping, or 2025+ access.

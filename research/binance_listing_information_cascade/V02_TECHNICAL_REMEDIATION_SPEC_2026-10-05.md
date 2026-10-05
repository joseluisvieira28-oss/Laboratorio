# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.2 TECHNICAL REMEDIATION SPEC
Date: 2026-10-05
Status: LOCKED TECHNICAL CORRECTION AFTER INTEGRITY AUDIT

The exact-bar integrity audit found that the V0.2 runner's 90-minute pagination advanced the next request by z+60s while z already represented the next boundary. Across the 24h baseline this created deterministic one-minute holes. The frozen R15 target happened to fall on a missing boundary in 11/12 observations, so the stored runner selected the prior available bar.

This is an implementation defect, not a scientific rule change.

## Locked remediation
- Keep the exact same 12 eligible observations, T0 values, venue hierarchy, symbols, P0 definition, horizons, baseline, metrics and V0.2 gates.
- Align retrieval to candle-start minute.
- Fetch exactly 90 candle-start timestamps per chunk: [start, start+89m], then next_start=end+1m.
- Deduplicate by timestamp.
- Require the exact target bar at minute+1m, +5m, +15m and +60m.
- Baseline remains T-24h..T-1h and non-overlapping 5m volume buckets.
- No substitution, filtering, threshold changes, outlier removal or symbol changes.
- Original results_v02 are retained as non-authoritative bugged evidence.
- Corrected outputs go to results_v02_remediated.
- 2025+ remains CLOSED.
- V0.2 gate remains: n>=12; median R15>0.75%; hit-rate>=65%; median R5>0.50%; median volume shock>=2x; LOO median R15>0; positive-return concentration<=35%.

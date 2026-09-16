# ETF-CREATION-FLOW-001 — SOURCE FEASIBILITY V0.1

Research-only / outcome-blind.

## Frozen source probe
- Official iShares / BlackRock only.
- Portfolio ID: 333011 (IBIT).
- Probe dates: 2024-03-28, 2024-06-28, 2024-09-30, 2024-12-30.
- Allowed fields: explicit holdings as-of date and Shares Outstanding.
- Probe PASS requires >=3 exact requested as-of dates across >=3 distinct quarters from the same official route.
- A response that silently returns a different/latest as-of date is rejected.
- No BTC data, returns, PnL, 2025 or 2026 access.

## Candidate official routes
1. iShares historical holdings AJAX pattern using `1467271812596.ajax` with `fileType=csv`, `dataType=fund`, portfolio product path, and `asOfDate=YYYYMMDD`.
2. Product `latest-holdings.csv` route with `asOfDate=YYYYMMDD`, accepted only if the payload explicitly matches the requested as-of date.

No unofficial mirror or aggregator fallback is authorized.
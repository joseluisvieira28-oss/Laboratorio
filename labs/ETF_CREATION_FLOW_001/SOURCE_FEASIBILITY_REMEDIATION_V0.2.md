# ETF-CREATION-FLOW-001 — SOURCE FEASIBILITY REMEDIATION V0.2

Pre-outcome source transport remediation only.

V0.1 result: SOURCE_FEASIBILITY_BLOCKED. The old CSV AJAX pattern returned HTML for IBIT, and `latest-holdings.csv?asOfDate=` ignored the historical date and returned the current snapshot. No BTC data/outcome was accessed.

V0.2 changes only the official iShares transport:
`/1467271812596.ajax?fileType=json&tab=all&asOfDate=YYYYMMDD`

Probe dates remain exactly: 2024-03-28, 2024-06-28, 2024-09-30, 2024-12-30.

V0.2 PASS requires, from the official historical JSON payload only:
- an exact requested historical as-of date or unambiguous requested-date binding;
- a numeric Shares Outstanding value or equivalent provider-native field explicitly identifying fund shares outstanding;
- >=3 exact dates across >=3 quarters from the same route.

Holdings quantity, market value, NAV, Bitcoin quantity or AUM may NOT substitute for Shares Outstanding under MVE ECF-IBIT-SHARES-1D-001.

No BTC market data, returns, PnL, 2025 or 2026 access.
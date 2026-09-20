# BTC-MVRV-VALUATION-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35499464849`
Artifact: `BTC_MVRV_VALUATION_001_SOURCE_V0_1`

## Classification

**BMV_SOURCE_FULL**

The Coin Metrics Community API exposes a direct Bitcoin MVRV series:

- `CapMVRVCur`: 100% daily coverage over 2019-01-01 through 2025-12-31;
- no API key;
- zero cash spend;
- no duplicate daily observations.

Additional findings:
- `CapMrktCurUSD`: 100% coverage;
- `CapMrktEstUSD`: 93.27% coverage;
- direct `CapMVRVFF`, `CapMVRVZ`, realized-cap detail metrics, NUPL and several related valuation metrics are catalogued but return HTTP 403 in the Community tier.

The lab therefore binds to **CapMVRVCur only** for valuation and does not attempt to reconstruct a different MVRV variant.

No future returns, regression, PnL or 2026 data were opened by the source gate.

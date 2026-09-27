# LICP-001 — MEXC HISTORICAL COVERAGE RESULT V0.2

Date: 2026-09-26
Workflow run: 36231698656
Status: HISTORICAL_2025_SOURCE_BLOCKED / RECENT_CONTROL_PASS

## 2025 probe
For BTC_USDT, ETH_USDT and SOL_USDT:
- 2025-08-10: 0 Min1 timestamps
- 2025-10-10: 0 Min1 timestamps
- 2025-12-31: 0 Min1 timestamps

## Recent controls
For all three target symbols:
- 2026-09-01: 121 Min1 timestamps in the two-hour window
- 2026-09-25: 121 Min1 timestamps in the two-hour window

Therefore the endpoint is functional, but the requested 2025 target history is unavailable through this public route.

## Decision
Historical MEXC validation against the external 2025 Hyperliquid event sample is SOURCE_BLOCKED through the tested public kline endpoint.

Do not substitute a different venue and call it MEXC validation.

Forward LICP-001 remains the canonical free/public path.

The external Hyperliquid requester-pays S3 archives are not used here because they would incur third-party transfer cost; no such spending is authorized by this research branch.

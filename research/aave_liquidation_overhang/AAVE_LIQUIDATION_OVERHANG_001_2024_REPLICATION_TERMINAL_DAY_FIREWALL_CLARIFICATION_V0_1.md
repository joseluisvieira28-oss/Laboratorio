# AAVE-LIQUIDATION-OVERHANG-001 — 2024 REPLICATION TERMINAL-DAY FIREWALL CLARIFICATION V0.1

Status: **FROZEN BEFORE ANY 2024 PREDICTOR OR LIQUIDATION OUTCOME OPENING**
Date: **2026-09-19**

## Conflict resolved

The frozen replication partition specifies daily snapshots from 2024-01-01 through 2024-12-31 inclusive and the same next-24h liquidation outcome used in Discovery.

The hard safety firewall independently forbids opening any 2025 scientific data.

The next-24h window after the 2024-12-31 00:00 UTC snapshot necessarily extends into 2025-01-01. Therefore that final outcome cannot be observed without violating the pre-existing 2025 lock.

## Frozen resolution

- Build and persist all **366** point-in-time 2024 predictor snapshots, including 2024-12-31.
- Open outcomes only for the **365 complete non-overlapping windows** beginning 2024-01-01 through 2024-12-30.
- The 2024-12-31 predictor row is right-censored for outcome purposes and is not included in the primary Spearman/bootstrap replication statistic.
- No 2025 block header, Aave state, LiquidationCall, price, return or other scientific value may be opened.
- Eligibility uses the complete paired replication sample (365 days). The already-frozen threshold >=330 valid 2024 daily snapshots is therefore evaluated on these 365 complete pairs.

## Science unchanged

Unchanged:
- daily 00:00 UTC clock;
- 10% primary stress;
- borrower/HF/eMode/oracle semantics;
- OVERHANG_DEBT_10;
- next-24h liquidation debt-notional outcome;
- Spearman statistic;
- stationary bootstrap (mean block 7, 10,000 resamples, seed 20260918);
- largest-outcome-day sensitivity;
- pass/fail gates;
- no market-return/PnL testing;
- no trading authority.

This clarification is boundary/firewall hygiene only and is frozen before any 2024 predictor or outcome is opened.

# DEFI-LIQUIDATION-SHOCK-001 — SOURCE COVERAGE PROBE RECEIPT V0.1

Date: 2026-09-16
Branch: `defi-liquidation-shock-v0.1`
Classification: `SOURCE_COVERAGE_CONFIRMED_IN_SAMPLED_WINDOWS / OUTCOME_BLIND`

## Purpose

Confirm that the public Solana BigQuery dataset contains historical instruction rows for the four frozen protocol program IDs without opening prices, returns, PnL, market direction, or any trading outcome.

Dataset: `bigquery-public-data.crypto_solana_mainnet_us.Instructions`

Frozen program IDs:

- Save / Solend: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- marginfi v2: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- Kamino Lend: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- Drift v2: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

## Cost / partition diagnostics

The original full-window V0.1 query estimated **89.21 TB** and was NOT executed under the fail-closed 100 GB per-query operational cap.

`INFORMATION_SCHEMA.COLUMNS` showed:

- `block_timestamp` = partitioning column
- `program_id` = clustering ordinal position 1

A one-day direct-filter probe for 2024-12-15 estimated **497.06 MB** and was executed.

A four-window historical probe using one seven-day window in December of each year 2021, 2022, 2023 and 2024 estimated **13.4 GB** and was executed.

No billing upgrade or paid resource was activated.

## One-day 2024 source presence probe

Window: `[2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)`

| protocol | instruction_rows | distinct_transactions | first_instruction_utc | last_instruction_utc |
|---|---:|---:|---|---|
| drift_v2 | 1,540,397 | 920,847 | 2024-12-15 00:00:00 UTC | 2024-12-15 23:59:59 UTC |
| kamino_lend | 225,789 | 43,681 | 2024-12-15 00:00:17 UTC | 2024-12-15 23:59:54 UTC |
| marginfi_v2 | 49,858 | 44,932 | 2024-12-15 00:00:00 UTC | 2024-12-15 23:59:56 UTC |
| save_solend | 14,605 | 5,315 | 2024-12-15 00:00:05 UTC | 2024-12-15 23:59:48 UTC |

## Historical sampled-window coverage

Each probe window is `[December 12 00:00:00Z, December 19 00:00:00Z)` for the given year.

| year | protocol | instruction_rows | distinct_transactions | first_instruction_utc | last_instruction_utc | outer_rows | inner_cpi_rows |
|---:|---|---:|---:|---|---|---:|---:|
| 2021 | save_solend | 649,971 | 143,328 | 2021-12-12 00:00:18 UTC | 2021-12-18 23:59:59 UTC | 591,500 | 58,471 |
| 2022 | drift_v2 | 343,437 | 186,140 | 2022-12-12 00:00:00 UTC | 2022-12-18 23:59:57 UTC | 343,437 | 0 |
| 2022 | save_solend | 3,273,963 | 903,068 | 2022-12-12 00:00:00 UTC | 2022-12-18 23:59:59 UTC | 3,268,041 | 5,922 |
| 2023 | drift_v2 | 16,517,155 | 12,073,297 | 2023-12-12 00:00:00 UTC | 2023-12-18 23:59:59 UTC | 16,503,902 | 13,253 |
| 2023 | kamino_lend | 800,484 | 133,038 | 2023-12-12 00:00:01 UTC | 2023-12-18 23:59:59 UTC | 800,466 | 18 |
| 2023 | marginfi_v2 | 604,333 | 497,124 | 2023-12-12 00:00:01 UTC | 2023-12-18 23:59:59 UTC | 602,672 | 1,661 |
| 2023 | save_solend | 1,643,441 | 514,933 | 2023-12-12 00:00:02 UTC | 2023-12-18 23:59:59 UTC | 1,631,010 | 12,431 |
| 2024 | drift_v2 | 11,618,489 | 7,183,736 | 2024-12-12 00:00:00 UTC | 2024-12-18 23:59:59 UTC | 10,516,227 | 1,102,262 |
| 2024 | kamino_lend | 1,358,617 | 243,478 | 2024-12-12 00:00:06 UTC | 2024-12-18 23:59:47 UTC | 1,179,932 | 178,685 |
| 2024 | marginfi_v2 | 256,847 | 182,516 | 2024-12-12 00:00:01 UTC | 2024-12-18 23:59:53 UTC | 78,922 | 177,925 |
| 2024 | save_solend | 119,989 | 41,730 | 2024-12-12 00:00:09 UTC | 2024-12-18 23:59:49 UTC | 101,029 | 18,960 |

## Interpretation

This establishes source presence in the sampled historical windows:

- Save/Solend: confirmed in the sampled 2021, 2022, 2023 and 2024 windows.
- Drift v2: confirmed in the sampled 2022, 2023 and 2024 windows.
- Kamino Lend: confirmed in the sampled 2023 and 2024 windows.
- marginfi v2: confirmed in the sampled 2023 and 2024 windows.

Absence from a sampled window is NOT evidence that a protocol did not exist or have activity elsewhere in that year. Exact historical activation/deployment boundaries remain subject to separate historical-version/source-authority work.

The 2024 sample also proves that inner/CPI instructions are materially present, particularly for Drift v2, Kamino Lend and marginfi v2. Candidate extraction must therefore preserve and inspect both outer and inner/CPI instruction locations; outer-only extraction would be incomplete.

## Scientific state

This is NOT evidence of edge, predictive direction, positive expectancy, or profitability.

No prices, returns, PnL, market outcomes, live trading, exchange mutation, wallet action, post-outcome tuning, or merge to main occurred.

Valid next step: run a bounded, outcome-blind liquidation-candidate census smoke test using the pre-registered discriminators, then reconcile candidate transactions against raw archival RPC and historical decoder/version authority before any SOURCE_DATA_PASS can be granted.

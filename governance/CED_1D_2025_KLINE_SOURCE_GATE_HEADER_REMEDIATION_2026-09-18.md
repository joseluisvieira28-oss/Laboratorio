# CED-1D-V1 — 2025 KLINE SOURCE-GATE HEADER REMEDIATION — 2026-09-18

**Status:** FROZEN AFTER SOURCE-ONLY TECHNICAL FAILURE / BEFORE 2025 OUTCOMES

Observed run: 35339719882.

The run accessed source bytes only. It computed no signals, returns, PnL, p-values, or promotion metrics.

Observed invariant pattern on the frozen source files:
- ZIP SHA256 matched frozen canonical registry;
- official .CHECKSUM matched;
- ZIP CRC passed;
- expected CSV member passed;
- expected row count and unique timestamp count passed;
- OHLC/timestamp/duplicate/volume structural checks passed;
- each file reported exactly one parse violation at the first CSV row.

Cause: Binance public kline archives contain a CSV header row. The V0.1/V0.2 source-only parser attempted to parse that header as numeric market data.

Frozen remediation:
- accept at most one header row;
- it must be the first non-empty CSV row;
- it must contain exactly 12 columns;
- normalized first column must identify open time (open_time, opentime, timestamp, time, or start_time);
- no later parse failure is waived;
- all hashes, checksums, CRC, month bounds, duplicates, row counts and structural checks remain unchanged.

Current source scope is the V0.2 32-file manifest (2024-09..2025-12 for AVAXUSDT/SOLUSDT).

This remediation changes no market rule, cost, target, neighbour, statistic, or 2025 outcome policy.

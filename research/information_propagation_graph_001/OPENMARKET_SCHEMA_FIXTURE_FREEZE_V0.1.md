# OPENMARKET NEGATIVE CONTROL — SCHEMA FIXTURE FREEZE V0.1

Frozen: 2026-09-24
Dataset: gregyoung14/openmarket-btc-polymarket
Exact immutable revision: 74502466d1a7cef56395bfd8d0b465fbebc849cf

Purpose: inspect one deterministic lag-pair parquet schema before choosing any
timing statistic implementation.

## File selection rule

From the exact immutable manifest:
1. keep paths under full/lag_pairs_ms/ ending .parquet;
2. require manifest size >= 100,000 bytes;
3. sort paths lexicographically;
4. select the first path.

This rule is based on file metadata only. No parquet row content was opened to
choose the fixture.

## Allowed probe

Read only parquet footer/schema metadata:
- selected path;
- file size / SHA256;
- row count;
- row-group count;
- column names and physical/logical types.

Do not compute timing distributions, predictive performance, correlations or
jitter sensitivity in this probe.

After schema receipt exists, a separate timing-statistic freeze is required
before row data is analyzed.

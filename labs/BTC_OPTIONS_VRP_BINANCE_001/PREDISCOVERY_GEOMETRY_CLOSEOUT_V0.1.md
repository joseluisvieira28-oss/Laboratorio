# BTC-OPTIONS-VRP-BINANCE-001 — PREDISCOVERY GEOMETRY CLOSEOUT V0.1

Date: 2026-09-19
Census: `BOVRP-BINANCE-PREDISCOVERY-GEOMETRY-001`
Canonical run: `35465012135`
Canonical head: `5999b9b6890cfbb6adcf100ad684dc743856b338`
Artifact ID: `10590784541`
Artifact digest: `sha256:259eb54903f356bfd21b0c29fdc90d59a601d9663433cf94d6b3655c9e8e87c1`

## Final classification

**PREDISCOVERY_GEOMETRY_PASS**

The corrected source-only census loaded 147 historical option-source days and opened no economic outcomes.

Frozen 24h episode counts:

| DTE bucket | Distinct 24h starts | Months | Paired strikes total | Gate |
|---|---:|---:|---:|---|
| 1-2 | 39 | 6 | 481 | FAIL sample |
| 2-4 | 90 | 6 | 1,756 | PASS |
| 4-8 | 76 | 6 | 1,213 | FAIL sample |
| 8-15 | 114 | 6 | 1,688 | PASS |
| 15-31 | 111 | 6 | 2,171 | PASS |

Frozen gate: at least 80 distinct 24h episode starts and at least 4 calendar months in one predeclared DTE bucket.

Qualifying buckets:
- `DTE_2_4`
- `DTE_8_15`
- `DTE_15_31`

## Scientific interpretation

The free Binance EOH archive contains sufficient point-in-time BBO geometry to justify a separately frozen economic Discovery.

For comparability to the existing Deribit 30-day volatility-premium finding, the next protocol may designate `DTE_15_31` as the primary economic stratum based on mechanism/horizon alignment, not on observed PnL (none has been opened). The other qualifying bins may be frozen as non-rescuing secondary term-structure diagnostics.

This closeout does not authorize any return, variance, VRP, PnL or strategy conclusion by itself.

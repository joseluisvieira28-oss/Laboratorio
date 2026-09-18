# LL-0017 — SOURCE SCHEMA CLOSEOUT V0.1A

Date: 2026-09-18
Branch: `ll-0017-positioning-ratio-v0.1`

## Verdict

**SOURCE_SCHEMA_PASS**

This is a source/provenance pass only. It is not an edge, not Discovery and not a trading result.

## Lineage

Original V0.1 run `35365438710` failed `PROVENANCE_FAILURE` because the 2021-01-15 file contained duplicate timestamps.

Frozen diagnostic run `35365589487` proved:
- 576 raw rows;
- 288 unique timestamps;
- every timestamp appeared exactly twice;
- every duplicate pair was byte-identical;
- zero non-identical duplicate groups.

V0.1A normalization was frozen before rerun and permits only collapse of exact byte-identical duplicate raw rows.

## Canonical V0.1A run

- GitHub Actions run: `35365746644`
- Artifact ID: `10555698648`
- Artifact name: `LL0017_POSITIONING_RATIO_SOURCE_SCHEMA_V0_1A`
- Artifact digest: `sha256:953257fcf56ef36f051f6e3d4174dc06efe48e881f15f772399e41b9a032424f`

Frozen probe dates:
- 2021-01-15
- 2022-06-15
- 2023-06-15
- 2024-12-15

All four:
- provider ZIP accessible;
- CHECKSUM accessible and exact;
- identical CSV schema;
- 288 normalized unique timestamps;
- first 00:00 UTC / last 23:55 UTC;
- median and p95 cadence = 300 seconds;
- no non-identical duplicate groups.

Provider header:
`create_time,symbol,sum_open_interest,sum_open_interest_value,count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,count_long_short_ratio,sum_taker_long_short_vol_ratio`

Required distinct positioning fields are therefore structurally present:
- top-trader account ratio = `count_toptrader_long_short_ratio`;
- top-trader position ratio = `sum_toptrader_long_short_ratio`;
- global account ratio = `count_long_short_ratio`.

## Safety

No ratio numeric values parsed or persisted.
No price values opened.
No returns or PnL.
No 2025/2026.
No live trading or exchange mutation.

## Next authorized step

Freeze and execute a 2021-01-01 through 2024-12-31 source coverage census using the same provider route and exact-byte duplicate normalization.

Discovery remains forbidden.

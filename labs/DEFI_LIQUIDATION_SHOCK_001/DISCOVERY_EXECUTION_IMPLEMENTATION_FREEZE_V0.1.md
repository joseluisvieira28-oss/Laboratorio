# DEFI-LIQUIDATION-SHOCK-001 — DISCOVERY EXECUTION IMPLEMENTATION FREEZE V0.1

Date: 2026-09-28
Status: FROZEN / OUTCOME-BLIND / PRE-FIRST-PRICE-ACCESS

## Authority

This implementation freeze is subordinate to and may not relax:
- FINAL_PRE_DISCOVERY_AUTHORITY_PASS
- PRE_DISCOVERY_TEMPORAL_HOLDOUT_FREEZE_V0.1.md
- CASCADE_CLUSTERING_FREEZE_V0.1.md
- SOURCE_SAMPLE_GATE_FREEZE_V0.1.md
- MARKET_DATA_SOURCE_GATE_FREEZE_V0.1.md
- OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md
- MARKET_DATA_MAPPING_SAMPLE_ADEQUACY_ADDENDUM_V0.2.md

It resolves implementation serialization and inference mechanics only. No scientific threshold, horizon, target, split, mapping, control concept, or promotion rule changes.

## Canonical authority chain

Discovery binds to:
- Global Field run 36464851648: GLOBAL_FIELD_COVERAGE_FINAL_PASS
- Sample Gate run 36465385517 / artifact 10988887983: SOURCE_SAMPLE_GATE_PASS
- Market Data Source run 36483390920 / artifact 10997661391: MARKET_DATA_SOURCE_PASS
- Final Pre-Discovery run 36483501137 / artifact 10998125981: FINAL_PRE_DISCOVERY_AUTHORITY_PASS
- mapping registry semantic SHA256: 97ff771dbeb2ec9c3b0a408edd8733701a973ffc1ae597413fbfed4455482f90
- mapping requirements receipt SHA256: b17164cd6735cae47bb3323cb82789ca2fa492f81eb4e70439b281a58a48bbe4

## Discovery market-data boundary

The Discovery executor may download/decompress only Binance public Spot 1m DAILY archives with open timestamps:
- >= the frozen listing boundary for each direct mapped product; and
- < 2024-01-01T00:00:00Z.

No 2024 price payload is opened during Discovery.
No 2025/2026 payload is ever opened.

If an event or control requires a horizon bar at or after 2024-01-01T00:00:00Z, that pair is ineligible under the Discovery split-boundary firewall. The split is not widened.

## Binance source implementation

Primary archive:
`https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{YYYY-MM-DD}.zip`

Companion checksum:
same URL plus `.CHECKSUM`.

Each downloaded ZIP must:
- match the companion SHA256 exactly;
- contain 1m records keyed by exact UTC minute open timestamps;
- have no duplicate open timestamp;
- be strictly monotonic within the archive.

Missing files/minutes are preserved as missing source coverage and never forward-filled.

REST reconciliation endpoint:
`https://data-api.binance.vision/api/v3/klines`

For each accepted symbol/calendar year in Discovery:
- rank archived minute timestamps by SHA256(`symbol|year|timestamp_ms|DLS_RECON_V0.1`);
- select the first 5;
- require REST open timestamp equality and exact Decimal open-price equality.

Any archive checksum mismatch or archive/REST open conflict is fail-closed:
`MARKET_DATA_SOURCE_BLOCKED`.

## Event alignment

For cluster T0:
- A = first exact UTC minute boundary >= T0.
- P0 = OPEN at A.
- Ph = OPEN at A+h for h in 1m, 5m, 30m, 240m.
- r_h = ln(Ph/P0).

No bar close is used.

## Control timestamp canonicalization

The frozen control rule is implemented as follows:
- calendar month and UTC hour-of-day are taken from the exact cascade T0;
- candidate timestamps are exact UTC minute boundaries formatted canonically as `YYYY-MM-DDTHH:MM:00Z`;
- candidate must be within the same Discovery split, at/after product listing boundary, and have all required horizon bars before the Discovery split end;
- candidate must not lie within +/-4 hours, inclusive, of any 60-second primary cascade T0 mapped to the same market.

Control ranking key is the lowercase hexadecimal value of:
`SHA256(UTF8(cluster_id + candidate_timestamp_canonical))`

No delimiter is inserted because the frozen rule specifies concatenation.
Candidates sort lexicographically by the 64-character SHA256 hex digest.
The first candidate with all required bars is selected.
Control reuse across different clusters is allowed because the frozen rule does not prohibit it.

## Overlap / dependence

Primary clusters are not dropped merely because future windows overlap.
The already frozen calendar-day block bootstrap is the explicit dependence-aware treatment:
all matched pairs from the same UTC event-T0 date travel together in every resample.

## Bootstrap implementation

Repetitions: 5,000.

For each split/horizon:
- block key = UTC calendar date of event cascade T0;
- sample the same number of calendar-day blocks with replacement;
- concatenate all pairs belonging to each sampled day, including multiplicity from repeated sampled days;
- statistic = cluster-weighted mean paired difference.

PRNG seed is the full integer value of:
`SHA256("DEFI-LIQUIDATION-SHOCK-001" + split + horizon_label + "V0.1")`.

Percentile CI uses deterministic linear interpolation (Hyndman-Fan type 7) at 2.5% and 97.5%.

One-sided bootstrap p-value for H1 mean(D_h)>0:
`p = (1 + count(bootstrap_mean <= 0)) / (5000 + 1)`.

The three secondary p-values (1m, 30m, 240m) use standard sequential Holm-Bonferroni FWER alpha=0.05.

## Coverage

Discovery paired coverage denominator:
all source-eligible, directly mapped Discovery primary 60-second clusters fixed before price access.

Aggregate eligible-pair coverage must be >=95%.

For every subgroup retained as INFERENTIAL_DISCOVERY_AND_OOS after mapping, eligible-pair coverage must be >=90%.

No unavailable mapping may be replaced by a proxy.

## Discovery verdict

If source integrity or required coverage fails:
`MARKET_DATA_SOURCE_BLOCKED`.

Otherwise apply OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md exactly:
- paired Discovery N >= 1,000;
- mean(D_5m) > 0;
- 95% day-block bootstrap lower bound > 0;
- 5m relative uplift >=10%;
- >=2 inferential protocol families with positive 5m mean D;
- >=2 of 1m/30m/240m with positive mean D;
- >=1 secondary horizon significant after Holm.

All pass:
`SURVIVES_DISCOVERY`.

Otherwise:
`NO_EDGE_DISCOVERY`.

OOS remains unopened until the immutable Discovery receipt is adjudicated.

## Firewall at freeze

prices_opened=false
returns_opened=false
economic_outcomes_opened=false
oos_2024_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false

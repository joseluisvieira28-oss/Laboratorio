# DEFI-LIQUIDATION-SHOCK-001 — DISCOVERY IMPLEMENTATION BINDING V0.1

Date: 2026-09-28
Status: FROZEN IMPLEMENTATION BINDING / PRE-OUTCOME

## Activation authority

This binding is executable only after `FINAL_PRE_DISCOVERY_AUTHORITY_PASS`.
It implements, but does not change, the already-frozen scientific design.

Pinned authority/evidence:
- Source Cluster Sample Gate run: `36465385517`
- Source Cluster Sample Gate artifact: `10988887983`
- `SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json` SHA256: `abfd67aed58ef9a486995d5b211606a7e007ad49eeef8cb9fdf387eff19ac34d`
- `SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson` SHA256: `0a10bf5ff4d7ad41f4764c4c1eb592c28f25b01b0a854b144944adf46363d46b`
- Market Data Source Feasibility run: `36483390920`
- Market Data Source Feasibility artifact: `10997661391`
- `MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json` SHA256: `4537e4e4b85dab3bcd1a79f38b76dafe1c715057f23b28c77f3ba111a0f1e67d`
- frozen mapping registry SHA256: `97ff771dbeb2ec9c3b0a408edd8733701a973ffc1ae597413fbfed4455482f90`
- Final Pre-Discovery Authority run: `36483501137`
- Final Pre-Discovery Authority artifact: `10998125981`
- `FINAL_PRE_DISCOVERY_AUTHORITY_RECEIPT_V0.1.json` SHA256: `1d9ad1290f0cfc7959c709a2623bb09863365ee9ee920358420d086047455d5c`

## Frozen market target

Only the already-authorized direct mapping is inferentially market-mapped in V0.1:
- source target: `mint:So11111111111111111111111111111111111111112`
- canonical asset: SOL
- venue/product: Binance Spot `SOLUSDT`
- primary source: Binance public Spot DAILY 1m archive

No proxy or second asset can be added after outcome access.

## Temporal order

Discovery:
`2021-12-08T00:00:00Z <= T0 < 2024-01-01T00:00:00Z`

OOS:
`2024-01-01T00:00:00Z <= T0 < 2025-01-01T00:00:00Z`

OOS may run only if the immutable Discovery receipt is `SURVIVES_DISCOVERY`.
All market timestamps at or after `2025-01-01T00:00:00Z` are forbidden.

## Price and return implementation

- Resolution: UTC 1-minute bars.
- Event alignment `A`: first exact UTC minute boundary >= source cascade T0.
- `P0`: OPEN at A.
- `Ph`: OPEN at A+h.
- `r_h = ln(Ph/P0)`.
- Frozen horizons: 1m, 5m, 30m, 240m.
- Primary: 5m.
- No close/high/low/volume field is used for the primary outcome.

## Archive acquisition and integrity

For every calendar month containing a directly mapped event, acquire all Binance DAILY `SOLUSDT` 1m archives required for that month. The following month may also be acquired only when it remains inside the same frozen split, solely to support +240m horizons for late-month event/control timestamps.

For each DAILY archive:
- download its companion `CHECKSUM` object;
- verify SHA256 before parsing;
- reject duplicate timestamps;
- reject non-monotonic timestamps;
- require exact UTC minute alignment;
- report missing UTC minutes;
- never forward-fill.

Deterministic REST reconciliation uses up to 8 archived timestamps per calendar year. Timestamp rank is ascending SHA256 of:
`DEFI-LIQUIDATION-SHOCK-001|SOLUSDT|<year>|<timestamp_ms>`.
For each selected timestamp, Binance public Spot `GET /api/v3/klines` 1m is queried. Timestamp must match exactly and OPEN is compared by exact Python `Decimal` numeric equality. REST cannot patch an archive conflict.

Transport-only failover across official public Binance API base hosts is allowed because venue, endpoint semantics, symbol and payload identity are unchanged.

## Matched control serialization

Admissibility follows `OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md` exactly.

For an event cluster, candidates are minute-aligned timestamps in:
- the same frozen split;
- the same calendar month;
- the same UTC hour-of-day;
- outside +/-4 hours (inclusive) of every 60-second primary cascade T0 for the same mapped market;
- with OPEN bars available at 0m, 1m, 5m, 30m and 240m.

Control ranking is ascending SHA256 of the exact UTF-8 bytes:
`cluster_id + candidate_timestamp`
where `candidate_timestamp` is canonical UTC `YYYY-MM-DDTHH:MM:00Z` and there is **no delimiter** between the two fields.
The first ranked admissible candidate is selected. Controls may be reused because the frozen authority does not require unique controls; dependence is handled by the frozen calendar-day block bootstrap.

## Coverage and source-blocking

Before economic classification:
- paired aggregate coverage >=95% of directly mapped source clusters in the split;
- each subgroup still inferential after the frozen mapping validation must have paired coverage >=90%;
- Discovery paired N >=1,000;
- OOS paired N >=500.

Failure of any of these produces `MARKET_DATA_SOURCE_BLOCKED`, not `NO_EDGE`.

The post-mapping subgroup statuses are read from the pinned `MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json`; they are not recomputed from outcomes.

## Dependence-aware bootstrap implementation

- block key: event cascade T0 UTC calendar date;
- repetitions: 5,000;
- all pairs belonging to a sampled day travel together;
- sample block-days with replacement, preserving all pairs inside each sampled day;
- seed text: exact concatenation with no delimiter:
  `DEFI-LIQUIDATION-SHOCK-001` + `<split>` + `<horizon, e.g. 5m>` + `V0.1`;
- PRNG seed integer: first 8 bytes of SHA256(seed text), interpreted unsigned big-endian;
- 95% percentile CI: linear interpolation at positions `p*(N-1)` for p=.025 and .975;
- one-sided supportive bootstrap p-value: `(1 + count(bootstrap_mean <= 0)) / (5000 + 1)`.

Secondary 1m/30m/240m p-values use frozen Holm-Bonferroni family-wise alpha 0.05 with standard step-down ordering.

## Protocol-family guardrail implementation

A protocol is counted toward the `>=2 inferential protocol families positive` rule only when its protocol/class row has a post-mapping status authorized for inference in the relevant split.

Discovery accepts only `INFERENTIAL_DISCOVERY_AND_OOS` rows.
OOS accepts `INFERENTIAL_DISCOVERY_AND_OOS` and `EXTERNAL_CONFIRMATORY_INFERENTIAL` rows.
The protocol-level 5m mean pools only eligible inferential rows within that protocol.

Descriptive-only rows remain in the pooled primary population exactly as frozen, but cannot satisfy the protocol-family guardrail.

## Terminal classifications

Discovery:
- `MARKET_DATA_SOURCE_BLOCKED`
- `NO_EDGE_DISCOVERY`
- `SURVIVES_DISCOVERY`

OOS, only after `SURVIVES_DISCOVERY`:
- `MARKET_DATA_SOURCE_BLOCKED`
- `NO_EDGE_OOS`
- `SURVIVES_OOS`

Sensitivity 15s/300s clustering cannot rescue the primary 60s classification and is not needed to issue the primary V0.1 verdict.

## Frozen no-change rule after first outcome byte

After the first market archive payload is downloaded, do not change:
- target or venue/product;
- split dates;
- cluster rule;
- control rule or control hash serialization;
- horizon family;
- price alignment/field;
- source precedence/checksum rule;
- reconciliation sample rule;
- coverage/sample gates;
- bootstrap settings/seed conversion/CI/p-value method;
- multiplicity rule;
- protocol-family guardrail;
- PASS/FAIL taxonomy.

## Firewall

2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

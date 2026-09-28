# DEFI-LIQUIDATION-SHOCK-001 — DISCOVERY EXECUTION IMPLEMENTATION FREEZE V0.1

Date: 2026-09-28
Status: FROZEN IMPLEMENTATION DETAIL / BEFORE FIRST MARKET-OUTCOME ACCESS

## Authority

This document operationalizes, without changing, FINAL_PRE_DISCOVERY_AUTHORITY_PASS and OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.

It is frozen before the Discovery workflow is launched and before any candle archive is downloaded/decompressed.

## Phase isolation

- Discovery may download/decompress only bars with UTC open timestamps before 2024-01-01T00:00:00Z.
- OOS may execute only after a durable SURVIVES_DISCOVERY receipt and may download/decompress only 2024 bars.
- No required event/control horizon may cross its split end.
- 2025/2026 remains closed.

## Market-data acquisition

For every required SOLUSDT daily Binance Spot 1m archive:
- use the frozen data.binance.vision DAILY route;
- fetch the companion CHECKSUM;
- verify SHA256 before decompression;
- require numeric open timestamp and OPEN;
- require timestamps to be exact UTC minute boundaries;
- reject duplicates and non-monotonic timestamps;
- never forward-fill a missing bar.

A missing archive/bar is treated as prospective market-data missingness. A checksum mismatch, duplicate timestamp, non-monotonic archive, or out-of-day timestamp is a source-integrity conflict and blocks the split.

## REST reconciliation

For each accepted symbol/year in the active split, choose up to 16 archive timestamps by ascending SHA256 of:

DEFI-LIQUIDATION-SHOCK-001 || symbol || year || canonical_UTC_minute

Selection uses timestamp identity only, never price magnitude.

Query the Binance public Spot 1m kline route for exactly that minute and require:
- identical open timestamp;
- Decimal equality of archive OPEN and REST OPEN.

Any reconciliation mismatch blocks the split.

## Event alignment

For cascade T0:
- A = first exact UTC minute boundary >= T0.
- P0 = OPEN(A).
- Ph = OPEN(A+h) for h in 1, 5, 30, 240 minutes.
- A and every required horizon must remain inside the active split.

## Control implementation

For each eligible cluster:
- same direct market;
- same split;
- same calendar month as T0;
- same UTC hour as aligned entry A;
- candidate is an exact minute boundary;
- candidate must be at/after the frozen listing boundary;
- candidate and its 240m horizon must remain inside the split;
- candidate must be more than 4 hours from every primary 60-second cascade T0 for the same market;
- candidate must have OPEN bars at 0, 1, 5, 30 and 240 minutes.

Candidate timestamp canonical form:
YYYY-MM-DDTHH:MM:00Z

Rank candidates by ascending SHA256 of the exact UTF-8 concatenation:

cluster_id || candidate_timestamp

No separator is inserted because the frozen rule specifies direct concatenation.

Select the first admissible candidate. Controls are not forced unique across clusters because the frozen authority did not impose uniqueness.

Bar existence may affect eligibility; price magnitude may not affect control selection.

## Coverage before inference

Before computing any return:
- pooled paired coverage must be >=95% of directly mapped clusters in the active split;
- every subgroup still inferential after market mapping must have >=90% paired coverage;
- paired N must satisfy the frozen split gate.

If not, classify SOURCE_BLOCKED and do not compute economic inference.

## Bootstrap implementation

For each horizon:
- D = |ln(Ph/P0)_event| - |ln(Ph/P0)_control|;
- block key = UTC calendar date of event cascade T0;
- B = 5000;
- resample the set of UTC day blocks with replacement, drawing exactly the observed number of distinct days;
- every pair in a sampled day travels with that day;
- bootstrap mean is the pair-weighted mean over sampled blocks;
- PRNG = Python random.Random seeded by the full unsigned integer represented by
  SHA256("DEFI-LIQUIDATION-SHOCK-001" || split || horizon || "V0.1").

95% percentile CI uses the empirical sorted bootstrap means:
- lower index floor(0.025*(B-1));
- upper index ceil(0.975*(B-1)).

One-sided secondary bootstrap p-value:
(1 + count(bootstrap_mean <= 0)) / (B + 1).

Holm-Bonferroni at alpha 0.05 is applied to 1m, 30m, 240m, sorting by p-value then horizon.

## Classification

Discovery:
- apply OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1 exactly;
- PASS => SURVIVES_DISCOVERY;
- valid-data gate failure => NO_EDGE_DISCOVERY;
- source/coverage failure => SOURCE_BLOCKED.

OOS:
- may run only after SURVIVES_DISCOVERY;
- apply the frozen OOS rules exactly;
- PASS => SURVIVES_OOS;
- valid-data gate failure => NO_EDGE_OOS;
- source/coverage failure => SOURCE_BLOCKED.

No sensitivity cluster result can rescue the 60-second primary result.

## Firewall

live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
protected_2025_2026_opened=false
post_outcome_tuning=false

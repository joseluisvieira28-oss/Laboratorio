# ETH-STAKING-FLOW-001 — V3 SOURCE CLOSEOUT V0.2.4

Date: 2026-09-27
Branch: `eth-staking-flow-v3-source-closeout-v024`

## CANONICAL CURRENT STATE

> **DISCOVERY_INSUFFICIENT_SAMPLE / V3_STAGEA_SOURCE_ACQUISITION_TECHNICAL_FAILURE / REPLICATION_NOT_ADJUDICATED / NO_PROMOTION**

This is **not** `NO_EDGE`.

This is **not** `V3_REPLICATION_FAIL_NO_TIER2_PROMOTION`, because Stage B market outcomes were never opened.

This is **not** `V3_REPLICATED_CORPUS_PASS`.

## IMMUTABLE HISTORICAL DISCOVERY

MVE:
`ESF-NETQUEUE-XATU-7D-003`

Canonical source:
- run `35384444641`
- 630/630 exact source dates
- period 2023-04-12 through 2024-12-31
- daily source series SHA-256:
  `95d225db9c4924852dfbca6333122fc78199092f0cdfd7a0995f4b5530cb2544`

Canonical Discovery:
- run `35387086232`
- artifact `10564142616`
- artifact digest:
  `sha256:fcfb9b547cdd9716fe7043b98209bf39fe95875850db25ddbbfa1f62dc0efa98`
- resolved non-overlapping events: **19**
- frozen minimum: **30**
- mean NET10: **+0.025716111971649736**
- PF NET10: **2.038225339621277**
- stationary-bootstrap one-sided p(mean NET10 <= 0): **0.0988901109889011**

Historical classification remains:

> **DISCOVERY_INSUFFICIENT_SAMPLE**

The positive diagnostics are preserved but do not override the prospectively frozen N>=30 gate.

## V3 INDEPENDENT REPLICATION AUTHORITY

The V3 authority froze before new source/market outcomes:
- R1 = 2025
- R2 = 2026-01-01 through 2026-08-31
- source ceiling = 2026-08-31
- market exit ceiling = 2026-09-08
- unchanged predictor, q80/prior-90 signal, LONG ETHUSDT Spot, t+1 entry, t+8 exit, non-overlap, 10 bps BASE, 20 bps STRESS.

Stage A required exactly **608** source dates before Stage B could open market outcomes.

Original V3 Stage-A run:
`35387477455`

Result:
- 601 valid source dates
- 7 missing dates
- classification:
  `SOURCE_REPLICATION_TECHNICAL_FAILURE`

Frozen missing dates:
- 2025-02-25 — epoch 347963
- 2025-02-26 — epoch 348188
- 2025-02-27 — epoch 348413
- 2025-02-28 — epoch 348638
- 2025-03-01 — epoch 348863
- 2025-10-18 — epoch 400838
- 2025-10-19 — epoch 401063

## SOURCE RECOVERY ATTACK HISTORY

### V0.1.1 — exact transport retry

Run `35394126480`.

The same seven dates remained unavailable.

Result:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

### V0.1.2 — Parquet metadata fallback

Run `35438864217`.

The fallback preserved control-day equivalence, but the seven dates could not be materialized because the exact objects had unusable physical row-group timestamp content.

Result:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

### V0.1.3 — empty-rowgroup fallback

Run `35439191122`.

The exact missing-day objects contained no non-empty row group capable of producing the frozen snapshot:
- 202502: 4 missing dates remained
- 202503: 1 missing date remained
- 202510: 2 missing dates remained

Result:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

### V0.1.4 — historical Beacon-state endpoints

Audit state dated 2026-09-21.

The frozen endpoint set returned historical-state 404/unavailable responses and zero usable control quorum.

Result:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

### V0.1.5 — CBT lifecycle-transition reconstruction

The public Xatu CBT source was investigated prospectively.

The V0.1.9 API-contract remediation later proved the valid endpoint contract:
`https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status`

V0.1.9 run:
`36313857671`

Classification:
`CBT_API_CONTRACT_PASS`

Exact validator IDs 0, 1 and 2 all returned valid lifecycle records with the required schema.

However, the full contract-bound V0.2.0 reconstruction demonstrated that the lifecycle representation is not semantically equivalent to the frozen daily snapshot source.

V0.2.0 run:
`36313994443`

Observed:
- pending_queued lifecycle rows = **54,063**
- active_exiting lifecycle rows = **57,715**
- 608 synthetic dates constructed
- seven missing dates synthetically materialized
- controls exact = **1/3**
- legacy overlap exact = **23/601**
- legacy overlap mismatches = **578/601**
- candidate series SHA-256:
  `4ef9e4adfb1c77becd73c31ddf314d4800c25b71e7c9943f725b35c4b198895b`

Classification:
`SOURCE_PROVENANCE_FAILURE`

Those reconstructed values are rejected and are not admitted to Stage A.

### V0.1.7 / V0.1.8 — independent Parquet readers

DuckDB V0.1.7:
- run `36278800820`
- classification `SOURCE_ACQUISITION_TECHNICAL_FAILURE`

ClickHouse-local V0.1.8:
- run `36313399052`
- engine `clickhouse/clickhouse-server:25.8`
- 3/3 control objects reproduced exactly
- all seven missing `0.parquet` objects yielded zero rows / NULL minimum timestamp

This independently proved the seven missing observations are not a PyArrow/DuckDB parser artifact.

Result:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

### V0.2.1 — exact-epoch fct_validator_balance

The official CBT model is one validator row per epoch and derives directly from `canonical_beacon_validators`.

Run:
`36314264995`

The public REST query path failed under bounded retries with:
`TimeoutError('The read operation timed out')`

No control completed.

Result:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

### V0.2.2 — daily floor-state plus exact lifecycle transitions

Run:
`36314983100`

The method was prospectively frozen to bridge from the published daily floor-epoch state to the frozen first epoch at/after UTC midnight using only actual target-epoch validator transitions.

Result:
- controls exact = **1/3**
- target-epoch lifecycle queries failed to expose transitions required to reconcile the two known control deltas
- classification:
  `SOURCE_PROVENANCE_FAILURE`

No missing-date values were admitted.

### V0.2.3 — ChainSafe Lodestar serial historical-state retry

Authority froze a single-endpoint transport-only retry against:
`https://lodestar-mainnet.chainsafe.io`

Run:
`36315172053`

The very first control request:
`/eth/v1/beacon/states/11127616/validators?status=pending_queued`

was attempted exactly six times.

All six responses:
- HTTP 500
- body:
  `{"code":500,"message":"QUEUE_ERROR_QUEUE_MAX_LENGTH"}`

No control state was opened.
No missing date was opened.
No source value was admitted.

Classification:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`

## SOURCE CONCLUSION

The seven missing canonical source dates remain unresolved under the prospectively authorized public/free source architecture.

Important distinctions:

- the 601 valid Stage-A rows remain valid;
- the seven dates are not imputed;
- no substitute queue definition is accepted;
- no adjacent epoch/day is accepted;
- lifecycle-model reconstructions that failed provenance are rejected;
- no threshold/lookback/horizon/cost/direction rescue is allowed.

Therefore Stage A cannot emit `SOURCE_REPLICATION_PASS`.

## STAGE B

**NEVER OPENED.**

No V3 ETH market outcomes for R1/R2 were opened under this replication lineage.

Therefore:
- R1 event count: **NOT ADJUDICATED**
- R2 event count: **NOT ADJUDICATED**
- R1/R2 NET10: **NOT ADJUDICATED**
- pooled D+R1+R2 N: **NOT ADJUDICATED**
- V3 promotion gates: **NOT ADJUDICATED**

Any pre-armed Stage-B implementation remained dormant because the source PASS gate was not satisfied.

## FINAL VERDICT

- historical Discovery: **DISCOVERY_INSUFFICIENT_SAMPLE**
- historical diagnostics: **POSITIVE / PRESERVED**
- V3 Stage A: **SOURCE_ACQUISITION_TECHNICAL_FAILURE**
- V3 replication economics: **NOT ADJUDICATED**
- NO_EDGE: **NO**
- V3 Tier-2 promotion: **NO**
- Quase Diamante: **NO**
- shadow: **NO**
- micro-live: **NO**
- live trading: **NO**
- main merge: **NO**

Canonical current classification:

> **DISCOVERY_INSUFFICIENT_SAMPLE / V3_STAGEA_SOURCE_ACQUISITION_TECHNICAL_FAILURE / REPLICATION_NOT_ADJUDICATED / NO_PROMOTION**

## REOPEN CONDITIONS

A future source-only lineage may reopen Stage A only if a prospectively frozen authoritative source can materialize the exact seven missing validator snapshots under the unchanged target semantics and passes the frozen controls/provenance gates.

Examples of admissible unlocks:
1. a reliable historical Beacon-state endpoint that serves the exact frozen slots;
2. a direct authoritative ethPandaOps source containing the exact missing validator states;
3. authenticated archive access prospectively frozen before reading missing values;
4. another first-party corpus demonstrably equivalent on the frozen control/overlap gates.

Stage B remains forbidden until the final 608/608 source corpus passes provenance.

No post-outcome rescue is authorized.

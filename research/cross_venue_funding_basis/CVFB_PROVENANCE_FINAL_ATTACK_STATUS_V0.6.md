# CROSS-VENUE FUNDING / BASIS — FINAL SOURCE ATTACK STATUS V0.6

Date: 2026-09-27
Branch: `cross-venue-funding-basis-p0f-final-attack-v0.6`

## CANONICAL CURRENT CLASSIFICATION

**PROVENANCE_RECOVERY_BLOCKED_NOT_NO_EDGE / REPLICATION_INCONCLUSIVE / EDGE_UNPROVEN**

This is not `NO_EDGE`.
This is not `EDGE_SURVIVES`.
The parent full-mechanism replication remains closed and may not be rewritten from diagnostics.

## PARENT FROZEN REPLICATION

Parent branch: `funding-slot-diag-v03`
Parent closeout: `CROSS_VENUE_FUNDING_BASIS_DISCOVERY_FULL_MECHANISM_INCONCLUSIVE_CLOSEOUT_V01.json`

Frozen primary:
- orientation: LONG_BINANCE_SHORT_HYPERLIQUID
- assets: BTC + ETH, both mandatory
- window: 2024-09-01 through 2025-12-31
- equal deployed capital 50/50
- 2026 locked
- no asset dropping
- no reverse-orientation rescue
- no window rescue
- no mark/mid/L2 substitution for missing settlement oracle
- no interpolation / nearest / forward-fill / backward-fill

Support requires BTC > 0, ETH > 0 and combined 50/50 > 0 under complete provenance-quality full-mechanism accounting.

## ECONOMIC DIAGNOSTICS ALREADY OPENED

### Run01 — funding rate/carry diagnostic only

BTC net screen return on immobilized capital:
`+0.00306026078447488584474885844748858447504`

ETH:
`-0.01410840988219178082191780821917808219163`

Combined 50/50:
`-0.005524074548858447488584474885844748858295`

Label:
`RATE_CARRY_SCREEN_NOT_POSITIVE_BOTH_ASSETS`

This diagnostic cannot close the full mechanism because it uses the frozen constant-notional screen rather than complete settlement-notional cashflow.

### Run02B — basis price component diagnostic only

BTC basis component return:
`+0.000065585133885548852867950269506842197362064145086667`

ETH:
`-0.00029457074275614717391217811180153893309661522294`

Combined 50/50:
`-0.00011449280443529916052211392114734836786727553892666`

This diagnostic also cannot close the full mechanism by itself.

## WHY THE FULL MECHANISM REMAINS INCONCLUSIVE

The official Hyperliquid `asset_ctxs` archive on the first frozen day is materially incomplete for the exact settlement-oracle join.

Observed canonical source probe on 2024-09-01:
- source: `s3://hyperliquid-archive/asset_ctxs/20240901.csv.lz4`
- BTC rows: 1018
- ETH rows: 1018
- first timestamp: 00:00 UTC
- last timestamp: 16:58 UTC
- exact top-of-hour slots: 17/24 for BTC and 17/24 for ETH
- required: 24/24
- duplicate exact time/coin pairs: 0

The frozen join requires exact logical settlement-hour matches and tolerance = 0.

Therefore complete settlement-notional funding cashflow cannot be reconstructed from the canonical archive under the frozen rules.

## PROVENANCE RECOVERY ATTACK

### P0 — public Explorer semantic scan

301 frozen blocks around target height 280538302 were scanned.

Result:
`FAIL_NO_NATIVE_ORACLE_SCHEMA_VISIBLE`

No oracle-related key path or oracle-related action/type label was exposed.

### P0D — official public schema audit

Official public documentation establishes:
- validators publish native perp oracle prices;
- `explorer_blocks` and `replica_cmds` are historical node-data surfaces;
- `replica_cmds` contains transaction blocks.

But it does not expose a deterministic native BTC/ETH validator-oracle publish schema or a documented mapping into those historical surfaces.

Result:
`FAIL_PUBLIC_SCHEMA_IDENTITY_UNRESOLVED`

HIP-3 `setOracle` remains explicitly inadmissible as a substitute for the native validator oracle.

### P0E — official replica_cmds requester-pays probe

Authenticated requester-pays access previously succeeded far enough to inspect the frozen path layout, but the exact 2024-09-01 target date was not present under the frozen resolver.

Result:
`TECHNICAL_BLOCKED_TARGET_DATE_NOT_FOUND`

No historical object body was opened.

### P0F — official raw explorer_blocks

The exact frozen P0F remains:
- source: `s3://hl-mainnet-node-data/explorer_blocks`
- keys:
  - `explorer_blocks/200000000/280000000/280538100.rmp.lz4`
  - `explorer_blocks/200000000/280000000/280538200.rmp.lz4`
  - `explorer_blocks/200000000/280000000/280538300.rmp.lz4`
  - `explorer_blocks/200000000/280000000/280538400.rmp.lz4`
- zero LIST
- max 4 HEAD
- max 4 GET
- max 32 MiB compressed
- planning ceiling USD 0.05
- source/schema only; no numeric oracle output and no economics

Prior run 35379993022 reached:
`BLOCKED_NO_AUTHORIZATION: AWS credentials unavailable`

No S3 request was made.

## V0.6 SECRET-ALIAS TRANSPORT ATTACK

Authority frozen before execution:
`CVFB_P0F_SECRET_ALIAS_TRANSPORT_AMENDMENT_V0.6.md`
commit:
`1882ebe05c5d4730497f4cad0166280369f08be7`

The amendment permits the exact same frozen P0F to use an already-existing repository-scoped AWS credential pair under either:
- `CVFB_P0E_AWS_*`
- `L2R_AWS_*`

No credential value may be emitted, transformed, logged or persisted.

Workflow:
`CVFB P0F Final Attack V0.6`

Workflow commit:
`c30b5ec4498bfbb4dc507d6e6ec9bf7a0cb8f463`

Run:
`36282144669`

State at this closeout:
**QUEUED / P0F SOURCE OUTCOME NOT OPENED**

The queued state is not scientific evidence and does not alter the canonical classification.

Independent recent evidence from run 36279222898 also showed the `L2R_AWS_*` aliases empty in that GitHub Actions runtime. The most recent dedicated CVFB readiness receipt likewise showed the CVFB mandatory credential pair absent.

## 2026-09-27 PUBLIC SOURCE RE-AUDIT

A current audit of official Hyperliquid documentation and official GitHub surfaces found no newly documented native BTC/ETH validator-oracle historical publish schema that resolves the frozen provenance boundary.

Current official material still documents:
- historical `asset_ctxs` and L2 archive data as requester-pays and potentially missing;
- `explorer_blocks` and `replica_cmds` as historical node data;
- node `replica_cmds` transaction blocks;
- explicit HIP-3 oracle-update output as a distinct mechanism;
- current `metaAndAssetCtxs` contains `oraclePx`, but no historical-time selector is exposed by that endpoint.

This public re-audit therefore does not unlock deterministic native-oracle reconstruction for 2024-09-01.

## FINAL CURRENT VERDICT

- parent replication: **REPLICATION_INCONCLUSIVE**
- edge: **UNPROVEN**
- rate-carry diagnostic: **NOT POSITIVE BOTH ASSETS**
- basis diagnostic: **COMBINED NEGATIVE**
- complete full-mechanism accounting: **NOT AVAILABLE**
- deterministic native-oracle reconstruction: **NOT PROVEN**
- P0F exact raw-source probe: **AUTHORIZED / PREPARED / CURRENTLY BLOCKED BY AWS RUNTIME ACCESS**
- 2026: **CLOSED**
- paper/live trading: **NO**
- exchange mutation: **NO**
- promotion: **NO**
- micro-live: **NO**
- main merge: **NO**

Canonical classification remains:

> **PROVENANCE_RECOVERY_BLOCKED_NOT_NO_EDGE**

## REOPEN CONDITION

The source-recovery boundary may advance only if one of the following happens without changing the frozen economic contract:

1. the exact P0F four-object official source probe executes with legitimate requester-pays credentials and returns an admissible schema candidate; or
2. Hyperliquid publishes an official deterministic historical mapping for the native BTC/ETH validator oracle sufficient to reconstruct the frozen settlement timestamps; or
3. an authoritative official historical corpus supplies the exact missing native oracle observations with auditable provenance.

A P0F schema candidate would still require a separately frozen identity audit before any numeric reconstruction or economic reopening.

No third-party substitution or post-outcome rescue is authorized.

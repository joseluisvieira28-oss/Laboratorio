# LCOD PROSPECTIVE MECHANICAL STATE OBSERVATION FREEZE V0.1

Frozen: 2026-09-25
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: M2 FORWARD MECHANISM / OUTCOME-BLIND
Parent curve: LCOD_CANONICAL_COLLATERAL_STRESS_CURVE_V0.1

## Scientific purpose

Build a prospective time series of the already-frozen Aave V4 Ethereum
liquidation-convexity state WITHOUT opening any future market or liquidation
outcome.

This stage measures whether the mechanical curve itself varies through time and
whether the complete same-block source pipeline remains reproducible.

It does NOT test predictive edge.

## Forward boundary

The first successful run triggered after this freeze may count as
FORWARD_OBSERVATION_001.

Thereafter the canonical cadence is one scheduled observation per UTC day.

Scheduled cadence:
03:17 UTC daily.

The unusual minute is operational only, to reduce collision with common
top-of-hour infrastructure load. It has zero market hypothesis meaning.

Manual workflow_dispatch runs are DIAGNOSTIC_ONLY and do not increase the
canonical forward-observation count.

Missed scheduled observations are NOT backfilled retrospectively.
Duplicate successful observations on the same UTC date do not create additional
canonical observations.

## Snapshot block

Each run resolves Ethereum tag "finalized" exactly once in the prepare stage.

That block number N and block hash H are immutable for the full snapshot.

Every scientific eth_call MUST use block N.
No latest/current fallback is permitted.

## Population authority

Universe:
the same 13 Ethereum Aave V4 lending Spokes already frozen for LCOD.

Historical borrower discovery:
- canonical Borrow event;
- range begins at block 24,720,899;
- source route = @subsquid/evm-stream@0.1.5 over the official SQD Ethereum
  dataset endpoint already validated by the source gate;
- history is split into exactly 16 contiguous chunks through N.

Active pair definition:
(spoke,user) has getUserAccountData(user).totalDebtValueRay > 0 at N.

Population PASS requires:
- exactly 16 chunks;
- exact contiguous coverage from 24,720,899 through N;
- all chunks on the same N/H;
- zero Borrow decode errors;
- zero UAD errors;
- active/inactive partition complete and disjoint;
- at least one active pair.

Raw wallet addresses remain runtime-memory only.
Durable artifacts may retain only SHA-256 pair identifiers or aggregate hashes.

## Component reconstruction

For the exact active pair set at N, apply the already-frozen
FULL_SAME_BLOCK_COMPONENT_RECONSTRUCTION_V0.1 semantics without modification.

Required PASS:
- reproduced active-set SHA exactly;
- 100% of active pairs receive block-N UAD classification;
- count coverage >= 90%;
- debt coverage >= 90%;
- exact totalDebtValueRay reconstruction for every INCLUDED pair;
- reconstructed HF relative error <= 5e-5;
- no imputation;
- all scientific calls block-pinned to N.

## Mechanical curve

Apply the already-frozen canonical collateral-only shock operator.

Frozen stress grid:
0.00%, 0.25%, 0.50%, 0.75%, 1.00%, 1.50%, 2.00%, 3.00%, 5.00%.

Do not:
- alter the grid;
- pick a preferred shock point after observing snapshots;
- shock debt oracle values;
- introduce asset-specific correlations;
- use floating-point borrower crossing decisions.

The complete vector is retained at every observation.

## Durable forward snapshot

Each passing snapshot persists only:
- observation role;
- captured UTC time;
- Ethereum block number/hash;
- population counts and active-set SHA;
- component coverage and component-row-set SHA;
- total active debt ValueRay;
- baseline counts/debt;
- complete frozen curve points;
- exact curve SHA;
- source/workflow provenance;
- explicit outcome-closure flags.

Raw wallet addresses are forbidden.
The 2,000+ per-pair component rows are retained only as workflow evidence
artifacts and represented durably by a deterministic SHA-256.

## Predictor-only accumulation gate

Before any market/liquidation outcome experiment may be designed from this
forward series, require BOTH:
- >= 30 canonical successful daily forward observations;
- >= 21 distinct UTC calendar days represented.

At that gate, predictor-only inspection may evaluate:
- source stability;
- missingness;
- active population variation;
- total-debt variation;
- full nine-point curve variation;
- slope/curvature variation.

No market return, liquidation-event outcome, direction, PnL or profitability
may be opened during this accumulation gate.

No single shock point may be selected because it looked interesting in the
first canonical curve or later forward snapshots. Any later predictive
experiment must pre-register its predictor transform and outcome definition
before outcomes are opened.

## Promotion firewall

FORWARD_MECHANICAL_SNAPSHOT_PASS earns zero trading-edge promotion credit.

This stage authorizes observation only.

Forbidden:
- live trading;
- orders;
- exchange mutation;
- wallet mutation;
- market-return inspection for this hypothesis;
- liquidation-outcome inspection for this hypothesis;
- post-outcome tuning;
- main merge without explicit authorization.

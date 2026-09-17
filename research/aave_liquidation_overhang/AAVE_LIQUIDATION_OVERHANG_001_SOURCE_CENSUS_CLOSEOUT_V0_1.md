# AAVE-LIQUIDATION-OVERHANG-001 — SOURCE CENSUS CLOSEOUT V0.1

Date: 2026-09-17  
Branch: `aave-liquidation-overhang-v0.1`

## Verdict

**SOURCE_CENSUS_PASS**

This is a structural-source verdict only. It is not an edge, not Discovery, not a trading result, and does not authorize health-factor/overhang calculation or outcomes.

## Canonical execution

GitHub Actions run: `35214027573`  
Source-census head: `fb3166253c4dcff62f4811964e9fb95cd94d2cc3`  
Canonical artifact: `10493989498`  
Artifact digest: `sha256:1d132e46c4bf10590fe5be5af7d76f0519c83970217858ae00abf568ecf61b9b`

Transport: SQD Ethereum mainnet Portal, used only to reproduce Ethereum log structure across the frozen envelope.

Frozen exact block envelope:
- from: `16,490,000`
- through: `21,525,890`
- hard timestamp ceiling: `2024-12-31T23:59:59Z`

The envelope was split into eight fixed disjoint contiguous shards after a monolithic transport run exceeded CI wall-clock limits. The aggregate verified exact no-gap/no-overlap coverage before passing.

## Structural population recovered

Total unique canonical `(transactionHash, logIndex)` identities: **2,072,691**.

Event counts:
- `Supply`: 295,190
- `Withdraw`: 198,848
- `Borrow`: 204,952
- `Repay`: 131,443
- `LiquidationCall`: 5,539
- `ReserveDataUpdated`: 863,030
- `ReserveInitialized`: 37
- `ReserveUsedAsCollateralEnabled`: 205,904
- `ReserveUsedAsCollateralDisabled`: 158,595
- `UserEModeSet`: 9,153

Participant coverage:
- unique position users: **63,514**
- unique liquidated users: **2,223**
- unique borrowers observed: 30,691
- unique suppliers observed: 59,325

The census therefore proves a large historical borrower/liquidation population exists before any economic predictor is constructed.

## Transport receipt

Across the sharded run:
- HTTP attempts: 2,937
- successful Portal responses: 2,751
- transient retries: 186
- network retries: 0
- Portal rows traversed: 647,525

The high transient-retry count confirms why the earlier monolithic public-Portal approach was unsuitable, but all eight frozen shards ultimately reached their exact terminal blocks and passed.

## Safety receipt

The canonical receipt records:
- `log_data_requested=false`
- `economic_values_decoded=false`
- `health_factor_computed=false`
- `overhang_computed=false`
- `future_liquidation_outcome_computed=false`
- `market_prices_opened=false`
- `returns_opened=false`
- `pnl_opened=false`
- `accessed_2025_or_2026=false`
- `live_trading=false`
- `exchange_mutation=false`

## Authority released

This pass releases only the already-frozen `AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_GATE_AUTHORITY_V0_1`.

Next allowed work:
- decode canonical historical source values required for borrower-state reconstruction;
- enumerate reserve/token/oracle/upgrade/configuration history;
- prove scaled collateral/debt replay and point-in-time source provenance.

Still forbidden until that gate passes and a separate final pre-Discovery protocol is frozen:
- health-factor based overhang predictor;
- adverse-shock selection;
- future liquidation outcomes;
- market returns or PnL;
- 2025/2026;
- live trading or exchange mutation.

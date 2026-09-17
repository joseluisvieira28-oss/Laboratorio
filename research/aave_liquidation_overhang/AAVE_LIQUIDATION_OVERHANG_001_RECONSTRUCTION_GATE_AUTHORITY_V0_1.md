# AAVE-LIQUIDATION-OVERHANG-001 — BORROWER-STATE RECONSTRUCTION GATE AUTHORITY V0.1

Status: **FROZEN / DORMANT UNTIL SOURCE_CENSUS_PASS / OUTCOME-BLIND**  
Date: **2026-09-17**  
Branch: `aave-liquidation-overhang-v0.1`

## 1. Activation condition

This authority is dormant unless the preceding structural census records `SOURCE_CENSUS_PASS` for the exact frozen Ethereum mainnet envelope through 2024-12-31.

A census pass authorizes only point-in-time source reconstruction. It does **not** authorize liquidation-overhang calculation, future liquidation outcomes, market returns, PnL, trading, 2025/2026 data or any threshold selection.

## 2. Purpose

Prove that a borrower-level Aave V3 Ethereum state can be reconstructed at historical snapshots without current-state substitution, survivorship leakage or future information.

The reconstruction must be sufficient to reproduce, at each allowed historical snapshot, the ingredients later required by Aave health-factor mathematics:
- reserve universe and reserve identities;
- scaled collateral balances;
- scaled variable-debt balances;
- reserve liquidity and variable-borrow indices;
- collateral-enabled flags;
- user eMode category;
- reserve LTV/liquidation-threshold/decimals and relevant eMode parameters;
- Aave oracle identity/source mapping and point-in-time asset prices.

No future liquidation event may be consulted while constructing a snapshot.

## 3. Historical protocol constraint

Aave V3 Ethereum activated as V3.0.1 with stable-rate borrowing not enabled on the main Ethereum V3 instance. Therefore V0.1 reconstruction treats user debt as variable debt only, but this assumption must be checked against the historical `Borrow.interestRateMode` population before any health-factor calculation. Any observed stable-rate borrow in the frozen Ethereum V3 population causes fail-closed review rather than silent omission.

## 4. Canonical event/state families

### Pool / PoolConfigurator
Required event history includes:
- `ReserveInitialized`
- `ReserveDataUpdated`
- `ReserveUsedAsCollateralEnabled`
- `ReserveUsedAsCollateralDisabled`
- `UserEModeSet`
- `Borrow`
- `Repay`
- `LiquidationCall`
- configuration-change events sufficient to reconstruct historical liquidation threshold, LTV, decimals, reserve activity and eMode membership/configuration.

### aTokens
For every reserve discovered point-in-time from `ReserveInitialized`, fetch the corresponding aToken event history.

Required transfer primitive:
- `BalanceTransfer(address indexed from,address indexed to,uint256 value,uint256 index)`

`BalanceTransfer.value` is the scaled amount. It must be used to account for user-to-user aToken transfers and liquidation transfers so collateral ownership is not inferred only from Pool `Supply`/`Withdraw` events.

Mint/burn handling must be version-aware. V0.1 may use Pool action events plus the contemporaneous reserve index, or token Mint/Burn events, only if a deterministic reconciliation proves identical scaled balance deltas on an audit sample. No current `balanceOf()` may be backfilled historically.

### Variable debt tokens
Variable debt is non-transferable. For every discovered reserve, reconstruct scaled debt changes from version-correct variable-debt token Mint/Burn events or from Pool Borrow/Repay/Liquidation events plus the contemporaneous variable-borrow index. The selected method must be reconciled against the alternative on an audit sample before pass.

### Oracle
Historical Aave prices must follow the point-in-time oracle actually referenced by the PoolAddressesProvider.

Required provenance:
- `PriceOracleUpdated` events on the PoolAddressesProvider;
- AaveOracle `AssetSourceUpdated` and fallback changes;
- price-feed observations available by the snapshot timestamp only.

Using today's oracle/source mapping retroactively is forbidden.

## 5. Version-awareness requirement

The reconstruction may not apply the current Aave implementation ABI/rounding/configuration semantics indiscriminately to all 2023-2024 history.

It must identify relevant implementation/configuration upgrade boundaries and use semantics compatible with the implementation active at each historical event. At minimum, the gate must prove compatibility across any Pool, PoolConfigurator, aToken or variable-debt-token implementation upgrades intersecting the frozen envelope.

If an upgrade changes event semantics needed for reconstruction and the transition cannot be deterministically bridged, result = `RECONSTRUCTION_PROVENANCE_FAILURE`.

## 6. Snapshot clock

This gate does not choose a Discovery predictor threshold or outcome horizon.

For reconstruction verification only, use deterministic audit snapshots from the frozen 2023-2024 source period. Snapshot blocks must be selected without inspecting future liquidations or market returns. The eventual Discovery snapshot clock will be frozen separately after this gate passes.

## 7. Required reconciliation tests

Before `RECONSTRUCTION_DATA_PASS`, all must pass:

1. **Reserve identity:** token addresses and reserve IDs are recovered point-in-time without present-day membership filtering.
2. **Coverage:** all required source families span their active historical intervals through 2024-12-31.
3. **Scaled collateral conservation:** replayed scaled aToken balances never become materially negative; transfers debit/credit exactly the same scaled amount.
4. **Scaled debt conservation:** replayed variable debt never becomes materially negative and non-transferability is respected.
5. **Collateral flags:** enabled/disabled state changes are time ordered and compatible with reconstructed holdings.
6. **eMode:** each user's category is reconstructed only from events/state available at the snapshot; category configuration changes are version-aware.
7. **Reserve indices:** liquidity and variable-borrow indices are time ordered and non-decreasing except where an officially documented protocol transition proves otherwise.
8. **Oracle provenance:** price source mapping is point-in-time; every price used has an observation timestamp <= snapshot timestamp.
9. **Independent validation sample:** for a prospectively selected deterministic set of historical blocks/users, reconstructed account ingredients must agree with a legitimate historical state query or an independent canonical data representation if such a route is available. No user/block may be selected because it produces a better fit.
10. **Protected-period firewall:** no 2025/2026 source, liquidation, price or return is accessed.

## 8. Allowed decoded values

Only after `SOURCE_CENSUS_PASS`, this gate may decode source values necessary to validate state reconstruction: Pool/token amounts, scaled balances, indices, configuration parameters, eMode IDs and oracle observations within the frozen source period.

Still forbidden:
- calculating the liquidation-overhang predictor;
- selecting an adverse-shock size;
- computing next-period liquidation notional as an outcome;
- opening market prices for trading outcomes;
- calculating returns, PnL, win rate, PF or drawdown;
- opening 2025/2026.

## 9. Pass/fail classifications

Permitted terminal states:
- `RECONSTRUCTION_DATA_PASS`
- `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`
- `RECONSTRUCTION_PROVENANCE_FAILURE`
- `RECONSTRUCTION_INSUFFICIENT_COVERAGE`
- `RECONSTRUCTION_RECONCILIATION_FAILURE`

`NO_EDGE` is forbidden here.

A pass permits creation of a separately frozen `FINAL_PRE_DISCOVERY_PROTOCOL`. It does not itself authorize Discovery.

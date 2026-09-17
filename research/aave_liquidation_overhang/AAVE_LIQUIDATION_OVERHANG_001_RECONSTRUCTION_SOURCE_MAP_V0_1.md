# AAVE-LIQUIDATION-OVERHANG-001 — RECONSTRUCTION SOURCE MAP V0.1

Date: 2026-09-17  
Status: **DESIGN RECORD / DORMANT UNTIL SOURCE_CENSUS_PASS**

This file records canonical source relationships only. It does not authorize decoding, health-factor calculation, overhang calculation, outcomes or Discovery.

## Stable root

Ethereum mainnet Aave V3 PoolAddressesProvider:
`0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`

The provider is the historical root for connected protocol addresses. Current address-book values may be used only as a cross-check, never as a substitute for point-in-time history.

## Historical address/config transitions

Reconstruct from provider events, including at minimum:
- `PoolUpdated(address,address)`
- `PoolConfiguratorUpdated(address,address)`
- `PriceOracleUpdated(address,address)`
- `AddressSetAsProxy(...)` / `ProxyCreated(...)` when relevant to implementation provenance.

For the oracle active at a historical block, reconstruct its own source mapping from canonical AaveOracle events:
- `AssetSourceUpdated(address,address)`
- `FallbackOracleUpdated(address)`
- base-currency identity/unit from the implementation active for that oracle instance.

No present-day `getSourceOfAsset()` or address-book source may be copied backwards across time without event/state proof.

## Reserve discovery and token identity

Reserve membership is event-driven, beginning from Configurator `ReserveInitialized`:
- underlying asset;
- aToken proxy;
- stable-debt-token proxy (identity retained even if borrowing mode is not active);
- variable-debt-token proxy;
- interest-rate strategy.

Track token implementation changes from Configurator upgrade events:
- `ATokenUpgraded`
- `StableDebtTokenUpgraded`
- `VariableDebtTokenUpgraded`

The reconstruction must not filter the historical universe by the current reserve list.

## aToken state primitive

Canonical user-to-user ownership movement requires aToken:
`BalanceTransfer(address indexed from,address indexed to,uint256 value,uint256 index)`

For the V3-era interface, `value` is explicitly the **scaled amount**. This event is required because Pool `Supply`/`Withdraw` alone cannot reconstruct collateral ownership after transferable aTokens move between addresses or during aToken-receiving liquidations.

Mint/Burn semantics must be replayed with the implementation active at the event. A burn may emit a Mint when accrued interest exceeds the requested burn amount; raw ERC20 Transfer values therefore cannot be naively interpreted as principal deltas.

## Variable debt state primitive

VariableDebtToken is non-transferable. Its balance is scaled principal multiplied by the reserve normalized variable-debt index.

V0.1 reconstruction must derive scaled debt deltas using version-correct debt-token Mint/Burn events or Pool Borrow/Repay/Liquidation plus the contemporaneous variable-borrow index, and reconcile the two approaches on a prospectively selected audit sample.

## Stable-rate firewall

The Ethereum V3 main instance was launched without stable-rate borrowing enabled. Nevertheless, every historical Pool `Borrow.interestRateMode` encountered in the frozen period must be inspected after reconstruction decoding is authorized. Any stable-mode borrow is a fail-closed exception requiring explicit treatment rather than silent deletion.

## Risk configuration required for health-factor ingredients

The later reconstruction must retain point-in-time changes sufficient to reproduce:
- reserve decimals;
- LTV;
- liquidation threshold;
- collateral enabled/disabled state;
- reserve active/frozen/paused status where it affects validity;
- user eMode category;
- eMode category parameters and reserve/category membership.

Configuration state must be reconstructed from the contemporaneous Configurator/Pool implementation and its event history; current configuration cannot be applied retroactively.

## Version boundaries

Pool, PoolConfigurator, aToken and debt-token proxies are upgradeable. Implementation transitions inside the frozen 2023-2024 envelope are first-class source events.

The gate must either:
1. replay each interval with semantics matching the implementation active in that interval; or
2. prove that the source fields used by V0.1 are semantically invariant across every intersecting upgrade.

No 'latest ABI everywhere' assumption can earn `RECONSTRUCTION_DATA_PASS` without that proof.

## Oracle observation rule

A price observation is valid for a historical snapshot only when:
- the oracle instance is proven active at that snapshot;
- the asset->source mapping is proven active at that snapshot;
- the underlying feed observation was available at or before the snapshot;
- decimals/base currency are resolved point-in-time;
- fallback behavior is handled exactly if the primary source was non-positive/unavailable under the active implementation.

The reconstruction gate remains outcome-blind. These prices are source ingredients for historical Aave account state, not market-return outcomes.

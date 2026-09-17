# AAVE-LIQUIDATION-OVERHANG-001 — HISTORICAL STATE PROVENANCE ADDENDUM V0.3

Date: 2026-09-17  
Branch: `aave-liquidation-overhang-v0.1`  
Status: **FROZEN BEFORE EXECUTION / SOURCE-ONLY / OUTCOME-BLIND**

## Why this addendum exists

The V0.1 and V0.2 oracle-bootstrap probes both failed to recover any PoolAddressesProvider oracle-registry transition from the SQD Ethereum stream. V0.2 already admitted both canonical mutation routes — `PriceOracleUpdated(old,new)` and `AddressSet(bytes32('PRICE_ORACLE'),old,new)` — yet the provider log surface returned zero matching transitions from provider creation through the first reserve activation.

This is a provenance-source limitation, not an economic result. No health factor, liquidation-overhang predictor, future liquidation outcome, market return, PnL or 2025/2026 source has been opened.

The frozen reconstruction authority already requires an independent historical-state validation route where available. V0.3 therefore adds a narrow, independent on-chain state proof for the oracle registry at activation. It does not change the sample, hypothesis, predictor, direction, horizon, costs or promotion criteria.

## Frozen activation facts and identities

- scientific sample: `16,490,000..21,525,890`
- first canonical `ReserveInitialized` block recovered before this addendum: `16,496,792`
- pre-activation comparison block: `16,496,791`
- PoolAddressesProvider: `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`
- expected Pool: `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`
- expected PoolConfigurator: `0x64b761D848206f447Fe2dd461b0c635Ec39EBb27`
- expected AaveOracle: `0x54586bE62E3c3580375aE3723C145253060Ca0C2`
- AaveOracle creation block: `16,291,123`

## Frozen independent RPC set

The following public Ethereum RPC endpoints are fixed before execution:

1. `https://ethereum-rpc.publicnode.com`
2. `https://eth.llamarpc.com`
3. `https://1rpc.io/eth`
4. `https://eth.drpc.org`
5. `https://rpc.ankr.com/eth`

Endpoint availability is not itself evidence. An endpoint that explicitly cannot serve historical state is classified as unsupported for this probe.

## Historical-state pass rule

For each endpoint, query at the exact historical block tags only:

- `eth_chainId` must be Ethereum mainnet (`0x1`);
- `eth_getBlockByNumber(16,496,792)` must return a block;
- `eth_getCode` for the provider and expected oracle at activation must be non-empty;
- `eth_call` on the provider for `getPriceOracle()`, `getPool()` and `getPoolConfigurator()` at block `16,496,792`;
- `eth_call getPriceOracle()` again at block `16,496,791`.

A state route is admissible only if at least **two independent frozen endpoints** successfully serve the historical calls and all successful endpoints agree on the same activation block hash and decoded contract values.

Required decoded activation values:

- `getPriceOracle()` = frozen expected AaveOracle;
- `getPool()` = frozen expected Pool;
- `getPoolConfigurator()` = frozen expected PoolConfigurator.

If successful endpoints disagree on any decoded value or block hash, result = `RECONSTRUCTION_PROVENANCE_FAILURE`.

If fewer than two endpoints can serve the historical state, result = `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`.

## Exact-block log cross-check

Using the same frozen endpoint set, query exact-block logs only:

- first `ReserveInitialized` evidence at block `16,496,792` from the PoolConfigurator;
- `AssetSourceUpdated` evidence from the expected AaveOracle at block `16,496,792`;
- `BaseCurrencySet` evidence from the expected AaveOracle at its creation block `16,291,123`;
- provider `PriceOracleUpdated` / exact `AddressSet(PRICE_ORACLE,...)` at block `16,496,792` as a conditional ordering aid if the pre-activation state differs from activation state.

At least two frozen endpoints must successfully serve the exact-block log queries and agree on the canonical log identities/counts used by the probe. Any disagreement is a provenance failure; fewer than two usable log endpoints is a technical failure.

## Boundary-state rule

Preferred proof: `getPriceOracle()` already equals the expected oracle at block `16,496,791` and remains equal at `16,496,792`.

If the pre-activation value differs, V0.3 does **not** silently pass. It may pass only if a canonical provider oracle-registry transition is independently recovered in block `16,496,792` and is ordered before the first `ReserveInitialized` log. Otherwise provenance remains failed.

## Firewalls unchanged

Still forbidden:

- health factor calculation;
- liquidation-distance / overhang calculation;
- adverse-shock threshold selection;
- future liquidation outcome;
- market-return prices;
- returns, PnL, win rate, PF or drawdown;
- 2025/2026 access;
- live trading, orders, wallets or exchange mutation;
- merge to `main`.

A V0.3 pass proves oracle/provider provenance only. It does not by itself grant `RECONSTRUCTION_DATA_PASS`.

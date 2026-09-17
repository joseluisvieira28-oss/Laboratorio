# AAVE-LIQUIDATION-OVERHANG-001 — ORACLE BOOTSTRAP PROVENANCE ADDENDUM V0.2

Date: 2026-09-17  
Branch: `aave-liquidation-overhang-v0.1`  
Status: **FROZEN BEFORE RERUN / SOURCE-ONLY / OUTCOME-BLIND**

## Why this addendum exists

The first oracle-bootstrap probe required `PoolAddressesProvider.PriceOracleUpdated(old,new)` as the only admissible registry transition. It recovered no such event. A source-code audit performed after that technical failure, while all outcome firewalls remained closed, identified a second canonical registry mutation path in the same historical Aave V3 `PoolAddressesProvider` implementation:

- `setPriceOracle(address)` updates `_addresses[PRICE_ORACLE]` and emits `PriceOracleUpdated`;
- generic `setAddress(bytes32,address)` updates the same `_addresses[id]` map and emits `AddressSet(id,old,new)`.

The implementation freezes `PRICE_ORACLE` as the bytes32 literal `'PRICE_ORACLE'`.

Therefore V0.2 corrects the **source-event route only**. It does not change the scientific sample, hypothesis, predictor, outcome, direction, horizon, costs, promotion gates or any economic definition.

## Canonical provider transition rule

For oracle-registry reconstruction, accept a transition only when it is one of:

1. `PriceOracleUpdated(address oldAddress,address newAddress)`; or
2. `AddressSet(bytes32 id,address oldAddress,address newAddress)` **with `id == bytes32('PRICE_ORACLE')` exactly**.

Any other `AddressSet` id is irrelevant to oracle provenance and must not be used.

## Provider provenance envelope

- PoolAddressesProvider creation block: `16,291,071`
- frozen scientific reconstruction envelope remains: `16,490,000..21,525,890`
- provider registry provenance may be read from creation forward solely to bootstrap/replay configuration state.
- 2025/2026 remain forbidden.

## Activation ordering gate

The provider does not need a non-zero oracle before the market is initialized. Therefore the R0 gate is refined prospectively as follows:

1. derive the first canonical `PoolConfigurator.ReserveInitialized` block from Ethereum logs;
2. reconstruct all oracle-registry transitions from provider creation through that block;
3. require the latest oracle registry value at the first `ReserveInitialized` to equal the frozen canonical Aave V3 Ethereum Oracle identity `0x54586bE62E3c3580375aE3723C145253060Ca0C2`;
4. require the oracle transition to occur no later than the first `ReserveInitialized` block;
5. reconstruct subsequent oracle-registry transitions throughout the frozen 2023-2024 envelope using the same two canonical event routes.

This does not move the sample start. Pre-activation empty blocks remain in the source envelope; they simply have no initialized lending market state to evaluate.

## Oracle contract bootstrap

For the event-derived active oracle, recover from its creation block through the first reserve initialization:
- `AssetSourceUpdated`;
- `FallbackOracleUpdated`;
- `BaseCurrencySet`.

Require at least one `AssetSourceUpdated` and one `BaseCurrencySet` before or at activation. Current address-book state is cross-check only and may not substitute for historical events.

## Firewalls unchanged

Still forbidden at this stage:
- health factor calculation;
- liquidation-distance / overhang calculation;
- adverse-shock threshold selection;
- future liquidation outcome;
- market-return prices;
- returns, PnL, win rate, PF or drawdown;
- 2025/2026 access;
- live trading, orders, wallets or exchange mutation;
- merge to `main`.

Allowed output remains reconstruction/provenance evidence only.

# AAVE-LIQUIDATION-OVERHANG-001 — ORACLE BOOTSTRAP PROVENANCE AUTHORITY V0.1

Date: 2026-09-17  
Branch: `aave-liquidation-overhang-v0.1`  
Status: **SOURCE-ONLY / RECONSTRUCTION-ONLY / OUTCOME-BLIND**

## Purpose

The frozen R0 reconstruction envelope begins at Ethereum block `16,490,000`. The R0 oracle component correctly failed closed because no `PriceOracleUpdated` event occurred inside that envelope, so the oracle address active at the left boundary could not be inferred from in-window transitions alone.

This authority permits one narrow bootstrap-provenance recovery before the left boundary. It does **not** enlarge the scientific sample or authorize predictor/outcome computation.

## Frozen bootstrap provenance envelope

- bootstrap start block: `16,291,123`
- bootstrap end block: `16,489,999`
- scientific/reconstruction sample still begins: `16,490,000`
- scientific/reconstruction sample still ends: `21,525,890`

The bootstrap start is anchored to the verified Ethereum creation block of the canonical Aave V3 Ethereum Oracle `0x54586bE62E3c3580375aE3723C145253060Ca0C2`.

Canonical identity references used to freeze this remediation before execution:
- Aave official Address Book: Ethereum V3 PoolAddressesProvider `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`, Pool `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`, PoolConfigurator `0x64b761D848206f447Fe2dd461b0c635Ec39EbB27`, Oracle `0x54586bE62E3c3580375aE3723C145253060Ca0C2`.
- Ethereum explorer provenance for the Oracle reports creation block `16,291,123`.

These references are identity cross-checks only. The active-at-boundary oracle must still be proven from historical Ethereum events; current address-book state may not be substituted backwards.

## Required proof

1. Recover canonical PoolAddressesProvider `PriceOracleUpdated(old,new)` events in the bootstrap envelope.
2. Define the active oracle at block `16,490,000` as the `new` address in the latest such event strictly before that block.
3. Require that historical-event-derived address to equal the canonical Aave V3 Ethereum Oracle identity above; mismatch = `RECONSTRUCTION_PROVENANCE_FAILURE`.
4. Recover the active oracle's `AssetSourceUpdated`, `FallbackOracleUpdated`, and `BaseCurrencySet` events from its creation block through `16,489,999`.
5. Require at least one `AssetSourceUpdated` and one `BaseCurrencySet` bootstrap event so per-asset source and base-currency state can be replayed at the first scientific snapshot.
6. Continue using normal in-window provider/oracle transitions for blocks `16,490,000..21,525,890`; current-state substitution is forbidden.

## Firewalls

This remediation may decode protocol configuration/provenance only.

Still forbidden:
- health factor calculation;
- liquidation-distance or overhang calculation;
- selecting an adverse shock threshold;
- future liquidation outcome;
- external market price returns;
- PnL / win rate / PF / drawdown;
- 2025 or 2026;
- live trading, orders, wallets or exchange mutation;
- merge to `main`.

This authority changes transport/provenance coverage only. It does not change the hypothesis, predictor, outcome, sample period, future horizon, costs, direction or promotion rules.

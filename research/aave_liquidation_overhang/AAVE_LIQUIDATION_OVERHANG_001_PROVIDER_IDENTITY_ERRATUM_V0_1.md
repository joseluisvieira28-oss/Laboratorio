# AAVE-LIQUIDATION-OVERHANG-001 — PROVIDER IDENTITY ERRATUM V0.1

Date: 2026-09-17  
Branch: `aave-liquidation-overhang-v0.1`  
Status: **FROZEN BEFORE CORRECTED RERUN / SOURCE-ONLY / OUTCOME-BLIND**

## Finding

A deterministic address-length audit after the V0.3 technical failure found that the PoolAddressesProvider constant used by the reconstruction probes was malformed by one missing hexadecimal character.

Incorrect value used in failed probes:

`0x2f39d218133afb8f2b819b1066c7e434ad94e9e`

This has only 39 hexadecimal characters after `0x` and is not a valid Ethereum address.

Canonical Aave V3 Ethereum value, independently verified against the official Aave Address Book and Etherscan verified contract:

`0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`

Normalized lowercase:

`0x2f39d218133afab8f2b819b1066c7e434ad94e9e`

Pool, PoolConfigurator and AaveOracle identities remain unchanged.

## Scientific consequence

All prior conclusions that depended on querying PoolAddressesProvider logs or historical state using the malformed address are invalidated as source-provenance evidence. Their receipts/runs remain preserved as failed technical history and must not be deleted or reinterpreted as negative protocol evidence.

This correction is an identity/input bug fix discovered before any health factor, overhang, future liquidation outcome, market return or PnL was opened. It does not change the hypothesis, sample, predictor, direction, horizon, costs or promotion rules.

## Corrected rerun order

1. Re-run the canonical SQD provider/oracle provenance gate using the corrected provider address and the already-frozen V0.2 admissible event routes:
   - `PriceOracleUpdated(old,new)`;
   - `AddressSet(bytes32('PRICE_ORACLE'),old,new)` exactly.
2. Only if the corrected SQD route remains unavailable, re-run the independent historical-state RPC route using the corrected provider identity.
3. No R1 reconstruction begins until oracle/provider provenance is actually passed.

## Firewalls

Still forbidden:
- health factor;
- liquidation-overhang calculation;
- adverse-shock selection;
- future liquidation outcomes;
- market-return prices;
- returns/PnL;
- 2025/2026 market data;
- live trading or exchange mutation;
- merge to `main`.

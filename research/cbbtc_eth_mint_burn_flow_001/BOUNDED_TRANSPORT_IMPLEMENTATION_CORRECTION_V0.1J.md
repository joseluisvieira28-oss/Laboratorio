# CBBTC-ETH-MINT-BURN-FLOW-001 — BOUNDED TRANSPORT IMPLEMENTATION CORRECTION V0.1J

Frozen: 2026-09-27
Parent: FULL_CENSUS_BOUNDED_TRANSPORT_V0.1I
Scope: TRANSPORT IMPLEMENTATION ONLY

## Reason

Static audit before relaunch found two implementation inconsistencies in the bounded Gate-2 transport:
- the census implementation still declared a 10,000-block outer chunk although V0.1I froze 2,000 blocks;
- raw log acquisition referenced LOG_RPCS without defining it.

## Correction

- Set Gate-2 outer eth_getLogs chunk to exactly 2,000 blocks.
- Define LOG_RPCS as [RPC], preserving the frozen primary PublicNode log source only.
- No alternate log provider is added.
- Existing explicit HTTP timeouts and bounded retries remain unchanged.

## Scientific invariants

UNCHANGED:
- Ethereum mainnet cbBTC contract;
- zero-address Transfer mint/burn definition;
- 2024-09-12 through 2026-01-01 exclusive census;
- exact UTC daily ledger;
- EIP-1898 supply reconciliation;
- q10/q90 calibration rules;
- H2-2025 sample gate;
- frozen BTC 24h Discovery;
- 2026 firewall;
- no PnL, live trading, orders, wallets, exchange mutation or main merge.

Promotion credit = 0.

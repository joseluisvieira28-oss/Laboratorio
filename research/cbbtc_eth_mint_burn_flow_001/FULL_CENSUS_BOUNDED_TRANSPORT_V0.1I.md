# CBBTC-ETH-MINT-BURN-FLOW-001 — FULL CENSUS BOUNDED TRANSPORT V0.1I

Frozen: 2026-09-27
Parent: FULL_CENSUS_RPC_TIMEOUT_REMEDIATION_V0.1G
Scope: TRANSPORT ONLY — Gate 2 outcome-blind census.

## Trigger

The canonical V0.1G single-run exhausted its 240-minute runner budget before Gate 1 completed. Before any future Gate-2 execution, the same bounded-transport discipline is applied to the already-frozen full census so an RPC stall cannot consume the continuation runner without a deterministic gate result.

## Transport-only changes

UNCHANGED science:
- 2024-09-12 through 2026-01-01 exclusive census;
- exact Ethereum cbBTC contract;
- zero-address mint/burn semantics;
- exact UTC daily ledger;
- EIP-1898 totalSupply blockHash anchors;
- exact start/end supply reconciliation;
- zero duplicate/decode/source-error gates;
- supply-normalized predictor;
- calibration/Discovery rules;
- 2026 firewall;
- no PnL/live trading/main merge.

Bounded transport:
- outer eth_getLogs chunk reduced from 20,000 to 2,000 blocks;
- all raw RPC calls retain explicit timeout, reduced to 10 seconds;
- header/archive/range retries are bounded before exact midpoint splitting/fail-closed;
- progress logging is increased;
- no block/day/event is skipped, sampled, imputed or interpolated.

Promotion credit = 0.

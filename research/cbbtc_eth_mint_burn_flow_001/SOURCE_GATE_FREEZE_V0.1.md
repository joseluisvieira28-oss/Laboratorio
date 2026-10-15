# CBBTC-ETH-MINT-BURN-FLOW-001 — SOURCE GATE FREEZE V0.1

Frozen: 2026-09-26
Lab ID: CBBTC-ETH-MINT-BURN-FLOW-001
Primary family: FLOW
Secondary family: SUPPLY
Governance: RESEARCH-ONLY / OUTCOME-BLIND SOURCE GATE

## Economic object

Coinbase Wrapped BTC (cbBTC) is a 1:1 BTC-backed wrapped asset.

Official Ethereum contract:
0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf

This lab asks whether canonical on-chain cbBTC creation/redemption flow can be reconstructed densely enough to support a later predictive-flow experiment.

This source gate DOES NOT test price prediction.

## Canonical flow definition

Use only ERC-20:
Transfer(address indexed from, address indexed to, uint256 value)

Mint:
from == 0x0000000000000000000000000000000000000000

Burn:
to == 0x0000000000000000000000000000000000000000

No exchange-wallet heuristics.
No address clustering.
No Coinbase internal-account inference.
No bridge-flow substitution.

## Network

Ethereum mainnet only.

Base / Arbitrum / Solana are out of scope for this exact lab.

## Fixed source-probe windows

Window A — launch-era:
2024-09-12T00:00:00Z <= block timestamp < 2024-10-12T00:00:00Z

Window B — mature:
2025-06-01T00:00:00Z <= block timestamp < 2025-07-01T00:00:00Z

Block bounds must be resolved by Ethereum timestamps, not guessed.

## Data source

Primary public source:
https://ethereum-rpc.publicnode.com

Required evidence:
- exact block number/hash/timestamp for each resolved boundary;
- eth_getLogs against the official cbBTC contract;
- Transfer topic exact;
- zero-address topic exact;
- transaction hash + log index retained;
- raw uint256 amount decoded exactly;
- duplicate txHash/logIndex count = 0.

## Source PASS

SOURCE_PASS requires ALL:

1. contract code exists at both probe-window ending blocks;
2. token decimals() and symbol() calls succeed at current finalized/latest state;
3. Window A returns >=1 zero-address Transfer event;
4. Window B returns >=1 zero-address Transfer event;
5. combined windows contain >=1 mint AND >=1 burn;
6. every retained log belongs to the exact official cbBTC contract;
7. every retained log has exactly the Transfer signature and expected indexed topics;
8. zero decode errors;
9. zero duplicate txHash/logIndex pairs;
10. no latest/current substitution for historical logs.

## Source BLOCKED

SOURCE_BLOCKED if:
- historical logs are unavailable;
- zero-address creation/redemption cannot be reconstructed;
- only one side (mint or burn) exists across both fixed windows;
- provenance is incomplete;
- provider limits cannot be overcome by transport-only chunking/backoff.

## Technical remediation allowed

Allowed without changing science:
- reduce eth_getLogs block-span;
- deterministic retries/backoff;
- sequential requests;
- alternate public/keyless Ethereum RPC transport while preserving identical logs and block bounds.

Forbidden:
- changing the two windows after seeing counts;
- replacing zero-address flow with ordinary transfers;
- adding Base/Arbitrum/Solana to rescue sample;
- opening BTC/cbBTC price returns;
- threshold selection;
- PnL;
- live trading;
- main merge.

## Next allowed step

Only SOURCE_PASS may authorize an outcome-blind historical flow census.

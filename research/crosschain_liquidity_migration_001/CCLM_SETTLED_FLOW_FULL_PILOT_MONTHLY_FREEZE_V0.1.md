# CCLM-CCTP-SETTLED-FLOW-002 — FULL FROZEN PILOT MONTHLY SCALE V0.1

Frozen: 2026-09-24
Parent historical pilot: CCTP V1 Ethereum <-> Avalanche, 2023-05-01 through 2024-12-31.
Market outcomes: CLOSED.

## Trigger

- one-day settled-flow smoke: PASS, 7 canonical flows, 0 semantic mismatches;
- seven-day scale: PASS, 87 canonical flows, 0 semantic mismatches.

The historical period is NOT selected from these source counts. It is inherited
from CCTP_V1_HISTORICAL_PILOT_FREEZE_V0.1, frozen before acquisition.

## Scale plan

Run one independent source receipt per calendar month:
2023-05 through 2024-12 inclusive.

Canonical event remains unchanged:
destination MessageReceived + same-transaction MintAndWithdraw with exact
source domain, TokenMessenger sender, V1 burn body, native USDC token,
recipient and amount.

## Monthly classifications

SOURCE_SETTLED_FLOW_MONTH_PASS:
- both chain transports complete;
- zero semantic mismatch among candidate canonical events.
A month may legitimately have zero canonical flows and still pass source
transport/semantics; zero is not imputed or rescued.

SOURCE_SETTLED_FLOW_MONTH_TECHNICAL_FAILURE:
- unresolved transport/decoding failure.

## Aggregate source pass

FULL_HISTORICAL_SETTLED_FLOW_SOURCE_PASS requires:
- all 20 calendar months present;
- no monthly technical failure;
- zero semantic mismatches across the aggregate;
- no 2025/2026 access.

This proves a historical completed-flow corpus can be reconstructed. It earns
ZERO predictive or promotion credit and opens no price/liquidity/PnL outcome.

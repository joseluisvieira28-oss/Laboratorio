# CBBTC-ETH-MINT-BURN-FLOW-001 — OUTCOME-BLIND FLOW CENSUS FREEZE V0.1

Frozen: 2026-09-26
Parent: SOURCE_GATE_FREEZE_V0.1
Execution condition: SOURCE_PASS only.

## Purpose

Build a complete Ethereum cbBTC zero-address mint/burn ledger and daily flow series without opening BTC/cbBTC price outcomes.

## Frozen census period

Start:
2024-09-12T00:00:00Z

End exclusive:
2026-01-01T00:00:00Z

2026 is protected and MUST NOT be read by this census.

## Canonical events

Same exact source semantics as SOURCE_GATE_FREEZE_V0.1:

Mint:
Transfer(from=0x0, to, amount)

Burn:
Transfer(from, to=0x0, amount)

Official Ethereum cbBTC contract only:
0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf

No normal transfers.
No wallet labels.
No Base/Arbitrum/Solana.

## Daily state

UTC calendar days.

For each day retain:
- mint event count;
- burn event count;
- gross mint raw amount;
- gross burn raw amount;
- signed net raw amount = mint - burn;
- gross absolute flow = mint + burn;
- first/last event block when present;
- zero-event day explicitly retained as zero, not missing.

No price field may be joined.

## Exact ledger requirements

PASS requires:
- exact timestamp-resolved census boundaries;
- all block ranges scanned with zero unhandled source errors;
- all zero-address Transfer logs decoded;
- duplicate txHash/logIndex count = 0;
- chronological ledger ordering;
- every event assigned to the UTC day of its exact block timestamp;
- daily rows contiguous from 2024-09-12 through 2025-12-31;
- deterministic ledger SHA-256;
- deterministic daily-series SHA-256.

## Allowed descriptive outputs

Outcome-blind only:
- total mints/burns;
- total raw minted/burned;
- active-flow day count;
- zero-flow day count;
- min/max/mean daily signed net flow;
- quantiles of daily signed net flow;
- quantiles of daily gross flow.

These statistics earn zero edge credit.

## Forbidden

- BTC returns;
- cbBTC market returns;
- price joins;
- forward labels;
- direction fitting;
- event threshold selection for trading;
- PnL;
- 2026 access;
- live trading.

## Next gate

Only PREDICTOR_FLOW_CENSUS_PASS can authorize a separately frozen calibration/state definition before any price outcome is opened.

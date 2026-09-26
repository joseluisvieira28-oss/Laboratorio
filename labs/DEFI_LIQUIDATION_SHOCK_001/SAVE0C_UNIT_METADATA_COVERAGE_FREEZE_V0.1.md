# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C UNIT METADATA COVERAGE FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Population

Frozen Save0c realized population: 66,628 events over
[2021-12-08T00:00:00Z, 2025-01-01T00:00:00Z).

Canonical key:
`save0c + LiquidateObligation + signature + instructionAddress`

No event may be added or removed based on metadata coverage.

## Direct event metadata

For every exact successful Save0c liquidation:
- debt underlying token identity: accounts 0 and 3 must yield the same single mint+decimals pair;
- collateral token identity: accounts 1 and 5 must yield the same single mint+decimals pair;
- withdraw reserve identity: account 4.

Use exact d1=0x0c + isCommitted + transactionTokenBalances.
Request tokenBalance identity/unit fields only:
account, transactionIndex, preMint, postMint, preDecimals, postDecimals.

No token amounts.

## Collateral underlying mapping V0.1

Use pinned official SDK production snapshot:
`SAVE0C_2021_PRODUCTION_RESERVE_REGISTRY_V0.1.json`

For a mapped withdraw reserve:
- collateral underlying mint+decimals comes from the pinned reserve→asset registry;
- observed collateral-token mint must equal the pinned collateral mint.

Unmapped reserves are NOT guessed and remain explicitly listed.

## Verdict taxonomy

Exact event join and direct metadata must always be complete.

If all 66,628 events map through the pinned reserve registry:
`SAVE0C_UNIT_METADATA_POPULATION_PASS`

If event join/direct metadata pass but one or more withdraw reserves are absent from the 2021 snapshot:
`SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE`

Any canonical mismatch, token metadata conflict, or mapped reserve collateral-mint conflict:
`SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED`

Partial coverage is a source-registry gap, not NO_EDGE.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
token_balance_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false

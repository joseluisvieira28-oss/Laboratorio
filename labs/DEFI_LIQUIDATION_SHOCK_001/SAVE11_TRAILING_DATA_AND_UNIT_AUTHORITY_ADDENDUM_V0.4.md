# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 TRAILING DATA & UNIT AUTHORITY ADDENDUM V0.4

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Trigger

Original Save11 population field/unit passes were incomplete even though canonical event identity remained exact.

Observed frozen population facts:
- canonical missing = 0;
- canonical extra = 0;
- fixed account count remains 15;
- successful instruction discriminator remains 0x11;
- instruction data lengths observed are 9 and 10 bytes;
- unit conflicts are sparse token-metadata absence on user-side transfer accounts, not mint contradictions.

No prices, returns, PnL, direction, USD notional, token amounts or protected outcomes were opened to establish this addendum.

## Source authority — instruction payload

Official public Solend SDK source constructs:
- discriminator u8;
- liquidityAmount u64;
for a nominal 9-byte payload and the same 15 fixed accounts.

Repository:
`solendprotocol/public`
Path:
`solend-sdk/src/instructions/liquidateObligationAndRedeemReserveCollateral.ts`

Relevant 2024 source commits include:
- d01b24d70b24638bc8544a34e3c244918f797122 — 2024-08-06
- a92a5c3b1b03b49724e5aebd61270e7e5d61251a — 2024-09-09

Archival Solend Rust decoder lineage independently shows the on-chain instruction decoder for tag 17 uses:

`let (liquidity_amount, _rest) = Self::unpack_u64(rest)?;`

and discards `_rest`.

Its `unpack_u64` requires at least 8 bytes and returns the remainder without requiring it to be empty.

Therefore, for the frozen successful Save11 population, one trailing byte after the canonical discriminator + u64 payload is decoder-ignored trailing data. The recovery does NOT assign any semantic meaning to that trailing byte and MUST NOT emit its value.

## Frozen field rule

For Save11 only:

- account count MUST equal 15;
- discriminator MUST equal 0x11;
- instruction data byte length MUST be exactly 9 or 10;
- canonical argument schema remains `liquidityAmount:u64`;
- trailing byte count may be 0 or 1 only;
- trailing byte value is not decoded, emitted or used;
- canonical event identity/population must remain unchanged.

Any other length or account shape is fail-closed.

## Source authority — unit metadata

Official Solend SDK account semantics identify:
- source liquidity account 0 against repay reserve liquidity supply account 4;
- destination collateral account 1 against withdraw reserve collateral supply account 7;
- destination reward/underlying liquidity account 2 against withdraw reserve liquidity supply account 8.

For unit identity, protocol-controlled reserve supply accounts are the PRIMARY authority:

- debt_underlying: primary account 4; optional user cross-check account 0;
- collateral_token: primary account 7; optional user cross-check account 1;
- collateral_underlying: primary account 8; optional user cross-check account 2.

PRIMARY must expose exactly one (mint, decimals) pair.

Optional user cross-check:
- zero metadata pairs: allowed and reported unavailable;
- exactly one pair: MUST equal PRIMARY;
- more than one pair or a different pair: fail-closed.

This rule resolves metadata availability only. It does not read token amounts or economic outcomes.

## Required recovery

Re-run all six Save11 partitions prospectively under this frozen authority:
- save11-202407
- save11-202408
- save11-202409
- save11-202410
- save11-202411
- save11-202412

Required per partition:
- field canonical missing=0;
- field canonical extra=0;
- field duplicates=0;
- field semantic/source conflicts=0;
- unit canonical missing=0;
- unit canonical extra=0;
- unit conflicts=0;
- every event has all three unit roles resolved.

## Population terminal

Field:
`KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS`

Unit:
`KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS`

Exact total remains:
- Save11 successful liquidations: 13,300

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
token_balance_amounts=false
requested_amount_values=false
trailing_byte_value_emitted=false
protected_market_outcomes_2025_2026=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false

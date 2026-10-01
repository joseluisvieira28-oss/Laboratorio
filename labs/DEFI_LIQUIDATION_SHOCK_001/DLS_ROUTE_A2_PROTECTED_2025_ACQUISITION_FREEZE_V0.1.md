# DLS ROUTE A2 — PROTECTED 2025 ARCHIVAL ACQUISITION FREEZE V0.1

Date: 2026-10-01
Status: FROZEN SOURCE-ONLY / PROTECTED 2025 MARKET OUTCOMES CLOSED

## Authority
Parent: DEFI-LIQUIDATION-SHOCK-001
Scientific source contract: PROTECTED_2025_SOURCE_AUTHORITY_FREEZE_V0.1.md
Alternative source gate: DLS_ALTERNATIVE_SOURCE_EQUIVALENCE_GATE_V0.1.md

Empirical Route A2 equivalence:
- run 36900517788
- artifact 11181427969
- artifact ZIP SHA256 1d9a597c60a730eecc2c0c3b5aace08f396d70a8d3947a3600c361649a430c80
- classification ALTERNATIVE_SOURCE_EQUIVALENCE_PASS
- FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_PASS
- exact semantic coverage: marginfi, save0c, kamino, save11
- blockers: none

## Purpose
Acquire the complete frozen 2025 source-event population through the empirically equivalent Helius archival RAW route, without opening any market outcome.

This changes transport only. It does not change:
- program IDs;
- discriminators;
- account roles;
- success semantics;
- collateral-unit semantics;
- 60-second clustering;
- target SOL mint;
- strategy direction;
- timing;
- costs;
- statistical gates.

## Window
2025-01-01T00:00:00Z <= transaction blockTime < 2026-01-01T00:00:00Z.

Partition manifest:
exactly 48 partitions = 4 frozen protocols x 12 UTC calendar months.

Protocols:
- marginfi / lending_account_liquidate
- save0c / LiquidateObligation
- kamino / liquidate_obligation_and_redeem_reserve_collateral
- save11 / LiquidateObligationAndRedeemReserveCollateral

## Transport
Credential: existing HELIUS_API_KEY secret in GitHub Actions. Never print/hash/persist the value.

Allowed RPC methods only:
- getSignaturesForAddress
- getTransaction
- getMultipleAccounts

Pagination:
- program address
- finalized
- limit 1000
- deterministic descending cursor using before
- continue until lower month boundary is crossed
- no page/sample cap that can be interpreted as completeness
- non-advancing cursor, missing blockTime, duplicate signature or transport exhaustion => partition BLOCKED

For each candidate successful program transaction:
- fetch version-0 capable getTransaction JSON
- reconstruct canonical account vector including loaded addresses
- reconstruct instruction paths using validated stackHeight semantics
- apply canonical frozen discriminator + shape rules
- emit only matching liquidation instruction rows

## Unit resolution
Use exact already-frozen 2025 semantics:
- marginfi: collateral bank accounts[1], finalized bank slice offset 8 length 33
- save0c: withdraw reserve accounts[4], finalized reserve slices 42/33 and 227/32
- kamino: accounts[8] direct collateral-underlying mint under fixed V1.6+ layout
- save11: token-balance metadata primary accounts[8], optional accounts[2] exact-match only

No token amounts, oracle values, prices or economic values are required or retained.

## Partition PASS
A partition is PROTECTED_2025_PROTOCOL_SOURCE_PASS only if:
- pagination reaches the month lower boundary;
- all candidate metadata have explicit status;
- all matching instructions satisfy canonical shape;
- all relevant collateral units resolve;
- zero duplicate canonical (signature,instructionAddress);
- zero source conflicts/errors.

Empty liquidation partitions may PASS only after complete program-address pagination proves zero matching frozen discriminator events in the month.

## Global finalization
Reuse the frozen scientific finalizer semantics:
- require exactly 48 month receipts;
- all 48 PASS;
- exact intervals;
- union all rows;
- fail on duplicate canonical identity;
- identical 60-second clustering over the full union;
- exclude T0 >= 2026-01-01;
- target SOL mint unchanged.

Terminal source classification:
PROTECTED_2025_SOURCE_AUTHORITY_PASS or PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED.

Only PASS authorizes the already-frozen 2025 economic holdout.

## Firewall
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
funding_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE

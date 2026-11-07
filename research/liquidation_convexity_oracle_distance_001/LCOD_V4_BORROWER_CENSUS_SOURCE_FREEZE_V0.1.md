# LCOD V4 BORROWER CENSUS SOURCE FREEZE V0.1

Date: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: SOURCE COVERAGE ONLY

## Question

Can the official Aave MCP borrow-holder index be deterministically paginated across every currently indexed V4 reserve to produce a finite, deduplicated borrower population without opening any liquidation or market outcome?

## Frozen census

- get_markets(version=v4) -> exact reserveId population observed at run time.
- For every reserveId:
  - get_reserve_holders(side=borrow, limit=50, version=v4)
  - first page has no cursor
  - subsequent pages use exactly nextCursor from prior response
  - continue until no non-empty nextCursor.
- Deduplicate valid 0x40 wallet addresses across all reserve pages.
- Persist only SHA-256 wallet identities, not raw addresses.

## Fail-closed

BLOCK if any:
- required tools missing;
- a reserve query errors;
- cursor repeats on one reserve;
- page count exceeds 1000 for one reserve;
- malformed nextCursor semantics prevent deterministic termination;
- reserve population changes inside the run in a way that cannot be reconciled.

## PASS

CENSUS_INDEX_SOURCE_PASS requires:
- every reserve returned by the frozen initial get_markets call is visited;
- zero reserve errors;
- zero cursor loops;
- all pages terminate naturally;
- at least one deduplicated borrower exists;
- receipt records reserve/page/row counts and hashed borrower set.

This proves the indexed Aave MCP holder population is enumerable.
It does NOT prove the index itself is protocol-exhaustive versus raw chain state.

No health factors, liquidation outcomes, market returns or PnL are opened.

# LCOD BORROW-EVENT BLOCK CENSUS V0.3 — PER-SPOKE BOUNDED REMEDIATION

Frozen: 2026-09-25
Stage: SOURCE / POPULATION COMPLETENESS
Outcomes: CLOSED

## Trigger

Two earlier all-history aggregate SQD queries returned zero Borrow logs, but an
exact historical Borrow fixture on BLUECHIP at block 25398769 returned the same
single event through:
- Blast archive RPC;
- SQD Ethereum portal.

Therefore zero-event results are classified as query-shape/transport failure,
not protocol absence.

Separately, exact first-code deployment blocks for all 13 official Ethereum V4
lending Spokes were pinned by binary-searching eth_getCode and passed.

## V0.3 remediation

Do NOT issue one multi-address genesis query.

For each of the 13 official lending Spokes independently:
- fromBlock = pinned first_code_block;
- toBlock = one finalized Ethereum block N chosen at run start;
- address = exactly one Spoke;
- topic0 = Borrow(uint256,address,address,uint256,uint256);
- SQD query returns Borrow logs only.

Union all decoded (spoke,user) pairs.

## Contradiction check

Independently enumerate current Aave MCP V4 borrow holders.
Require every current (spoke,user) pair to exist in the event-derived union.

## Block-N active filter

For every event-derived (spoke,user) pair, call getUserAccountData(user) at the
same exact finalized block N.

ACTIVE iff totalDebtValueRay > 0.

## PASS

BORROW_EVENT_BLOCK_CENSUS_PASS_V03 requires:
- all 13 independent SQD spoke queries complete;
- total Borrow log count > 0;
- zero topic/user decode errors;
- 100% coverage of current MCP borrower×spoke pairs by Borrow history;
- zero unresolved block-N account-data call failures;
- at least one active-debt pair at N.

No raw wallet address is persisted.
No curve or market/liquidation outcome is opened.

# LCOD BORROW-EVENT TRANSPORT CLOSEOUT V0.1

Date: 2026-09-25
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: SOURCE TRANSPORT
Market/liquidation outcomes: CLOSED

## Truth fixture

A known historical Aave V4 BLUECHIP Borrow event at Ethereum block 25398769,
transaction:
0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f

Borrow topic0:
0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd

The exact one-block fixture is independently visible through:
- Blast public archive RPC: PASS;
- SQD Portal exact-block query: PASS.

Therefore address/topic semantics are proven and historical Borrow data exists.

## Raw SQD /stream POST

Large raw POST queries returned only a first stream batch rather than the full
requested historical range.

A response-shape diagnostic showed:
- response = NDJSON/list of 20 block objects;
- first batch for BLUECHIP began at deployment block 24720920;
- last object in that response was block 24721758;
- no claim that this one response completed through the requested toBlock.

Previous zero-log mega/per-spoke results are therefore INVALID as evidence that
Borrow history is empty. They are preserved as transport/query-shape failures.

## Public RPC range matrix

The historical truth fixture was probed across public Ethereum RPC routes.

Result:
PUBLIC_RPC_RANGE_ROUTE_BLOCKED.

Notable constraints:
- Blast public: historical truth works, but eth_getLogs is limited to 10 blocks;
- 1RPC reports a 50-block limit and public-rate constraints;
- Cloudflare reports max 800 blocks but historical fixture calls did not return
  a defensible passing route;
- PublicNode historical archive requires a personal token;
- OnFinality/Merkle public routes rate-limited;
- no tested free public RPC passed the frozen >=1001-block practical range gate.

Using Blast in 10-block chunks across the full 13-Spoke history is rejected as
operationally disproportionate while a first-party stream client exists.

## Canonical remediation route

Use the official SQD SDK:
@subsquid/evm-stream@0.1.5

Its DataSourceBuilder.getStream() consumes Portal batches/continuations rather
than interpreting one raw /stream response as the complete historical range.

The currently authorized source gate must still require:
- full SDK stream completion;
- known truth fixture present;
- 100% current-MCP borrower×spoke coverage by event history;
- zero decode/MCP errors.

Until that gate passes:
POPULATION_COMPLETENESS remains BLOCKED.

No curve, future market outcome, liquidation outcome, PnL or trading execution
was opened by these transport tests.

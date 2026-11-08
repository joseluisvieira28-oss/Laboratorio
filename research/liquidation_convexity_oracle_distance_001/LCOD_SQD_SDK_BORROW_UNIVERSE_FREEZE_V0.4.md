# LCOD SQD SDK BORROW-UNIVERSE GATE V0.4

Frozen: 2026-09-25
Stage: SOURCE / BORROWER UNIVERSE
Outcomes: CLOSED

## Remediation basis

Raw POST requests to the SQD Portal `/stream` endpoint returned only one
stream batch at a time. The official SQD `@subsquid/evm-stream` SDK exposes
`DataSourceBuilder.getStream()`, which iterates the complete stream and handles
batch continuation internally.

SDK is pinned for this gate:
- @subsquid/evm-stream = 0.1.5

## Official protocol authorities

Aave V4 source:
- aave/aave-v4 @ 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

Aave Ethereum address book:
- aave-dao/aave-address-book @ f08dbd218a1da7ea1ac3bb0e387652fdb9f98042

Use exactly the 13 official lending Spokes in ALL_SPOKES.

Borrow topic:
0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd

## Deterministic source procedure

1. Enumerate current Aave MCP v4 borrow-holder pairs first.
2. After MCP enumeration finishes, read Ethereum latest block L from Blast.
3. Stream Borrow logs from min(pinned spoke deployment blocks) through L using
   the official SQD SDK and the 13 exact addresses + Borrow topic filter.
4. Canonical pair = lowercase(spoke) + "::" + indexed Borrow user.
5. Confirm the pre-existing historical BLUECHIP truth fixture transaction
   0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f
   is present.
6. Compare current MCP pair set with the streamed event-derived pair set.

Durable evidence stores hashes/counts only, never raw wallet addresses.

## PASS

SQD_SDK_BORROW_UNIVERSE_PASS requires:
- SDK stream completes normally through L;
- >=1 Borrow event;
- known truth fixture present;
- zero undecodable Borrow logs;
- all 13 spokes represented in query manifest;
- every current MCP borrow-holder pair is in Borrow-event history (100% coverage);
- no MCP enumeration error.

PASS proves the event-history route is a defensible superset for debt-population
construction. It does not yet classify which historical pairs are active at one
finalized block.

No curve or market/liquidation outcome is opened.

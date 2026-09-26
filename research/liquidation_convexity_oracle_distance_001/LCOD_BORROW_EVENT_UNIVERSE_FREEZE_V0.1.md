# LCOD BORROW-EVENT UNIVERSE SOURCE GATE V0.1

Frozen: 2026-09-25
Stage: SOURCE / BORROWER UNIVERSE
Outcomes: CLOSED

## Motivation

LCOD has already proven:
- 98.7002% current live component reconciliation coverage across 2,385 debt-bearing borrowers;
- exact HF parity for 16 / 16 borrower×spoke pairs at one identical finalized Ethereum block.

The remaining source problem is borrower-universe completeness at a pinned block.
A current MCP holder list cannot by itself prove point-in-time completeness.

## Official event authority

Pinned Aave V4 source:
aave/aave-v4 @ 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

ISpoke emits:
Borrow(
  uint256 indexed reserveId,
  address indexed caller,
  address indexed user,
  uint256 drawnShares,
  uint256 drawnAmount
)

The indexed user is the owner of the debt position.

Pinned Aave Ethereum V4 address book:
aave-dao/aave-address-book @ f08dbd218a1da7ea1ac3bb0e387652fdb9f98042

Use exactly ALL_SPOKES (13 lending spokes), excluding treasury/tokenization spokes.

## Frozen fixture

1. choose latest finalized Ethereum block N at start;
2. retrieve all Borrow logs from the 13 pinned ALL_SPOKES from genesis through N
   using an append-only public Ethereum archive/datalake route;
3. canonical borrower key = lowercase(spoke) + "::" + lowercase(indexed user);
4. independently enumerate current v4 borrow holders from Aave MCP;
5. compare pair sets using hashes only in durable evidence.

## PASS

BORROW_EVENT_UNIVERSE_SOURCE_PASS only if:
- event source returns >=1 Borrow event;
- every current MCP borrower×spoke pair is present in the event-derived universe;
- current-pair coverage = 100%;
- zero undecodable event topic/user;
- all 13 pinned lending spokes are represented in the source query manifest,
  even if a spoke has zero Borrow events;
- no market/liquidation outcome is opened.

Passing proves the event source is a defensible superset route for constructing
a point-in-time debt universe. It does not by itself prove which historical
borrowers still have debt at N; that requires block-N getUserAccountData.

No curve is authorized by this gate.

# BITGET MAKER MICROSTRUCTURE V0.2 — PRE-OUTCOME EXECUTION FREEZE

Date: 2026-10-05
Status: FROZEN BEFORE MICROSTRUCTURE OUTCOMES

## Authority

Parent cross-venue family:
- Run `37239207816`
- Artifact SHA256 `8ff31989d819783091bccac08f73936cfd7c942f19c23e02205c8c51d0171358`
- Verdict: `MAKER_ONLY_FEE_SURVIVORS_FOUND__FILL_MODEL_REQUIRED`

All four carried-forward candidates remain:
- HOODUSDT
- COINUSDT
- ARMUSDT
- AAPLUSDT

Route is fixed:
`BINANCE_LEADER__BITGET_TARGET`

Public trades source:
- Run `37239649192`
- Artifact SHA256 `348a5c5a7b6e910f220948cbfe0255406bb3e477c0c1bc5a0d7846756838d64d`

Historical Bitget depth:
- Transport run `37240398478`
- Artifact SHA256 `56eb5974893b6dfd8ad40dd37e60326d5957ed70ed3c8203c4b2b07550599551`
- Strict XLSX schema run `37240564117`
- Artifact SHA256 `1cccfb5ffd9181f8ff5168caa5654e235d3b246a3bf4d533d9312a45909fa328`
- Level1 schema: timestamp, ask_price, bid_price, ask_volume, bid_volume
- Level500 schema: timestamp, asks, bids

The source-verification date 2026-09-16 is burned and is not used as a microstructure outcome date.

## Scope

This is a **conditional execution-feasibility test** on the already-selected parent window 2026-08-17 through 2026-09-04.

It is NOT claimed as a new independent OOS scientific validation.

The underlying signal remains exactly:
- Binance 1m shock >= 5 bps
- Binance minus Bitget 1m lag gap >= 3 bps in the same direction
- FOLLOW_BINANCE
- 1-minute horizon
- 1-minute cooldown
- signal window 14:31–18:44 UTC

## Frozen passive model

At signal close:
- deterministic strategy latency = 1 second;
- use the latest Bitget Level1 snapshot at or before the intended placement time;
- snapshot age must be <=5 seconds or the signal is data-unverifiable;
- long entry posts at best bid;
- short entry posts at best ask;
- queue ahead equals **100% of displayed Level1 volume** at that price;
- cancellations never reduce queue ahead;
- own order size is treated as de minimis because this study measures bps and queue clearance, not capacity;
- entry TTL = 10 seconds.

A maker fill occurs only when:
- cumulative public trade size at the exact posted price clears the frozen queue ahead; OR
- the public tape trades through the posted price, which would be impossible without consuming the hypothetical order first.

Unfilled entry after 10 seconds is cancelled and creates no position.

Exit clock is fixed at signal close +60 seconds, preserving the original one-minute horizon:
- 1 second deterministic exit latency;
- long exit posts at current best ask;
- short exit posts at current best bid;
- same full displayed queue-ahead model;
- exit TTL = 10 seconds.

If the maker exit does not fill:
- force a taker exit at the exit TTL;
- close long at current best bid;
- close short at current best ask;
- quote age <=5 seconds required.

No position may be silently dropped merely because the maker exit failed.

Fees:
- maker = 2 bps/side;
- taker = 6 bps/side;
- maker-maker = 4 bps round trip;
- maker-taker = 8 bps round trip.

Actual entry/exit quote prices incorporate spread.

## Frozen execution gate

Per asset:
- parent-signal placement observability >=90%;
- entered positions >=30;
- entered positions span >=8 distinct sessions;
- every entered position must have a valid close, otherwise data fail-closed;
- realized net mean >0;
- realized net median >0;
- realized net win rate >50%;
- all three chronological thirds realized-net mean >0;
- exact one-sided binomial p;
- Holm-Bonferroni FWER 0.05 across the four carried-forward assets.

PASS classification:
`MAKER_EXECUTION_FEASIBILITY_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

FAIL:
`MAKER_EXECUTION_FEASIBILITY_FAIL`

Source/data failure:
`MICROSTRUCTURE_DATA_BLOCKED`

No threshold rescue, candidate dropping, private endpoints, account reads, orders, wallets, exchange mutation or live trading.

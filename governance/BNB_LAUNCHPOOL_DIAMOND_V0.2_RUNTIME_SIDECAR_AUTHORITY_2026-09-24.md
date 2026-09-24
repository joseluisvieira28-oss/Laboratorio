# BNB-LAUNCHPOOL-DEMAND-001 — DIAMOND V0.2 RUNTIME SIDECAR AUTHORITY — 2026-09-24

**Status:** FROZEN BEFORE FIRST ELIGIBLE DIAMOND EVENT  
**Parent:** BNB-LAUNCHPOOL-DEMAND-001  
**Measurement contract:** BNB-LAUNCHPOOL-DIAMOND-V0.2-2026-09-24  
**Parent science changes:** NONE

## Freeze-state fact

At the last canonical runtime observation before this sidecar authority:
- eligible prospective Launchpool events visible = 0;
- prospective clusters = 0;
- prospective BNB paper selections = 0;
- prospective BNB resolutions = 0;
- missed prospective observations = 0.

Therefore the measurement implementation is being frozen before any Diamond-counted event outcome exists.

## Sidecar-only contract

The sidecar may observe only parent events that already have a canonical
`BNB_FORWARD_PAPER_SELECTION` receipt.

It may not:
- create an eligible parent event;
- alter event identity;
- alter <=60 minute clustering;
- alter overlap suppression;
- change LONG BNBBTC direction;
- change 15m parent entry;
- change 24h parent exit;
- change BASE20/STRESS30 costs;
- delete or suppress a parent winner/loser;
- authorize an order or capital.

A sidecar transport failure never changes parent evidence.

## Frozen causal measurement

Public read-only Binance Spot 1m klines only:
- BNBBTC;
- BNBUSDT;
- BTCUSDT.

Event alignment:
- first complete 1m bar whose open timestamp is strictly greater than the canonical parent signal timestamp.

Measure:
- 15m and 60m simple return for all three symbols;
- BNBUSDT 60m quote-asset volume;
- context-only BNBUSDT minus BTCUSDT 60m return;
- BNBUSDT 60m quote-volume shock ratio.

Volume baseline:
- median quote-asset volume of the most recent 20 prior UTC dates with a complete same-clock 60m window;
- scan at most 40 prior calendar dates;
- no historical Launchpool outcome calibration;
- fewer than 20 valid baseline dates = MECHANISM_DATA_BLOCKED and that event does not count toward the Diamond 25.

## Frozen first-25 causal gate

The first 25 complete causal measurements are immutable for V0.2.

Later measurements may be preserved but cannot replace, reorder or rescue the first 25.

At first 25:
- >=17/25 BNBBTC 60m returns positive;
- median BNBBTC 60m return > 0;
- >=17/25 volume-shock ratios > 1;
- median volume-shock ratio > 1.

Passing the causal gate is **not** by itself a Diamond verdict.
It routes to:
`CAUSAL_GATE_READY_FOR_PARENT_RECONCILIATION`.

Final Diamond V0.2 still requires the parent economic/integrity gates frozen in the measurement contract. No automatic promotion, Tier change, micro-live or capital authority is created.

## Failure semantics

- transient HTTP/source transport issue: fail closed for the sidecar iteration, do not alter parent evidence, retry naturally on a later runtime cycle;
- incomplete 60m event window: WAITING;
- frozen baseline insufficiency: MECHANISM_DATA_BLOCKED;
- malformed source bytes/schema: fail closed, no fabricated measurement;
- no outcome-driven threshold or baseline edits.

## Governance

- public/read-only market data only;
- no API key;
- no authenticated exchange endpoint;
- no orders;
- no wallets;
- no leverage;
- no exchange mutation;
- no capital;
- no main merge implied.

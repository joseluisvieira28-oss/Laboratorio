# LIQUIDATION-FLOW-FWD-001 — SOURCE GATE PASS CLOSEOUT V0.13.1

Date: 2026-10-03
Verdict: `SOURCE_GATE_PASS`
Status: SOURCE PROVEN / CALIBRATION MAY BEGIN / FAMILY NOT ACTIVE

## Authoritative completion run

- Workflow: `MEXC V0.13.1 Liquidation ETH Source Completion`
- Run: `37100077597`
- Job: `111137723756`
- Head: `3474fa4366c967a67c005b4cd0e0a6176e6a7c0e`
- Artifact: `v0131-liquidation-eth-source-completion`
- Artifact id: `11268610332`
- Artifact digest: `sha256:a144f33f12e31c9f948fdaf609078122119899368fb136cb3ed0f6cf8eb48098`

## Cumulative source proof

Prior BTC real-payload evidence remains anchored from run 37075262340:
- 3 valid BTCUSDT liquidation payloads;
- artifact digest `sha256:1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f`.

Current completion run:
- BTC topic acknowledgement: PASS;
- ETH topic acknowledgement: PASS;
- BTC connection errors: 0;
- ETH connection errors: 0;
- BTC heartbeat pongs: 370;
- ETH heartbeat pongs: 370;
- current BTC valid events: 0;
- current ETH valid events: 1.

The real ETH payload that closes the missing source leg:

- raw SHA256: `de6afb8f19578958d1aecb80849640c000f3b96065fe21263264173f8464b45a`
- symbol: ETHUSDT
- side: Sell
- event timestamp T: 1791012955250
- envelope timestamp: 1791012955372
- local receive timestamp: 1791012955459
- volume v: 3.17
- bankruptcy price p: 2690.40

The frozen semantics interpret Bybit side `Sell` as a SHORT position liquidation, i.e. forced buying pressure. The product v*p is only a bankruptcy-price notional proxy, not executed notional.

## Boundary

This ETH event is source-gate evidence only and MUST NOT enter calibration.

No source-gate BTC/ETH event can be reused as a calibration observation.

The calibration boundary is a NEW future boundary after this closeout commit.

## Family state

The source gate is passed, but the family is NOT active for Event Futures shadow outcomes.

Next state:

`SOURCE_PASS_PENDING_CALIBRATION`

Activation still requires the frozen calibration minimum for EACH symbol:

- 1440 healthy 60-second bins;
- at least 100 nonzero healthy bins;
- nearest-rank P95 of nonzero healthy-bin total notional proxy;
- numeric thresholds committed in a separate pre-outcome activation freeze.

No MEXC outcomes or trading occurred in this source gate.

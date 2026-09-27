# PREDICTION-SETTLEMENT-RV-001 — NEGATIVE MAP PRECHECK V0.1

Date: 2026-09-27
Status: PASS_FOR_SOURCE_DESIGN_ONLY / RESEARCH_ONLY

## Proposed identity

LAB_ID: PREDICTION-SETTLEMENT-RV-001
Primary family: RV — Relative Value / Convergence
Secondary: MARKET STRUCTURE / ACCESS
Math engine: executable binary-payoff package basis under distinct settlement functions.

## Mechanism

Compare public BTC binary contracts that share:
- the same resolution instant;
- the same displayed nominal strike;
- the same nominal underlying;
but differ in explicitly documented settlement construction.

Current candidate geometry:
- Polymarket: strict BTC/USDT Binance 1h candle Close > nominal strike.
- Kalshi KXBTCD: CF Benchmarks BRTI settlement with encoded cent boundary nominal strike - $0.01.

The one-cent boundary is part of the mechanism and may never be hidden under an EXACT_EXCEPT_ORACLE label.

## Negative Edge Map result

This proposal does NOT reopen:
- generic OHLC/indicator mining;
- generic BTC→ALT lead-lag;
- raw macro/event direction;
- failed access-shock directional-price labs;
- naive cash-and-carry;
- stablecoin peg mean reversion.

Closest prior work:
PREDICTION-ORACLE-BASIS-001 on branch prediction-oracle-basis-v0.1.

That parent required EXACT_EXCEPT_ORACLE and remains scientifically separate. Its 15m child was SOURCE_RULE_PROVENANCE_BLOCKED because Kalshi target-price initialization could not be proven. A later explicit-strike source probe found a near-equivalent population but with an explicit $0.01 tie-boundary difference. Under governance this requires a new scientific identity rather than a rescue or relabel of the parent.

## Why this is materially new

Information primitive:
contract settlement semantics themselves.

Economic object:
relative pricing of two binary payoffs with known, non-identical terminal state maps.

No price-direction forecast is required.

## Main falsifiers

- no recurring same-time/same-strike population;
- insufficient simultaneous executable depth;
- transaction fees/capital lock-up dominate gross package headroom;
- settlement-reference disagreement risk fully prices the apparent wedge;
- timestamp/stale-book effects create false discrepancies;
- source/rule changes break deterministic matching.

## Precheck verdict

NEGATIVE_MAP_PRECHECK_V0.1 = PASS_FOR_SOURCE_DESIGN_ONLY.

This is permission to test source feasibility, not evidence of edge.
No outcomes, PnL, live trading, orders, capital, exchange mutation or main merge are authorized.

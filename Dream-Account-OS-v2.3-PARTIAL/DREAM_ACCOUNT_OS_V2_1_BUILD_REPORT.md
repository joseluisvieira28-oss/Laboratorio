# DREAM ACCOUNT OS v2.1 — BUILD REPORT

**Observed:** 2026-09-07 17:38 UTC  
**Status:** PARTIAL — FAIL-CLOSED FOR LIVE SIGNALS

## Outcome

A read-only scanner core, scoring/risk/cost engines, SQLite journal, paper
fixture regression, dashboard generator, MEXC REST adapters, and fail-safe data
handling were implemented. No order execution, cancellation, withdrawal,
transfer, account mutation, or private-key capability exists.

The live Definition of Done did **not** pass because both public MEXC hosts were
unreachable from the build environment. Spot timed out and Futures returned
HTTP 502. The scanner correctly returned `FAIL_CLOSED`, emitted no candidate,
and persisted the failure as a system event.

## Data sources

- Intended primary: MEXC Spot public REST (`api.mexc.com`).
- Intended Futures: MEXC Contract public REST (`contract.mexc.com`).
- No private API keys.
- No external price source was substituted for signal generation.
- Offline fixtures are labelled `FIXTURE` and cannot become live signals.

## Architecture

`MEXC public REST → universe/fast filter → candle + book engines → regime → scoring + hard filters → risk/cost validation → SQLite journal → dashboard`

Implemented REST adapters:

- exchange information;
- 24-hour tickers;
- book ticker;
- order-book depth;
- klines;
- Futures ticker;
- Futures contract detail.

WebSocket streaming remains a next-phase item. REST recovery semantics and
fail-closed validation are present.

## Dry-run results

| Metric | Live dry-run | Offline regression |
|---|---:|---:|
| Pairs scanned | 0 | 1 fixture |
| Passing fast filter | 0 | 1 fixture |
| Passing deep filter | 0 | 0 |
| Market regime | unavailable | RISK_ON_TREND fixture |
| Active signals | 0 | 0 |
| Paper signals opened | 0 | 0 |

### Why the SOL fixture was rejected

The test fixture reproduced a confirmed 15-minute close above $107 followed by
a defended retest. Liquidity, spread, RVOL, regime and catalyst inputs passed,
but the cost-adjusted TP1 reward/risk was below 2R. The hard filter therefore
overrode the apparent technical setup and returned `NO_TRADE` with score 72.82
(Tier B). This is the intended behaviour.

### SOL status

**UNAVAILABLE / NO SIGNAL.** The live scanner could not validate whether the
historical $107 and $106.50–107 zones remain relevant. No inference was made
from stale data.

### BTC status

**UNAVAILABLE / NO SIGNAL.** The live scanner could not validate the historical
$80,500 trigger. No signal was emitted.

### Current market regime

**UNAVAILABLE.** Fail-closed due to unavailable primary market data.

### Current best move

**NO TRADE.** No live signal can exist without validated primary data.

## Validation

Automated checks cover:

1. candle-close breakout logic;
2. defended retest logic;
3. wick-only rejection;
4. unclosed-candle rejection;
5. spread calculation;
6. depth calculation;
7. slippage estimation;
8. CHF 56 position sizing and balance cap;
9. gross versus net RR;
10. RVOL;
11. SQLite persistence after restart;
12. API outage fail-closed;
13. rate-limit fail-closed;
14. malformed-data fail-closed;
15. hard-filter override.

## Definition of Done status

| Requirement | Status |
|---|---|
| Real MEXC ingestion | FAIL — network timeout/502 |
| Correct 15m candle closes | PASS in deterministic tests |
| Reproducible breakout + retest | PASS in deterministic tests |
| Spread/depth measurement | PASS in deterministic tests; live blocked |
| Funding/OI | PARTIAL — adapters only; live validation blocked |
| Scoring 0–100 | PASS |
| Hard filters | PASS |
| CHF 0.84–1.12 normal / CHF 1.68 max | PASS |
| Net RR includes configured costs | PASS; live fee discovery pending |
| Paper Shadow Mode | PARTIAL — schema and regression path; lifecycle pending |
| Journal survives restart | PASS |
| NO TRADE | PASS |
| Execution disabled | PASS |
| SOL/BTC regression | PARTIAL — SOL fixture; live levels blocked |
| Full MEXC market dry-run | FAIL — primary data unavailable |

## Security check

- No trading API key is read.
- No authentication/signature code exists.
- No order/cancel/withdraw/transfer method exists.
- A data-layer error produces zero candidates.
- Fixture data is explicitly separated from live mode.

## System limitations

- Public MEXC endpoints must be reachable from the eventual runtime.
- WebSocket ingestion is not implemented yet.
- Futures funding history, funding schedule and OI history need live endpoint
  verification and persistence.
- Fee discovery must be validated against the exact MEXC market/account mode;
  the fixture uses an explicit test fee and cannot justify a live trade.
- Paper-trade MFE/MAE/TP lifecycle is not complete.
- The dashboard is static HTML regenerated per scan, not a background service.
- No live Top 10/Top 3 can be produced while primary data is unavailable.

## Next development step

Run the scanner in a network environment that can reach both MEXC public hosts.
Capture and validate one complete exchange-info/ticker/klines/depth snapshot,
then finish Futures field mapping, WebSocket candle-close events, and the paper
trade lifecycle. Production or live trading must remain disabled until the full
Definition of Done passes.


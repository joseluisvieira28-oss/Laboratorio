# LICP-001 — CONTROL ROOM V0.1

Date: 2026-09-26
Branch: liquidation-cascade-propagation-v0.1
PR: #107

## Scientific state

| Gate | State |
|---|---|
| Core public liquidation source gate | PASS_SAMPLE |
| Binance BTCUSDT BBO source | PASS_SAMPLE |
| Bybit BTC/ETH/SOL allLiquidation subscription | PASS_SAMPLE |
| MEXC BTC_USDT target depth | PASS_SAMPLE |
| MEXC ETH_USDT target depth | PASS_SAMPLE |
| MEXC SOL_USDT target depth | PASS_SAMPLE |
| Hyperliquid BTC/ETH/SOL OI context | PASS_SAMPLE |
| Trigger-engine fail-closed tests | PASS |
| Mechanical calibration→config freezer tests | PASS |
| Executable LONG/SHORT fee/spread math tests | PASS |
| First 5m feature calibration | CALIBRATION_SPARSE |
| Second 10m feature calibration | RUNNING at last update |
| Numeric trigger config | UNFROZEN |
| MEXC post-trigger outcomes | NOT OPENED |
| MEXC 2025 public history | SOURCE_BLOCKED |
| LICP-HIST-XALT-003 Discovery | SURVIVOR — SOL SHORT / 60m selected |
| LICP-HIST-XALT-003 Holdout | HOLDOUT_SURVIVES_WITH_EXECUTION_DEVIATION — canonical run #36234052123; duplicate identical recomputation audited |
| LICP-FWD-XALT-004 transfer | LOCKED — waits for frozen numeric trigger config |
| Outcome-blind collector quiet-feed hardening | PASS — no false reconnects in post-fix smoke |
| Calibration shard aggregator | PASS tests — enforces 7d / 250 Bybit / 50 BTC / 95% uptime / clock/hash gates |
| First long calibration block | PASS — 20700s, Bybit 81 incl. BTC 22, Binance 211, MEXC depth 90057, zero disconnects/regressions |
| Current calibration block | COLLECTING — GitHub run 36261304688 |
| XALT-004 persistent state/restart layer | PASS — integrity run 36261561814 |
| OKX liquidation-orders robustness source | PASS_SAMPLE — public WS ack, 3 rows / 120s |
| BitMEX liquidation:XBTUSD robustness source | PASS_SAMPLE — public WS ack, quiet sample |
| Live trading | NOT AUTHORIZED |

## Frozen causal chain

1. Bybit BTC liquidation ignition:
   - 5s notional p95
   - 5s side-concentration p75

2. Binance BTC confirmation:
   - 5s notional p75
   - same normalized forced-pressure direction
   - observable within 5s of ignition

3. Open-interest context:
   - Hyperliquid public BTC OI
   - recorded causally
   - NOT a V0.1 trigger gate

4. ETH/SOL second wave:
   - Bybit 5s notional p95
   - same pressure direction
   - within 30s after confirmed BTC ignition

5. MEXC executable targets:
   - BTC_USDT
   - ETH_USDT
   - SOL_USDT

6. Horizons:
   - 1s / 2s / 5s / 15s / 30s / 60s

7. Economics:
   - taker/taker: executable BBO + 16 bps API fees
   - maker/maker: optimistic economic ceiling + 12 bps API fees

## Fail-closed state

Forward observer is wired to run only when
`LICP_001_TRIGGER_CONFIG_V0_1.json` changes to a valid `FROZEN` configuration.

Sparse or missing calibration values do not unlock it.


## Historical XALT validation update — 2026-09-26

LICP-HIST-XALT-003 frozen candidate:
- BTC liquidation ignition
- SOL short continuation
- entry proxy t0 + 6m
- horizon 60m

Single-pass holdout 2025-11..2025-12:
- n = 35
- mean gross = +25.0714 bps
- median gross = +16.8824 bps
- transfer-ceiling net after 16 bps hurdle = +9.0714 bps
- decision = HOLDOUT_SURVIVES

This is not MEXC executable validation.

Forward transfer gate LICP-FWD-XALT-004 is pre-frozen to:
- Bybit BTC ignition + Binance confirmation
- SELL pressure only
- 60s post-confirmation entry delay
- MEXC SOL_USDT taker SHORT
- 60m exit
- 16 bps round-trip fee hurdle
- >=20 independent episodes across >=3 UTC dates before verdict

The forward observer must fail closed while the numeric trigger config remains UNFROZEN.


## Holdout integrity caveat — 2026-09-26

The XALT-003 holdout was unintentionally recomputed once after the canonical first opening because a workflow-only commit retriggered the job.

- canonical run: 36234052123
- unintended duplicate: 36234349727
- scientific holdout script blob identical across both runs
- selected-candidate freeze blob identical across both runs
- numerical results identical
- no tuning or rescue occurred

The literal single-pass procedure was nevertheless violated.
Canonical scientific state:
**HOLDOUT_SURVIVES_WITH_EXECUTION_DEVIATION**.

A permanent repository lock now prevents any further XALT-003 holdout opening.

Forward MEXC validation remains mandatory before any promotion.


## Infrastructure hardening update — 2026-09-26 evening

### XALT-004 lifecycle
The forward SOL/60m observer was hardened before any forward outcomes:
- persistent episode state;
- deterministic episode IDs and duplicate protection;
- exact +60s entry and +60m exit logic;
- stale/crossed BBO rejection;
- restart gaps crossing an entry/exit deadline are marked missing, never backfilled;
- forward verdict remains locked behind >=20 matured episodes, >=3 UTC dates and <=10% missing/unresolved coverage;
- no orders, auth or exchange mutation.

Integrity workflow:
- run 36261561814 = PASS.

### Additional liquidation robustness sources
OKX:
- public endpoint accepted channel liquidation-orders / SWAP;
- 120s sample: 3 liquidation rows;
- decision: PASS_SAMPLE;
- role: robustness only, NOT primary trigger.

BitMEX:
- public endpoint accepted liquidation:XBTUSD;
- 120s sample quiet: 0 liquidation rows;
- decision: PASS_SAMPLE;
- role: robustness only, NOT primary trigger.

Primary frozen source-transfer design remains Bybit allLiquidation + Binance forceOrder.
No source substitution occurred.

### Branch orchestration limitation
GitHub workflow_dispatch cannot dispatch a workflow that does not exist on the default branch.
This was proven by dispatch smoke run 36261600279 (HTTP 404 for branch-only workflow).

Therefore:
- no fake claim of autonomous 7-day chaining;
- valid calibration blocks remain artifact-backed;
- the current long block continues independently;
- no merge to main was performed.

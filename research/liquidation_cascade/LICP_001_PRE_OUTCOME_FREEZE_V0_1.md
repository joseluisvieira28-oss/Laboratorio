# LICP-001 — LIQUIDATION CASCADE IGNITION & CROSS-VENUE PROPAGATION
## PRE-OUTCOME FREEZE V0.1

Date: 2026-09-26
Status: SOURCE / FORWARD FEASIBILITY ONLY
Branch: liquidation-cascade-propagation-v0.1

## Objective

Test whether the first observable burst of forced liquidations on major perpetual venues contains short-horizon information about a second-wave price displacement on the intended target venue large enough to survive real execution costs.

This lab is NOT an attempt to predict all crashes in advance.
It studies observable cascade ignition and propagation after forced-liquidation flow has begun.

## Why this is economically distinct

LICP-001 is not:
- static order-book imbalance;
- microprice displacement;
- liquidity depletion alone;
- ordinary aggressive-trade imbalance;
- cross-venue BBO dislocation alone;
- a rescue of prior scalping failures.

The causal state is forced deleveraging itself.

## Motivation

Public venue mechanics support direct observation:
- Bybit allLiquidation streams publish all liquidations for a symbol at 500 ms push frequency.
- Binance forceOrder streams publish force-liquidation snapshots at up to one update per symbol per 1,000 ms.
- MEXC public depth can provide the target-venue BBO and forward price path.

A recent 2026 study of a BTC perpetual liquidation cascade examined a roughly 9% decline using 7.16 million sub-fills and fifty-level order-book data, demonstrating that liquidation cascades operate on a price-move scale far larger than the 1–2 bps signals that failed the earlier scalping economic ceilings.

A separate 2026 study found that pre-cascade early-warning signatures were heterogeneous across major liquidation events. LICP-001 therefore does not assume a universal pre-crash fingerprint; it tests post-ignition propagation.

## Governance

- Research only.
- No authentication.
- No orders.
- No exchange mutation.
- No wallets or capital.
- No merge to main without explicit operator authorization.
- No threshold selection from outcome data.
- No live-trading authority.
- Fail closed on clock ambiguity, stale quotes, source disconnects, or malformed liquidation messages.

## Phase A — Source gate

Public forward streams:

### Bybit
Symbols:
- BTCUSDT
- ETHUSDT
- SOLUSDT

Topic:
- allLiquidation.<symbol>

Capture:
- system timestamp
- liquidation timestamp
- symbol
- liquidated-position side
- executed size
- bankruptcy price

### Binance USD-M
Streams:
- all-market forceOrder snapshot stream
- BTCUSDT bookTicker for source-clock/BBO reference

Capture for force liquidation:
- event time
- order trade time
- symbol
- side
- original quantity
- price
- average price
- last filled quantity
- accumulated filled quantity

Important limitation:
Binance forceOrder is a snapshot feed. For each symbol only the latest liquidation order inside a 1,000 ms interval is published. It MUST NOT be interpreted as complete liquidation volume.

### MEXC Futures
Symbol:
- BTC_USDT

Capture:
- incremental depth version
- timestamp
- best bid / best ask
- local monotonic receive time

## Source-gate PASS criteria

PASS_SAMPLE requires:
- Binance websocket subscription acknowledged;
- Bybit websocket subscription acknowledged;
- MEXC depth subscription acknowledged;
- Binance BTCUSDT BBO produces valid non-crossed quotes;
- MEXC BTC_USDT produces valid non-crossed quotes;
- local monotonic receive clocks do not regress;
- malformed liquidation payload count = 0.

Liquidation event count is NOT a PASS requirement because a quiet observation window may legitimately contain zero liquidations.

## Phase B — Baseline forward collection

Only after Phase A passes:
- collect forced-liquidation events and BBO state without trading;
- calibrate event-size and burst distributions from forward data only;
- do not create strategy thresholds from a single event.

## Candidate causal features for later freezing

Not yet authorized for outcome testing:
- liquidation notional per 250 ms / 500 ms / 1 s / 5 s;
- count of distinct liquidation events;
- side concentration;
- cross-venue agreement;
- BTC liquidation burst followed by ETH/SOL liquidation burst;
- liquidation burst + contemporaneous spread/depth deterioration;
- Bybit-first vs Binance-first event ordering.

## Candidate outcome horizons for later freeze

To be frozen only after source feasibility is proven:
- 250 ms
- 500 ms
- 1 s
- 2 s
- 5 s
- 15 s
- 30 s
- 60 s

No outcome is opened in the Source Gate.

## Terminal states

- SOURCE_FEASIBLE
- FORWARD_COLLECTING
- DISCOVERY_SURVIVES
- NO_EDGE
- BLOCKED

No state in this document authorizes live trading.

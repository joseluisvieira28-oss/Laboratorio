# LIQUIDATION EXHAUSTION V1 — source-first adversarial preregistration
Date: 2026-11-04 (Europe/Zurich)
Status: SOURCE_BLOCKED / ECONOMICS_NOT_TESTED / NO_LIVE_GO
Scope: independent new reversal hypothesis; no historical post-outcome optimization.

## Why this is not LICP-001 revival
LICP-001 (PR #107) forced-flow continuation BTC/60s, 16/32bps, had terminal NO_EDGE mean base -16.374554bps, as confirmed in PR #279. Preserve without modification or regrading. This research tests a *distinct* economic mechanism: exhaustion of price impact after a forced selling/buying burst, followed by observable contemporaneous passive absorption and book stabilization. Do not reinterpret LICP forward outcomes as training data or trade reversed signs on them.

## Evidence inspected before this protocol
- PR #279: 2026-04-01 Tardis/Bybit native raw full 1440-minute census, 1100 raw messages, 1318 BTC and 1013 ETH nested liquidation children; count parity only, NOT complete actual exchange event population.
- 1173 empty response minutes mean no raw messages available, NOT verified zero liquidations.
- Six explicit collector disconnect markers: 08:00, 08:01, 10:26, 15:10, 15:34, 20:22 UTC. Duration/recovery not established.
- 95.002s independent live Bybit feed carried trade/book, but cannot prove historical completeness. No contemporaneous full-day source custody, executable entry/exit quotes and causal lag quality certificate reviewed for this new experiment.
- PR #315 WebSocket 120s BTC feed: 834 real trades but zero observed liquidations; one initial MEXC index frame stale by 27.979s; not a liquidation-positive source proof.

## Hypothesis, distinct direction and operational feasibility
H_EXHAUST: following an *observed positive* burst of forced liquidations, absorption and stabilization observed **as of decision time** may precede a price rebound, e.g. SELL-liquidations => candidate LONG; BUY-liquidations => candidate SHORT. This is a conjecture, NOT a signal, edge or order instruction.

First gate is SOURCE ACCESSIBILITY, with no market return data opened before source rules and independent challenge are fixed.

## Source-admissibility hard gate (fail closed)
For EVERY prospective eligible episode, require:
1. Source-authenticated liquidation events with exchange event timestamp AND local receive timestamp, symbol, side, size, contract units, venue, and source archive hash. Positive witnessed liquidations required; do not infer events from open interest moves or impute zero on an empty interval.
2. Contemporaneous trade tape and L2 order book stream with sequence continuity and receive timestamps; independent BBO of intended execution venue, symbol matching, contract size and price units.
3. Proven publisher heartbeat/sequence or equivalent transport evidence before/during/after episode, and provenance for dropped frames, reconnects, stale or crossed books.
4. Explicit exclusion of every known disconnect and all affected intervals until an independently evidenced recovery / good sequence baseline. A six-minute list of disconnect markers alone cannot prove precise outage bounds.
5. Measurable clock offsets and end-to-end latency; no use of event-time data arriving after decision time. If order-book reconstruction or completeness cannot be certified, SOURCE_BLOCKED.
6. Append-only records plus SHA-256 source and code, no archive editing, no protected 2026 holdout opening. No look-ahead joins.

## Before first outcome: still required distinct frozen numerical protocol
Do NOT calculate a candidate mean/win rate/PnL until a separate pre-outcome commit defines, with independent scientific review:
- liquidation burst window, minimum size and denominators using only pre-trigger information;
- operational observable definition of *declining* forced-pressure, passive absorption and book stabilization, with **no** future candles;
- rule for direction, duplicate episode prevention, session restrictions, event order, and paired controls/ablations;
- one primary BTC symbol, one horizon, one entry/exit convention and fixed decision latency; ex ante sample size/power and multiple-testing policy;
- source eligibility & recovery windows and stress test plans;
- realistic manual delay scenarios 5/15/30s, taker/taker fees per verified accessible route, spread and slippage, notional limits, missed fills, drawdown and tail losses;
- time-forward discovery/validation split, *independent holdout* that remains sealed until frozen adjudication.

Cost note: PR #107 froze 16bps base and 32bps stress for a MEXC API route; there is a documented conflict with public metadata 2bps per side. Neither figure is automatically applicable to user's actual MANUAL execution route. Never retrofit cheaper costs after observing a result.

## Veredict machine
SOURCE_BLOCKED: inability to establish causal positive liquidation plus executable book/trade/quote continuity for sufficient observation; **not** NO_EDGE.
PROTOCOL_BLOCKED: sources usable, but objective primary rule/power not frozen before future outcomes.
INCONCLUSIVE: frozen study has too little independent eligible forward information for a defensible economical conclusion.
NO_EDGE: only if the *pre-frozen* adequate economic test fails at its specified costs/uncertainty thresholds.
SURVIVES_FORWARD_CANDIDATE: only if pre-frozen tests, independent causal source and net economics robust after execution delay/costs pass. Even then no LIVE GO absent separate risk & execution validation.

## Current adjudication (2026-11-04)
SOURCE_BLOCKED — for currently evidenced historical candidate dataset. The known six disconnect markers, non-certified zero-event intervals, missing causal paired book/quotes custody and as-of manual execution evidence prevent an admissible historical reversal verdict. There is **no observed net PnL for this hypothesis**. Do not label DEAD/NO_EDGE or SURVIVES.
Next legitimate action is a **small, explicitly capped, free, public, positive-event source-only forward acquisition** with continuity metadata and an independently verified recovery rule. No new scheduled or paid data collection authorized by this document; no duplicate LICP runs; only after source gate pass may an ex ante economic freeze be considered.

References:
- https://github.com/joseluisvieira28-oss/Laboratorio/pull/107
- https://github.com/joseluisvieira28-oss/Laboratorio/pull/279
- https://github.com/joseluisvieira28-oss/Laboratorio/pull/315
- research/liquidation_cascade/LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md (PR #107 branch)
- research/mexc_event_direction_v01/TRIPLE_FLOW_V02_SOURCE_RECOVERY_CLOSEOUT_2026-10-29.md (PR #279 branch)

Safety: RESEARCH ONLY. No orders, private exchange/API/account/wallet calls, fees, spend, deployments, persistent schedulers or merge to main.

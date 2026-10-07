# V0.13 CURRENT VERDICT — 2026-10-07

Branch: `mexc-event-futures-event-conditioned-v0.13-prereg-2026-10-03`

This closeout records only already-frozen, already-observed evidence. It does not change any rule, threshold, horizon, source gate or forward boundary.

## LIQUIDATION-FLOW-FWD-001

Initial 600-second source gate: `NO_EVENTS_OBSERVED`.
Authoritative extended one-hour source-only run: 37075262340 / job 111063614589.

Observed real valid liquidation events:
- BTCUSDT: 3
- ETHUSDT: 0

Extended source verdict: `PARTIAL_SOURCE`.

Interpretation:
- public transport/subscription worked;
- real BTC liquidation payloads were observed;
- ETH did not produce a qualifying real payload during the frozen one-hour window;
- the family therefore does NOT satisfy the frozen requirement that both BTC and ETH have at least one valid real event;
- no MEXC/Event Futures research outcome was opened;
- no calibration threshold is authorized yet;
- this is not NO_EDGE.

Current scientific state: `SOURCE_GATE_INCOMPLETE / PARTIAL_SOURCE`.

The existing calibration freeze remains authoritative. A legitimate activation still requires a real-message PASS for both symbols, then 1440 healthy non-overlapping 60-second bins per symbol plus at least 100 nonzero valid-event bins per symbol, then a separate numeric activation freeze before any outcome.

## OPTIONS-VOL-FWD-001

Public/free source gate: `SOURCE_GATE_PASS`.
Frozen rule: `OPTIONS_VOL_RULE_V013_V01.json`.
Activation freeze remains unchanged.

Initial forward smoke run: 37074644170 / job 111061698944.

Smoke result:
- preflight_pass: true
- resolved_n: 0
- outcomes_opened: 0
- BTC/ETH polls returned `NO_SIGNAL_OR_INVALID_SOURCE` during the bounded smoke
- no authenticated requests
- no Event Futures orders or live trading

Interpretation:
- runtime preflight passed;
- the bounded smoke did not produce an eligible >=5 percentage-point skew signal;
- zero outcomes means there is no basis for SURVIVES or NO_EDGE;
- the frozen 30-calendar-day batch rule still prohibits significance peeking before the batch boundary.

Current scientific state: `ACTIVE_RULE_FROZEN / AWAITING_FORWARD_EVIDENCE`.

## Verdict discipline

As of 2026-10-07:
- neither family is a confirmed edge;
- neither family is scientifically dead;
- LIQUIDATION-FLOW-FWD-001 is blocked before activation by incomplete source/calibration evidence;
- OPTIONS-VOL-FWD-001 is source-valid and rule-frozen but has insufficient forward evidence and must respect its frozen batch boundary.

No merge to main. No live trading. No orders. No private Event Futures endpoints. No account reads. No wallets. No spending. No post-outcome tuning.

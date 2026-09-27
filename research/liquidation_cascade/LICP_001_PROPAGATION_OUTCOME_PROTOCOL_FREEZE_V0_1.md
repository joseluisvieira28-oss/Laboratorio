# LICP-001 — PROPAGATION OUTCOME PROTOCOL FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Numeric trigger thresholds: NOT YET FROZEN

## Principle
The outcome clock starts only when a predeclared causal state becomes observable.
No event is timestamped retrospectively at an earlier, more favorable point.

## Event stages

### Stage 1 — BTC ignition
A Bybit BTCUSDT 5-second liquidation burst crosses the numeric ignition thresholds that will be frozen from outcome-blind calibration.

### Stage 2 — multi-venue confirmation
A Binance BTCUSDT forceOrder burst in the same normalized forced-pressure direction satisfies its frozen confirmation rule within 5 seconds of Stage 1.

Because Binance forceOrder is throttled, Binance is confirmation only and its notional is never summed with Bybit as if both feeds were complete.

### Stage 3 — OI context
Public Binance BTCUSDT open interest is observed causally.
V0.1 records OI destruction but DOES NOT require it for the trigger until an independent feature-only calibration supports a numeric rule.

No post-outcome OI threshold may be invented.

### Stage 4 — ETH/SOL second wave
Within 30 seconds after confirmed BTC ignition, a Bybit ETHUSDT or SOLUSDT 5-second liquidation burst crosses its independently frozen notional threshold in the same forced-pressure direction.

Two event families are preserved:
- BTC_CONFIRMED
- ALT_SECOND_WAVE (ETH or SOL)

They are never pooled silently.

## Episode de-duplication
After a confirmed BTC ignition, suppress new BTC episode starts for 120 seconds.
Events inside this interval belong to the same cascade episode.

This rule is frozen before outcomes.

## Target venue
MEXC Futures public BBO:
- BTC_USDT
- ETH_USDT
- SOL_USDT

A target observation is valid only when the target BBO is fresh and non-crossed at the causal event timestamp.

## Frozen horizons
From the causal observable event time:
- 1 s
- 2 s
- 5 s
- 15 s
- 30 s
- 60 s

Use the first valid target BBO observed at or after each horizon.
No interpolation.

## Direction
Normalized forced pressure defines continuation direction:
- SELL pressure => test SHORT continuation
- BUY pressure => test LONG continuation

This is a continuation hypothesis. Reversal is a separate future hypothesis and must not be rescued from failed continuation outcomes.

## Executable taker return

SELL pressure / SHORT:
- entry = current target best bid
- exit = future target best ask
- gross_bps = (entry - exit) / entry × 10,000

BUY pressure / LONG:
- entry = current target best ask
- exit = future target best bid
- gross_bps = (exit - entry) / entry × 10,000

MEXC API taker/taker fee hurdle frozen from the current official schedule:
- 8 bps per side
- 16 bps round trip

net_taker_bps = executable_gross_bps - 16 bps

Slippage sensitivity must be reported separately and can only worsen this result.

## Optimistic maker/maker ceiling
For economic triage only:
SELL / SHORT:
- entry assumed at current ask
- exit assumed at future bid

BUY / LONG:
- entry assumed at current bid
- exit assumed at future ask

MEXC API maker/maker fee hurdle:
- 6 bps per side
- 12 bps round trip

This is deliberately optimistic and does NOT imply fillability.

## Initial evidence states
- SOURCE_FEASIBLE
- CALIBRATING
- TRIGGER_FROZEN
- FORWARD_COLLECTING
- FORWARD_INSUFFICIENT
- FORWARD_SIGNAL
- NO_EDGE
- BLOCKED

FORWARD_SIGNAL is not promotion and not live authority.

## Minimum evidence before any edge verdict
Do not issue NO_EDGE or positive edge verdict from fewer than:
- 20 independent cascade episodes, AND
- observations spanning at least 3 distinct UTC dates.

Before that, report descriptive results only.

## Protected actions
This protocol authorizes:
- public forward observation;
- research receipts;
- executable-return calculation after the trigger config is frozen.

It does NOT authorize:
- orders;
- exchange authentication;
- exchange mutation;
- live capital;
- merge to main.

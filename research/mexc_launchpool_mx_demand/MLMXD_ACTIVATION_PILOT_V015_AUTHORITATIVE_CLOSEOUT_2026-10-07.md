# MEXC-LAUNCHPOOL-MX-DEMAND-001 — ACTIVATION PILOT AUTHORITATIVE CLOSEOUT V0.1.5
Date: 2026-10-07
Status: CLOSED — PILOT_NO_SIGNAL
Role: EXPLORATORY SOURCE-BOUNDED PILOT — ZERO PROMOTION CREDIT

## Frozen hypothesis
For the exact 14 pre-frozen official MEXC Launchpool events with explicit MX staking and exact activation T0:

- market: MX/USDT relative to BTC/USDT;
- timeframe: exact 15-minute UTC candle opens;
- entry: first 15m open at or after frozen activation T0;
- exit: exact +24h open;
- primary response: ln(MX_exit/MX_entry) - ln(BTC_exit/BTC_entry);
- positive expected sign;
- no event filtering, no alternate T0, no horizon rescue, no sign inversion.

## Authoritative run
Workflow: MLMXD Activation Pilot V0.1.5 UTC8 History Files
Run: 37636852086
Head: 3bc5be3a6fb60a3424875110303fadf97a2096a1

Market data:
- official public MEXC history CSV files;
- MX_USDT symbol id: 7fb2a8ab8a5e4eb699ac34ee340489f8;
- BTC_USDT symbol id: 2fb942154ef44a4ab2ef98c8afb6a4a7;
- verified CSV schema: open_time,open,high,low,close,volume,amount,close_time;
- verified file bucket rule: date(UTC timestamp + 8 hours).

## Result
- analyzable N: 14 / 14
- positive relative-return observations: 7 / 14
- mean relative 24h log return: -0.0024508339603943716
- median relative 24h log return: -0.0004906813124367256
- positive fraction: 0.50
- one-sided exact sign-test p: 0.604736328125
- bootstrap 90% CI for mean: [-0.007553875411941132, 0.0026348590544360375]
- leave-one-out minimum mean: -0.0037869863105163023

Calendar diagnostics:
- 2025: N=12, mean=-0.0027780586283911745, median=-0.0004906813124367256
- 2026: N=2, mean=-0.00048748595241355445, median=-0.00048748595241355445

## Frozen gate adjudication
PILOT_SIGNAL_PRESENT required ALL:
- N >= 10: PASS
- median > 0: FAIL
- positive fraction > 0.50: FAIL
- one-sided sign p < 0.10: FAIL
- leave-one-out minimum mean > 0: FAIL

Authoritative classification:

PILOT_NO_SIGNAL

## Interpretation
The specific activation-time analogue
"MX-staking Launchpool activation -> long MX relative to BTC for 24h"
did not show a positive signal in the complete frozen 14-event pilot.

This is a negative result for that exact pilot rule.

It is NOT:
- a verdict on every possible MEXC Launchpool mechanism;
- a result for announcement-time trading;
- permission to invert the direction;
- permission to select the 1h/6h diagnostics;
- permission to change T0 or filter events.

## Preserved transport history
Earlier runs are not deleted:
- V0.1 / run 37624255115: only 2/14 analyzable due historical transport limitation.
- V0.1.1 / run 37624682179: still 2/14 under REST kline transport.
- V0.1.3 / run 37636354586: N=0 due incorrect daily-file date mapping.
- V0.1.4 proved official MEXC daily files use a UTC+8 filename bucket.
- V0.1.5 resolved 14/14 and supersedes earlier runs for pilot adjudication.

## Governance
- zero promotion credit;
- no live trading;
- no orders;
- no exchange mutation;
- no account access;
- no wallet;
- no spending;
- no main merge;
- no post-outcome rescue.

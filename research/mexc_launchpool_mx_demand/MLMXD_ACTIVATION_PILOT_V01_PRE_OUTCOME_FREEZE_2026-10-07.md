# MEXC-LAUNCHPOOL-MX-DEMAND-001 — ACTIVATION PILOT V0.1 PRE-OUTCOME FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY MARKET OUTCOME
Role: EXPLORATORY SOURCE-BOUNDED PILOT — ZERO PROMOTION CREDIT

## Purpose
Test whether the exact opening of an official MEXC Launchpool MX staking window is followed by positive MX performance relative to BTC.

This is a separate activation-time pilot. It does not alter or rescue the announcement-timestamp source gate.

## Frozen source-bounded sample
All currently identified official MEXC Launchpool events with explicit MX staking and exact activation time in the fixed source review are included.

1. APT — 2025-01-23T10:00:00Z
2. Story (IP) — 2025-02-12T10:00:00Z
3. TERM — 2025-03-25T11:00:00Z
4. Kinto (K) — 2025-03-28T10:00:00Z
5. MNT — 2025-03-31T14:00:00Z
6. EPT — 2025-04-21T12:00:00Z
7. SHM — 2025-05-02T11:00:00Z
8. ICEBERG — 2025-05-20T11:00:00Z
9. BOMB — 2025-06-13T10:00:00Z
10. EURR — 2025-07-24T11:00:00Z
11. USDR — 2025-07-28T11:00:00Z
12. EIN Round 2 — 2025-08-04T10:00:00Z
13. EMBLEM — 2026-04-15T13:00:00Z
14. NEX — 2026-05-20T13:00:00Z

Source authority:
- official MEXC Launchpool announcement/tag archive;
- individual official MEXC articles;
- public/read-only only.

No event may be added or removed after market outcomes are opened for this pilot.

## Frozen market construction
Public MEXC spot market data only:
- MX/USDT
- BTC/USDT

Timeframe:
15-minute UTC candles.

Entry:
first 15m candle open whose timestamp is >= Launchpool activation T0.

Exit:
15m candle open exactly 24 hours after entry.

Primary response:
relative log return:
R_rel_24h = ln(MX_exit/MX_entry) - ln(BTC_exit/BTC_entry)

Positive means MX outperformed BTC.

Diagnostics frozen before outcomes:
- MX raw 24h return;
- BTC raw 24h return;
- relative 1h return;
- relative 6h return.
Only 24h is primary.

## Pilot integrity
An event is analyzable only if both MXUSDT and BTCUSDT contain exact required candles.
No interpolation or nearest-neighbor substitution.

## Frozen pilot classification
Report:
- N analyzable
- median and mean R_rel_24h
- positive fraction
- exact one-sided sign-test p for positive direction
- 10,000-row bootstrap 90% CI for the mean, seed 20261007
- leave-one-out minimum mean
- 2025 mean/median
- 2026 mean/median (diagnostic only because small N)

PILOT_SIGNAL_PRESENT requires ALL:
- N >= 10
- median R_rel_24h > 0
- positive fraction > 0.50
- exact one-sided sign p < 0.10
- leave-one-out minimum mean > 0

Otherwise: PILOT_NO_SIGNAL.

This classification grants ZERO Tier/production/live credit.

## No-rescue
No alternative T0.
No event deletion.
No horizon change.
No sign inversion.
No asset substitution.
No post-outcome filter.
No use of Launchpool reward size to select events.

## Governance
Research only.
No authenticated API.
No orders.
No exchange mutation.
No wallet.
No account access.
No spending.
No main merge.

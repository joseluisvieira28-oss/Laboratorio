# ETF-CME-INSTFLOW-001 — EXACT RUNTIME SCHEDULER V0.2

Date: 2026-09-23
Status: FROZEN PROSPECTIVELY BEFORE RUNTIME CHANGE

## Scientific authority preserved

Frozen mechanism remains:
- CFTC Legacy Futures Only
- contract code 133741
- signal = delta(noncommercial_long - noncommercial_short) / current open interest
- information-safe time = CFTC as-of date + 8 calendar days at 00:00 UTC
- entry target = first BTCUSDT daily 00:00 UTC price at/after information-safe time
- exit = entry + 7 calendar days at 00:00 UTC
- base/stress costs unchanged
- no threshold/regime/category/horizon change

The operational ExactTimingPolicy remains unchanged:
- arm lead = 60 seconds
- maximum technical lateness = 2 seconds
- late chase = forbidden

## Observed operational defect

The canonical runtime is healthy and continuously awake, but the general Radar cycle runs every 30 seconds and the ETF-CME source watcher is otherwise refreshed on a coarse cadence.

On 2026-09-23, the frozen information-safe target was 00:00:00Z. The signal was not persisted inside the +2 second technical budget and was correctly recorded as:
MISSED_EXPECTED_OBSERVATION_NO_CHASE.

That miss is immutable and MUST NOT be reconstructed.

## Authorized prospective remediation

Add a dedicated in-process exact-time scheduler which:
1. reads only the same frozen public CFTC source;
2. discovers the next frozen information-safe timestamp;
3. refreshes periodically while far from target;
4. pre-arms inside the existing 60-second arm window and records a source-only prearm receipt;
5. sleeps independently of the 30-second general Radar loop;
6. invokes the existing ETFCMEPublicSignalWatcher using actual UTC wall-clock time at the frozen target;
7. accepts success only if the unchanged ExactTimingPolicy classifies the actual invocation as DUE;
8. preserves append-once/idempotency semantics;
9. never reconstructs a missed target after the +2 second budget.

## Prospective boundary

The 2026-09-23 missed observation remains missed.

No exact scheduler event may create ETF_CME_FORWARD_SIGNAL_OBSERVATION for a CFTC as-of date <= 2026-09-15.

The first possible scheduler-created signal must belong to a strictly later CFTC as-of date.

## Firewalls

scientific_target_changed=false
information_lag_changed=false
hold_days_changed=false
late_budget_changed=false
costs_changed=false
missed_2026_09_23_recovered=false
historical_backfill=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
automatic_promotion=false
main_merge=false

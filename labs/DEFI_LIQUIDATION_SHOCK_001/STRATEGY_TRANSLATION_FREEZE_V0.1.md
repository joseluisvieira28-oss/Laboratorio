# DEFI-LIQUIDATION-SHOCK-001 — STRATEGY TRANSLATION FREEZE V0.1

Date: 2026-09-29
Status: FROZEN / BEFORE 2025 PROTECTED OUTCOMES

## Authority chain
- OOS_ADJUDICATION_LOCK_V0.1.json = SURVIVES_OOS
- DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json = DIRECTION_SOURCE_ROLE_AUDIT_PASS
- source role = LIQUIDATED_COLLATERAL_SOL
- direct market sale is NOT proven.

## Prospective hypothesis
H_SHORT_COLLATERAL_LIQUIDATION_V0.1

A qualifying 60-second SOL-collateral liquidation cascade is hypothesized to create a short-horizon bearish executable opportunity.

This is a hypothesis, not a conclusion.

## Signal
Exactly the existing 60-second primary cluster construction.
Target market identity:
mint:So11111111111111111111111111111111111111112

Allowed protocols/classes are exactly those in DIRECTION_SOURCE_AUDIT_LOCK_V0.1.json.
No new protocol, asset, proxy, cluster threshold, or event filter may be added after 2025 outcomes open.

## Direction
SHORT only.

No long/short switch based on future price behavior.
No model chooses direction.

## Timing
Signal availability time T0 is the already-defined cluster T0 = final liquidation event + 60 seconds quiet period.

Execution entry timestamp E:
- first exact UTC minute boundary strictly AFTER T0.
- if T0 is already exactly minute-aligned, E = T0 + 1 minute.

This deliberately reserves at least one minute-boundary of reaction latency.

Exit X:
E + 5 minutes, using the 1m OPEN at X.

No stop-loss, take-profit, trailing exit, adaptive exit, or alternate horizon in V0.1.

## Market field
Primary research price authority remains SOLUSDT 1m OPEN.
For the protected economic test, only the entry OPEN and +5m OPEN may be used for the primary gate.

## Return
Gross short simple return:
R_gross = (P_entry - P_exit) / P_entry

Net return at cost hurdle c:
R_net(c) = R_gross - c

No leverage is applied in scientific classification.

## Concurrency
Operational serialization is frozen:
- sort signals by E, then cluster_id;
- accept the first eligible signal;
- while a position is open, suppress any signal with E < current exit X;
- a signal at exactly X is eligible.

No pyramiding and no overlapping positions.

## 2025 protected economic holdout gate
2025 may be opened only after:
1. this freeze exists;
2. EXECUTION_COST_FREEZE_V0.1.md exists;
3. PROTECTED_2025_SOURCE_AUTHORITY_PASS exists.

Required for SURVIVES_2025_ECONOMIC_HOLDOUT:
- eligible serialized trade N >= 500;
- source/market pair coverage >= 95%;
- mean R_net(primary cost hurdle) > 0;
- day-block bootstrap 95% CI lower bound for mean R_net(primary cost hurdle) > 0;
- at least 2 inferential protocol families have positive mean R_net(primary cost hurdle).

Bootstrap:
- UTC event-T0 calendar day blocks;
- 5,000 repetitions;
- deterministic seed = full unsigned SHA256 integer of
  DEFI-LIQUIDATION-SHOCK-001 + "2025-economic-holdout" + "5m" + "V0.1";
- percentile CI with the same linear interpolation already frozen for the canonical experiment.

PASS => SURVIVES_2025_ECONOMIC_HOLDOUT
valid data but any gate fails => NO_EDGE_2025_ECONOMIC_HOLDOUT
source/integrity/coverage failure => SOURCE_BLOCKED_2025_ECONOMIC_HOLDOUT

## 2026 final holdout
2026 remains closed unless 2025 = SURVIVES_2025_ECONOMIC_HOLDOUT.

The final holdout window is prospectively fixed now, before 2025 outcomes are opened:
2026-01-01T00:00:00Z <= event timestamp < 2026-09-28T00:00:00Z.

The cutoff is the last fully closed UTC day before this freeze was made. Data at/after 2026-09-28T00:00:00Z is reserved for later forward/live-shadow observation and may not be pulled into the final holdout.

If opened, the 2026 final holdout uses this exact same strategy, 26 bps primary cost hurdle, 40 bps supportive stress, source mapping, timing, serialization, bootstrap and classification with no parameter change. It requires serialized trade N >= 500 and the same PASS gates as 2025.

## Firewall
protected_2025_outcomes_opened=false
protected_2026_outcomes_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false

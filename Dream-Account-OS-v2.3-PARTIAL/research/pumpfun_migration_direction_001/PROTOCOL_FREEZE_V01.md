# PMD-001 — PUMPFUN MIGRATION DIRECTION LAB — PROTOCOL FREEZE V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-v0.1`
Date: 2026-09-16

## 1. Question
Can information observable strictly before a Pump.fun bonding-curve graduation predict the economically tradable direction of the token after migration to its canonical PumpSwap pool?

This lab does not ask whether a launch will graduate. It conditions on graduation and asks whether pre-migration microstructure predicts the first post-migration move.

## 2. Independence from MSEL-001
MSEL-001 made its decision at T+5 minutes after token creation and explicitly prohibited future migration status as a feature. PMD-001 makes its decision at the migration boundary after the token has completed the curve. A materially different mechanism, population, decision time and outcome are therefore used. MSEL-001 failed outcomes may not be used to tune PMD-001.

## 3. Economic mechanism frozen before outcomes
The mechanism is demand absorption versus latent sell supply.

A graduating token can continue upward only if fresh, broad external demand around the end of the bonding curve is sufficient to absorb inventory held by earlier buyers who can realize gains after migration. High gross turnover without independent fresh demand is not treated as equivalent to broad demand.

Expected relation before outcomes:
- stronger fresh external demand, broader buyer participation and accelerating final-curve activity -> more positive post-migration return;
- greater concentration, more one-sided early inventory and decelerating final-curve demand -> weaker or negative post-migration return.

This directional thesis may not be reversed after results.

## 4. Candidate source regime
Primary candidate corpus: `Slinky21/Pumpfun_Memecoin_Corpus`, continuously collected 2026-06-05 through 2026-07-14, before the 2026-07-21 BOOST rollout.

The corpus is a source candidate only. Its published `KNOWN_ISSUES.md` is binding for the source gate. In particular:
- concentration rows flagged `top10_pct_suspect` are excluded from concentration-dependent work;
- corrupted / missing SOL trade amounts may not be silently used;
- stale `wallet_stats` activity aggregates are forbidden;
- synthetic migration pool sentinels are not authoritative pool addresses;
- 2026-07-03 is an outage day and is excluded;
- the post-2026-07-04 curve-depletion regime shift must be preserved as a regime flag, never hidden by random splitting;
- Mayhem launches are excluded from the primary population.

No `postgard_outcomes.parquet` labels may be opened in the source-gate stage.

## 5. Population
Primary eligible observation = one Pump.fun token with all of the following:
1. a graduation/migration record with a real canonical PumpSwap pool address, not a synthetic sentinel;
2. authoritative migration timestamp `T0`;
3. non-Mayhem token;
4. pre-migration data available up to the frozen decision cutoff;
5. post-migration price snapshots sufficient for the frozen entry and primary exit rule;
6. migration not on 2026-07-03;
7. no manual token selection, popularity filter, ticker filter or outcome-based exclusion.

Duplicate migration rows for the same mint fail closed until deterministically reconciled.

## 6. Decision time and leakage wall
`T0` = authoritative migration timestamp for the canonical pool.

Feature cutoff = strictly `< T0`.

No transaction, holder state, social state, price, pool state or wallet behavior timestamped at or after T0 may enter predictive features.

Migration existence is a population condition, not a feature.

## 7. Frozen executable outcome
Primary economic horizon: 5 minutes.

Entry price rule:
- first valid canonical-pool price snapshot at or after `T0 + 15 seconds`;
- if no valid price is observed by `T0 + 60 seconds`, the observation is execution-unavailable and excluded under a source/execution rule, never based on return.

Exit price rule:
- first valid canonical-pool price snapshot at or after `entry_timestamp + 300 seconds`;
- it must occur no later than `entry_timestamp + 330 seconds`; otherwise the observation is execution-unavailable.

Primary gross return: `exit_price / entry_price - 1`.
Primary net return: gross return less a frozen 3.00 percentage-point round-trip execution stress.

The 3.00% stress is intentionally conservative relative to the approximately 1.25% per-side low-market-cap canonical-pool platform fee regime and leaves additional room for execution friction. It may not be reduced to rescue results.

Secondary diagnostics, with no authority to replace the primary horizon: 60 seconds and 15 minutes, using the same +15s entry convention and analogous bounded snapshot rules.

## 8. Target
Primary target = whether `net_return_5m > 0` after the frozen 3.00% round-trip stress.

Raw UP/DOWN sign is descriptive only. Promotion requires economic, after-cost evidence.

## 9. Feature families allowed
Exact formulas must be frozen in `FEATURE_FORMULA_FREEZE_V01.md` after the schema/source gate and before any outcome return is computed.

Only these families are allowed:
- final-curve buy/sell pressure over frozen backward windows;
- fresh-buyer arrival / buyer breadth;
- final-curve velocity and acceleration;
- holder / buyer concentration where source integrity permits;
- creator/early-buyer retained inventory where reconstructible strictly before T0;
- point-in-time creator-linked / protocol / known-agent exclusions;
- elapsed time from launch to migration;
- explicit source/regime flags used for stratification, never as post-outcome rescue filters.

Forbidden in the first MVE:
- RSI/MACD/Bollinger or indicator fishing;
- social sentiment added after seeing outcomes;
- complex ML;
- post-T0 wallet profitability;
- post-T0 pool/liquidity variables as features;
- token name/manual narrative selection;
- any feature chosen because it correlates with opened outcomes.

## 10. Split frozen before outcomes
After source exclusions and before outcome calculation, order eligible mints by `(T0, mint)` and freeze contiguous chronological blocks:
- first 60%: Discovery;
- next 20%: Validation;
- final 20%: Protected Holdout.

The split is by count, not random sampling. Calendar date and known collection-regime flags remain recorded so regime dependence can be diagnosed. No mint may cross partitions.

## 11. Minimum sample gate
Before opening outcomes:
- total eligible population >= 1,000;
- Validation >= 200;
- Holdout >= 200;
- at least 20 distinct migration dates across the retained corpus.

Failure => `INSUFFICIENT_SAMPLE`; no threshold relaxation.

## 12. MVE order
1. Source/data gate only; no returns.
2. Freeze exact feature formulas and hashes.
3. Freeze chronological partition manifest without returns.
4. Open Discovery outcomes only.
5. If Discovery gates survive, open Validation.
6. If Validation survives without modification, open Protected Holdout.

No later stage may be opened to rescue an earlier failure.

## 13. Primary promotion gates
Exact score construction will be frozen pre-outcome, but the following economic gates are fixed now:
- after-cost median 5m return of the promoted slice must be > 0 in Validation and Holdout;
- after-cost positive-rate must be >= 55% in Validation and Holdout;
- promoted slice must exceed contemporaneous eligible baseline positive-rate by >= 5 percentage points in Validation and Holdout;
- top-versus-bottom score separation must have the same sign in Discovery, Validation and Holdout;
- no single migration date may contribute > 25% of total promoted-slice positive PnL in Validation or Holdout;
- the result must remain positive under the frozen 3.00% stress; no lower-cost rescue.

Statistical intervals and exact slice definitions must be frozen with the feature score before Discovery outcomes are opened.

## 14. BOOST quarantine
The 2026-07-21 BOOST mechanism changes post-migration microstructure by adding programmed buys during the first five minutes. PMD-001 V0.1 is strictly PRE-BOOST.

Post-BOOST data is a separate future regime and cannot be mixed into V0.1. If V0.1 survives all gates, a separately frozen translation/replication experiment is required before any shadow or micro-live consideration.

## 15. Governance
- research-only;
- fail-closed;
- no exchange mutation;
- no live orders;
- no alerts/webhooks that can place orders;
- no merge to main;
- no post-outcome tuning;
- no cherry-picking;
- no threshold rescue;
- no protected-holdout opening before prior gates pass.

A failed hypothesis is closed, not repaired.
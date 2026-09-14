# OPTIONS-SPOTPERP-002 — TIER 1 ADJUDICATION AUTHORITY V0.1

Status: PROSPECTIVELY FROZEN BEFORE 2025 OOS OUTCOME
Date: 2026-09-14
Repository: joseluisvieira28-oss/Laboratorio
Branch: options-spotperp-regime-v0.2
Candidate: UP_LOW only
Parent V2 status: TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE

## Governing policy

CRYPTO NEAR-DIAMONDS RECOVERY PROGRAM — V2
Policy ID: ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14

This authority translates the already-frozen Tier 1 bullets into an OPTIONS-SPOTPERP-002 adjudication map before the 2025 OOS result is available. It does not change the signal, costs, sample rules, OOS gates, source rules, regime threshold, horizon, asset, or candidate.

## Frozen scientific inputs

- Candidate regime: UP_LOW only.
- Signal: unchanged OPTIONS-SPOTPERP trade-implied call-minus-put IV skew implementation.
- Regime definition: 30-day BTC trend UP and 30-day realized volatility LOW under the frozen 80% annualized threshold.
- OOS window: authorized 2025 one-shot only.
- Base cost: 10 bps.
- Stress cost: 20 bps, diagnostic only.
- Minimum entered trades: 80.
- OOS gates remain exactly those frozen in OPTIONS_SPOTPERP_002_CONFIRMATION_AUTHORITY_V01.md.
- 2026 remains locked.

## Tier 1 required-evidence mapping

Tier 1 may be awarded only if ALL of the following are supported by the immutable 2025 OOS closeout and source receipts:

1. Clean provenance and reproducibility
   - confirmation source status = SOURCE_AUDIT_PASS;
   - timestamp compatibility correction is documented as technical-only and does not alter scientific rules;
   - raw/source hashes and immutable OOS artifacts are available.

2. No leakage / hindsight
   - this adjudication authority exists before the OOS scientific result;
   - UP_LOW is the only candidate;
   - no post-outcome threshold, horizon, cost, subgroup, quarter, asset or sign selection;
   - year_2026_accessed = false.

3. Adequate OOS sample
   - entered trades >= 80.

4. Positive frozen base-cost economics
   - 10 bps net mean per entered trade > 0;
   - 10 bps profit factor > 1.0.

5. Independent/OOS replication
   - frozen 2025 one-shot classification = OOS_REPLICATED;
   - no rerun may replace a scientifically valid negative OOS outcome.
   - retries are permitted only for documented TECHNICAL_FAILURE / DATA_FAILURE before scientific classification, with scientific rules unchanged.

6. No concentration pathology
   - frozen OOS concentration gate passes: no single quarter >75% of positive gross PnL;
   - at least two qualifying quarters (n>=15) have nonnegative 10 bps net mean.

7. Acceptable execution realism and risk profile
   - base cost remains the frozen realistic 10 bps assumption;
   - no V2 fatal risk combination: max drawdown >50% AND cumulative net return <5%;
   - 20 bps stress is reported as a fragility diagnostic and is not retroactively converted into a new hard gate;
   - any material execution caveat must remain visible in the final classification.

8. Statistical uncertainty reported
   - beta and HAC uncertainty from the frozen OOS runner are reported;
   - p<=0.05 is strong evidence but is not the sole gate when independent OOS replication exists, exactly as Policy V2 states.

9. No protected holdout contamination
   - 2026 remains unopened and unused.

## Frozen adjudication outcomes

- TIER1_VALIDATED_EDGE: all nine required-evidence items above are supported and the 2025 OOS classification is OOS_REPLICATED.
- TIER2_RETAINED: OOS does not scientifically invalidate the candidate but one or more Tier 1 required-evidence items remain unsupported or unresolved.
- TIER4_REJECTED: adequate-sample independent OOS materially destroys the frozen base-cost effect under Promotion Policy V2; historical Tier 2 status remains part of the audit trail but is superseded for this tested implementation.
- INSUFFICIENT_SAMPLE / DATA_FAILURE / TECHNICAL_FAILURE / BLOCKED / PROVENANCE_FAILURE remain non-scientific states outside the Tier ladder and must never be converted to Tier 4.

## Governance

Research-only. Tier 1 never authorizes live trading by itself.
No live trading.
No exchange mutation.
No orders.
No merge to main.
No deployment.
No post-outcome tuning.
No cherry-picking.
No parameter rescue.
No 2026 access.

This authority is frozen prospectively and must not be rewritten after the 2025 OOS outcome is observed.
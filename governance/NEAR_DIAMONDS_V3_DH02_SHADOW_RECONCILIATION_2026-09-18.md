# CRYPTO LAB — V3 DH-02 SHADOW EVIDENCE RECONCILIATION

**Date:** 2026-09-18  
**Governing policy:** `ND-PROMOTION-POLICY-V3.0-FROZEN`  
**Mode:** additive evidence reconciliation; no historical verdict rewrite  
**Repository branch:** `promotion-policy-v3-aggressive-2026-09-17`

## Reason for this amendment

The 2026-09-17 global V3 re-adjudication described `HTF-DONCHIAN / DH-02-HO1 6H` as Tier 2 retained and stated that the protected 2026 shadow remained locked / preflight-ready.

That operational statement was stale.

Before the V3 re-adjudication was written, the exact 6H candidate had already consumed a prospectively frozen protected Jan–Aug 2026 shadow block on branch `htf-donchian-shadow-v0.1` and had been formally closed as `SHADOW_READINESS_FAIL`.

Authority:
- shadow closeout commit: `11b19990579adc4175dcb85bd52767d991492ec4`
- closeout file: `Dream-Account-OS-v2.3-PARTIAL/research/htf_diamond_hunt/HTF_DONCHIAN_SHADOW_001_2026_CLOSEOUT_V0.1.json`
- source run: `35082752107`
- source artifact: `10441136713`
- execution run: `35083173576`
- execution artifact: `10441131489`

## Protected shadow evidence

Source/execution integrity was clean:
- 48 price archives and 48 funding archives;
- zero checksum mismatches;
- zero detected source gaps;
- zero incomplete 15m bars;
- zero unresolved execution paths;
- zero signal-rule deviations.

Economic result:
- elapsed calendar days: 243;
- resolved trades: 27;
- BASE expectancy: **-0.5689228153 R/trade**;
- BASE profit factor: **0.3529532167**;
- BASE total net: **-15.360916 R**;
- BASE win rate: **11.11%**;
- STRESS expectancy: **-0.5791187872 R/trade**;
- STRESS profit factor: **0.3413879439**.

Frozen failed conditions:
- minimum resolved shadow trades below 30;
- BASE expectancy not positive;
- BASE PF not above 1;
- STRESS expectancy not positive.

The closeout explicitly set:
- `production_ready=false`;
- `eligible_for_separate_risk_review=false`;
- `live_trading_authorized=false`;
- no partial-September rescue;
- no 12H sibling rescue;
- no post-outcome tuning;
- no asset selection;
- no timeframe substitution;
- close the 6H production path under this implementation.

A later Crypto Edge Radar implementation receipt independently records that Donchian 6H is not connected after `SHADOW_READINESS_FAIL`.

## Reconciliation under Promotion Policy V3

Historical V1/V2/V3 labels are preserved. This amendment does **not** retroactively erase the positive Phase-5 holdout or the 2026-09-17 V3 Tier-2 evidence adjudication.

However, the current operational state must include the already-known protected shadow contradiction.

Therefore:

`CURRENT_OPERATIONAL_STATUS = TIER2_HISTORICAL_EVIDENCE__SHADOW_READINESS_FAIL__VALIDATION_LADDER_CLOSED`

Consequences:
1. DH-02 6H is **not micro-live eligible**.
2. DH-02 6H is **not production-ready** and is not an active fast-path candidate.
3. The 2026 protected shadow must not be reopened, extended into partial September, or reinterpreted to rescue the exact 6H path.
4. DH-03 12H remains supporting sibling evidence only and must not replace DH-02 after outcomes.
5. Any future modified/12H Donchian candidate requires a new prospective authority and genuinely independent evidence.
6. This amendment does not force a new Tier-4 label because the frozen shadow protocol resolved 27 trades versus its 30-trade minimum; a separate policy adjudication would be required to convert the operational closeout into a tier reclassification.
7. Regardless of tier nomenclature, the existing V3 execution ladder for DH-02 stops here: no shadow-to-micro-live advancement is permitted.

## Current actionable V3 Tier-2 research lanes

For aggressive research prioritization, the active lanes are now:
- `BNB-LAUNCHPOOL-DEMAND-001` — Tier 2 / Quase Diamante; forward source preflight operational; waiting for a genuinely prospective eligible event.
- `ETF-CME-INSTFLOW-001` — Tier 2 retained / fragile; forward shadow is the next active evidence source.

DH-02 6H remains preserved in the historical board but is removed from the **active execution shortlist**.

## Governance

No trading rule changed. No negative evidence deleted. No 2026 data newly opened by this amendment. No live trading, orders, wallets, exchange mutation, alerts/webhooks, or main merge are authorized.

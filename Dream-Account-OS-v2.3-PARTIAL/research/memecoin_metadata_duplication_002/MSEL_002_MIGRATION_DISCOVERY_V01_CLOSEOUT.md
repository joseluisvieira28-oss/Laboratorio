# MSEL-002 — MIGRATION DISCOVERY V0.1 CLOSEOUT

Date: 2026-09-20
Branch: `memecoin-metadata-duplication-v0.1`
Canonical run: `35520388553`
Artifact: `10608642323`
Artifact digest: `sha256:94c38774328a23a5d2bc5f7399c2fcf1eb649eed4355a5b77bd6890083b6c798`

## Final classification

**DISCOVERY_NO_EDGE_FOR_FROZEN_MIGRATION_MECHANISM**

This is a terminal closeout for the exact frozen mechanism:
`PRIOR_EXACT_IMMUTABLE_IDENTITY_REUSE_6H -> lower Pump→PumpSwap migration completion within 24h/72h`.

No rescue is authorized by changing cohort, exposure definition, identity rules, matching window, control count, horizons, statistic, threshold, bootstrap method, direction or source population.

## Source integrity

- provider: SQD Portal solana-mainnet finalized-stream
- coverage_complete: true
- start_slot: 364937756
- end_slot: 365632973
- transport_batches: 987
- blocks_returned: 20,606
- total migrate instructions observed: 1,608
- committed migrate instructions: 949
- cohort migration evidence rows: 13

Cohort:
- 51 exposed
- 510 controls
- 561 total
- 51 matched sets
- all 561 source-resolved

## Frozen outcomes

Total:
- MIGRATED_24H: 6
- MIGRATED_72H_ONLY: 0
- NO_MIGRATION_72H_SOURCE_COMPLETE: 555

By role:
- exposed: 0 / 51 migrated within 24h or 72h
- controls: 6 / 510 migrated within 24h; 0 additional by 72h

## Frozen statistic

- D24 = -0.011764705882352941
- D72 = -0.011764705882352941
- matched-set bootstrap 95% CI for D24 = [-0.02156862745098039, -0.00392156862745098]
- resamples = 100,000

Frozen verdict gates:
- D24 <= -0.10: **FAIL**
- bootstrap upper 95% < 0: PASS
- D72 < 0: PASS

The directional difference is negative and the frozen CI excludes zero, but the effect magnitude is only about **-1.18 percentage points**, far below the prospectively frozen minimum materiality gate of **-10 percentage points**.

Therefore the exact frozen mechanism is **NO_EDGE** under its own pre-outcome decision rule.

## Safety

No prices, returns, PnL, market-cap labels, live trading, orders, wallets or chain/exchange mutation were opened.

No Tier promotion is authorized.

The MSEL-002 source/prevalence finding remains historically valid as a source fact, but this exact economic migration-fragility hypothesis is closed and must not be rescued post-outcome.

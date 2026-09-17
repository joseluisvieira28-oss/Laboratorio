# PMD-001 — V0.12 Exploratory Replication-Candidate Gate

Status: **FROZEN BEFORE FULL CHAIN-EXACT FEATURE DATA — EXPLORATORY ONLY**

This gate does not restore holdout status and cannot promote an edge, diamond, or live strategy. Outcomes were already opened in V0.8. Its purpose is only to prevent weak multiple-testing artifacts from being carried forward.

## Fixed family

Evaluate only the features frozen in `CHAIN_EXACT_FEATURE_RECIPE_FREEZE_V012.md` and emitted by `extract_chain_exact_features_v012.py`. No feature subset search, threshold optimization, ML, or transformations added after the V0.12 feature table is observed.

## Multiple-testing control

For all fixed continuous V0.12 features with sufficient observations:

1. compute Spearman rho versus the frozen 5-minute net return;
2. compute the two-sided Spearman p-value;
3. apply Benjamini-Hochberg FDR correction jointly across the tested V0.12 feature family;
4. report both raw p and BH q values.

No feature may be called a replication candidate solely because of a small raw p-value.

## Minimum evidence for a V0.12 replication candidate

A feature can be labelled `V012_REPLICATION_CANDIDATE` only if all of the following hold:

- at least 500 decoder-complete observations for that feature;
- BH q-value <= 0.05;
- the Spearman direction is the same in early, middle, and late chronological thirds;
- the favorable-versus-unfavorable extreme-quintile median-return difference has the same direction in all three chronological thirds;
- the favorable extreme quintile has at least 100 observations;
- favorable-quintile median net return > 0;
- favorable-quintile trimmed mean net return > 0;
- favorable-quintile positive rate is greater than the eligible-sample baseline positive rate;
- after removing the single largest positive return from the favorable quintile, its mean net return remains > 0.

The favorable extreme is the high quintile when rho > 0 and the low quintile when rho < 0. This is diagnostic orientation only, not a tradable threshold.

## Outcomes

- `V012_REPLICATION_CANDIDATE`: deserves an independently frozen replication dataset / period.
- `V012_NO_ROBUST_FEATURE_SIGNAL`: no feature satisfies the complete gate.
- `V012_DECODER_OR_SAMPLE_INSUFFICIENT`: source passes but fewer than 500 decoder-complete observations are available for the tested feature family.

None of these labels has trading-production authority.

# DEFI-LIQUIDATION-SHOCK-001 — MARKET MAPPING REQUIREMENTS ARTIFACT SELECTION FREEZE V0.1

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Source artifact

Artifact name:
`dls-source-cluster-sample-gate-v01`

Selection:
- query non-expired GitHub Actions artifacts with that exact name;
- sort by created_at descending, then artifact id descending;
- select the newest artifact;
- extract it without inspecting any market outcome because this artifact is source-only;
- require included `SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json`
  classification == `SOURCE_SAMPLE_GATE_PASS`.

A newer artifact with a non-PASS receipt cannot be bypassed by choosing an older PASS artifact.

The same selected artifact must contain:
`SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson`

No other run/artifact may be substituted silently.

## Firewall

prices=false
returns=false
pnl=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
post_outcome_tuning=false
live_trading=false
merge_main=false

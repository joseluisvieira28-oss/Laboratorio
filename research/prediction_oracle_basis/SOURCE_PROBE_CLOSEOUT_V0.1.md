# POB-15M-CHAINLINK-CFRTI-001 — SOURCE PROBE CLOSEOUT V0.1

Date: 2026-09-27
Status: TARGET_INITIALIZATION_UNPROVEN
Scientific meaning: SOURCE/RULE PROVENANCE BLOCKER — NOT NO_EDGE
Parent lab: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Draft PR: #143

## Execution
GitHub Actions workflow: POB 15m Source Probe
Run ID: 36328704949
Job ID: 108646362348
Conclusion: SUCCESS
Artifact ID: 10934642285
Artifact name: POB_15M_SOURCE_PROBE_RECEIPT
Artifact ZIP SHA256: b9126e7180717b4c3b1d11962e52f62698b6adaffd424033dddcc99eaf4b5e54

## Outcome firewall
PASS.
- economic_outputs_computed = false
- future_nearest_joins = 0
- silent_imputations = 0
- no PnL / profitability / win-rate / optimal-threshold / best-direction output

## Source census
- Polymarket 15m source-shape candidates recovered: 13
- Kalshi open KXBTC15M markets recovered: 1
- Kalshi candidates with complete executable quote-schema fields: 1
- Kalshi candidates whose official captured rules prove target-reference initialization from BRTI/CF Benchmarks: 0
- EXACT_EXCEPT_ORACLE pairs: 0

## Adjudication
TARGET_INITIALIZATION_UNPROVEN.

The current source route proves that:
1. a live population exists on both venues;
2. Kalshi exposes machine-readable quote fields for the open KXBTC15M market;
3. the probe can acquire and hash source metadata without economic outcome access.

It does NOT prove the key causal identity required by this child:
that Kalshi's initial Target Price is generated from a reference object equivalent to Polymarket's start-side Chainlink BTC/USD TWAP/reference.

Therefore the exact oracle-only comparison is not authorized.

## Next legitimate source action
Seek first-party Kalshi contract terms / rule text / product documentation that explicitly defines how the KXBTC15M Target Price is initialized.

Permitted:
- official contract terms;
- official API market/series/event fields;
- official help/rules pages;
- public source snapshots.

Not sufficient:
- third-party dashboards;
- inference from displayed target values;
- matching one observed target to a contemporaneous price;
- reverse-engineering target formation from market outcomes.

If first-party provenance cannot establish target initialization:
close this child as SOURCE_RULE_PROVENANCE_BLOCKED.

No contract-definition widening is permitted.

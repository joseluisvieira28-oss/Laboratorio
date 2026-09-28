# DLS V0.2 — EXECUTABLE VOLATILITY DEVELOPMENT CLOSEOUT

Date: 2026-09-28
Branch: dls-v02-executable-volatility-v01
Classification: V02_DEVELOPMENT_NO_EXECUTABLE_EDGE

## Authority

V0.1 inherited terminal state:
SURVIVES_OOS

V0.2 source gate:
V02_EXECUTION_SOURCE_PASS
Run: 36487730407
37/37 frozen monthly archive+checksum metadata probes passed.

V0.2 development:
Run: 36488734701
Artifact: dls-v02-executable-volatility-development-v01
Artifact ID: 11001390109

## Result

Eligible configurations under the frozen primary 26 bps round-trip cost model:
0 / 60.

All 60 primary configurations failed:
- positive overall net mean gate: 0/60 passed;
- positive all-three-fold mean gate: 0/60 passed;
- profit factor > 1.05 gate: 0/60 passed.

All 60 satisfied the positive-PnL protocol concentration <=80% rule.
36/60 satisfied the ambiguous-first-bar <=10% rule.

## Pre-frozen lower-cost sensitivity

Even the lowest pre-frozen cost stress (20 bps round trip) had no positive candidate.

Best observed 20 bps configuration:
- k = 1.50
- W = 30m
- H = 60m
- trades = 2,890
- mean net return/trade = -0.001954017936793003
- profit factor = 0.6630776535292241
- fold means:
  - F1 2021-12..2022: -0.0006738013804906167
  - F2 2023: -0.0020844240801933347
  - F3 2024: -0.0022882118253200402
- ambiguous-first-bar rate = 0.6574%

Primary 26 bps version of the same configuration:
- mean net return/trade = -0.002554182254066302
- profit factor = 0.5858346077651405
- all three folds negative.

## Interpretation

The V0.1 direction-agnostic volatility expansion does not convert into a robust symmetric first-breakout strategy under the frozen V0.2 rule.

This is a terminal failure of this execution family, not a failure of V0.1.

No parameter rescue is authorized under V0.2.

## Holdout preservation

2025 protected OOS was NOT opened.
2026 final protected holdout was NOT opened.

## Firewall

live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_parameter_rescue=false

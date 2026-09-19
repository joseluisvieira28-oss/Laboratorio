# CROSSCHAIN-PRICE-ATTENTION-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-20
Canonical run: `35476877482`
Canonical head: `f63061ea3457ed9d5713465689928cf4422bd6d1`
Artifact: `CROSSCHAIN_PRICE_ATTENTION_001_V0_1`
Artifact digest: `sha256:3cd50b8ea29f73f8ce6585b83c6c96ac4ceaa5f8f5c5952f5cc73db966db046d`

## Source gate

**CPA_SOURCE_FULL**

For ETHUSDT, SOLUSDT, BNBUSDT and AVAXUSDT:
- 48 / 48 monthly 1h-kline archives;
- 48 / 48 monthly funding-rate archives;
- 12 / 12 months in each year 2022–2025.

No source substitution was required.

## Frozen Discovery

Period: 2022-01-01 through 2024-12-31.

Signal:
- positive 12h return at or above its own past-only rolling 95th percentile;
- if multiple chains trigger, select the largest standardized shock;
- enter one hour after the decision boundary;
- hold 12h;
- long shocked-chain native / short equal-weight basket of the other three;
- include funding settlements;
- 20 bps primary and 40 bps stress costs.

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Primary 20 bps:
- N = 272
- mean = -0.0804%
- median = -0.1809%
- hit rate = 48.16%
- PF = 0.9268
- bootstrap 95% CI = [-0.4163%, +0.2605%]
- positive years = 1 / 3
- max losing streak = 7

Year means:
- 2022 = +0.2759%
- 2023 = -0.0645%
- 2024 = -0.3214%

Stress 40 bps:
- mean = -0.2804%
- PF = 0.7674
- bootstrap 95% CI = [-0.6138%, +0.0695%]

Winner-event counts were balanced:
- AVAX = 66
- BNB = 69
- ETH = 67
- SOL = 70

Only the sample-size gate passed. All frozen economic promotion gates failed.

## Holdout discipline

Because Discovery failed, **2025 outcomes were not opened**.

This exact price-attention continuation translation is terminal. No percentile/horizon/direction/cost/symbol rescue is authorized.

No 2026 data, live trading, exchange mutation, wallet access or merge to main occurred.

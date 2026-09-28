# DEFI-LIQUIDATION-SHOCK-001 — V0.1 TERMINAL CLOSEOUT

Date: 2026-09-28
Branch: dls-field-enrichment-v01
Terminal classification: SURVIVES_OOS

## Executive result

DEFI-LIQUIDATION-SHOCK-001 passed the frozen Discovery and OOS gates under the outcome/statistical authority frozen before market-outcome access.

This classification means:
- Discovery passed under the frozen 2021-2023 split.
- OOS passed under the frozen 2024 split.
- The primary 60-second liquidation-cascade experiment survived OOS.
- This is NOT live-trading authority.
- This is NOT a signed-direction claim.
- 2025/2026 protected market outcomes remain CLOSED.
- No post-outcome tuning is authorized.
- No main merge is authorized by this closeout.

## Authority chain

- GLOBAL_FIELD_COVERAGE_FINAL_PASS
  - run: 36464851648
- SOURCE_SAMPLE_GATE_PASS
  - run: 36465385517
- MARKET_DATA_SOURCE_PASS
  - run: 36483390920
- FINAL_PRE_DISCOVERY_AUTHORITY_PASS
  - run: 36483501137

## Discovery

Run: 36485204623
Artifact: dls-discovery-v01
Artifact ID: 10998631696
Classification: SURVIVES_DISCOVERY

Mapped source clusters: 5,672
Paired clusters: 5,672
Pair coverage: 100.000%

Primary 5m:
- mean event |return|: 0.004178422980739870
- mean control |return|: 0.002366473337592779
- mean paired difference: 0.001811949643147091
- relative uplift: 76.56750719998562%
- 95% UTC-day block-bootstrap CI for mean paired difference:
  [0.0010973078085018632, 0.0026492348082339605]

Inferential protocol-family 5m mean paired differences:
- Kamino: +0.0017244960648843473
- marginfi: +0.0006740882343774944

Secondary horizons:
- 1m relative uplift: 82.68326828500752%
- 30m relative uplift: 65.42956859715288%
- 240m relative uplift: 63.13789661173170%
- all three one-sided secondary bootstrap p-values: 0.0001999600079984003
- all three survived frozen Holm-Bonferroni family-wise alpha 0.05

Discovery firewall:
- OOS 2024 opened: false
- protected 2025/2026 opened: false
- live trading: false
- orders: false
- exchange mutation: false
- post-outcome tuning: false

## OOS 2024

Run: 36485809687
Artifact: dls-oos-v01
Artifact ID: 10999821052
Classification: SURVIVES_OOS

Mapped source clusters: 9,931
Paired clusters: 9,929
Pair coverage: 99.97986104118417%
Exclusions:
- 2 clusters excluded by frozen split-boundary rule
- archive missing minutes: 0
- hard source errors: 0

Primary 5m:
- mean event |return|: 0.003256871085761012
- mean control |return|: 0.001798248703232434
- mean paired difference: 0.001458622382528578
- relative uplift: 81.11349558638008%
- 95% UTC-day block-bootstrap CI for mean paired difference:
  [0.0010259767254329436, 0.0019865411570330663]

Inferential protocol-family 5m mean paired differences:
- Kamino: +0.002588472486207109
- marginfi: +0.0011456306332162883
- Save11: +0.0011705561088862435

Secondary horizons:
- 1m relative uplift: 73.92989651340418%
- 30m relative uplift: 72.45287651739802%
- 240m relative uplift: 66.06056330030092%
- all secondary mean paired differences positive
- secondary bootstrap p-values reported as 0.0001999600079984003 each (supportive; Holm is not an OOS promotion gate in V0.1)

OOS firewall:
- OOS 2024 opened: true
- protected 2025/2026 opened: false
- live trading: false
- orders: false
- wallets: false
- exchange mutation: false
- post-outcome tuning: false
- merge main: false

## Frozen scientific interpretation

The V0.1 primary claim was direction-agnostic:
completed on-chain liquidation cascades are followed by a larger near-term absolute market move than prospectively matched non-event control windows for the same directly mapped market.

V0.1 does NOT establish:
- universal post-liquidation signed direction;
- realized liquidation-to-exchange sell flow;
- executable alpha after fees/slippage;
- live-trading profitability;
- authorization to trade.

## Terminal V0.1 status

SURVIVES_OOS

The next scientific step, if pursued, requires a new explicit pre-outcome authority. Protected 2025/2026 must not be opened under this V0.1 authority.

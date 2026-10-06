# BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001 — V0.2 AUTHORITATIVE DISCOVERY CLOSEOUT
Date: 2026-10-06
Status: NO_EDGE_DISCOVERY

## Authority
Pre-outcome freeze:
- V02_PRE_OUTCOME_DISCOVERY_FREEZE_2026-10-06.md
- V021_PRE_OUTCOME_CLUSTER_INDEPENDENCE_AMENDMENT_2026-10-06.md

Authoritative deterministic runs:
- 37414791311
- 37414798706

Both runs completed successfully and reproduced identical metrics.

## Sample
- frozen development universe: 33
- valid observations: 33
- source-invalid: 0
- distinct official article clusters: 24
- 2026 outcomes opened: false

## Primary metrics
- median event signed convergence: +62.0572 bps
- event convergence hit rate: 63.6364%
- median excess convergence vs matched control: +55.6947 bps
- leave-one-out minimum median convergence: +51.4747 bps
- observation positive concentration: 16.3945%
- article-cluster positive concentration: 16.3945%
- median event OI decay: 15.2983%
- median excess OI decay vs control: +13.8021 pp

## Frozen gates
PASS:
- n >= 12
- median event convergence > +15 bps
- median excess convergence > +10 bps
- leave-one-out median > 0
- observation concentration <=35%
- distinct article clusters >=10
- article-cluster concentration <=35%
- median excess OI decay >= +10pp

FAIL:
- event convergence hit rate >=65%: observed 63.6364%
- median event OI decay >=20%: observed 15.2983%

Because the primary gate is ALL-of, the authoritative verdict is:
NO_EDGE_DISCOVERY

## Year split — descriptive only
2024:
- n=11
- hit rate=72.7273%
- median convergence=+77.1501 bps
- median OI decay=8.4146%

2025:
- n=22
- hit rate=59.0909%
- median convergence=+38.9010 bps
- median OI decay=16.3905%

These splits do not rescue the failed primary gate.

## Interpretation
The forced-settlement population shows a real descriptive tendency toward mark/index convergence relative to the matched control and positive excess OI decay. However, under the prospectively frozen decision rule, the effect is not reliable enough across observations and OI does not decay strongly enough in the one-hour event window.

The mechanism is therefore scientifically interesting but NOT promoted as an edge.

No execution freeze, tradability test, holdout, or 2026 confirmation is authorized from V0.2.

## Governance
No live trading.
No orders.
No main merge.
No exchange mutation.
No post-outcome tuning or rescue.
2026 remains closed.

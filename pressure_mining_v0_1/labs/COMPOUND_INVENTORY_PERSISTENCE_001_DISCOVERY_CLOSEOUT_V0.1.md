# COMPOUND-INVENTORY-PERSISTENCE-001 — DISCOVERY TERMINAL CLOSEOUT V0.1

Date: 2026-09-27
Status: DISCOVERY_FAIL_NO_SUPPORT — EXACT 24H CHILD CLOSED
Historical window: 2023–2024
Protected 2025+: unopened

## Frozen hypothesis

Persistent known Compound III seized-collateral inventory remaining positive after the liquidation block would predict **underperformance of the collateral asset versus BTC over the next 24 hours**.

The signal, four assets, BTC benchmark, 24h horizon, sample gate, weekly-cluster bootstrap and pass gates were frozen before market prices were opened.

## Source authority before outcomes

Compound source census:
- AbsorbCollateral logs: 894
- BuyCollateral logs: 999
- unique absorbed borrowers lower bound: 505
- collateral assets: 7
- known historical anchor recovered

Lower-bound inventory ledger:
- 43 closed known-inventory episodes
- 31/43 persisted >20 blocks
- 27/43 persisted >100 blocks
- median duration: 28,171 blocks

Market source coverage:
- Binance Data Vision Spot monthly 1m
- BTCUSDT / ETHUSDT / LINKUSDT / UNIUSDT / COMPUSDT
- 24 months each, 2023-01 through 2024-12
- 120/120 archive objects available before Discovery
- no price rows emitted during the source gate

## Execution integrity

Final successful GitHub Actions run:
- Run: 36342514858
- Artifact: 10939376635
- Artifact digest: sha256:74aaf920665ffaa9574a70e0412b3fcd92c4200128bce0aa6687aebdaa56ccf8
- Receipt pre-self SHA256: 03098fa1a1b850efff87ca728ed8d74c529f9d35b73e56e1645de685c0e6f5ff

Two earlier attempts were technical-only failures before scientific output:
1. Blockscout block-timestamp HTTP 429.
2. Python import-line syntax defect introduced by the operational retry patch.
Neither produced a Discovery receipt or changed the frozen scientific contract.

The final runner hardened timestamp transport only. No asset, horizon, sign, sample threshold, inference rule or outcome gate changed.

## Sample gate

PASS:
- eligible episodes: 17
- represented assets: 4
- distinct ISO weeks: 12
- years represented: 2023 and 2024
- excluded episodes: 0

Frozen minimums were >=12 episodes, >=3 assets, >=8 weeks and both years.

## Primary result

Frozen expected sign: negative.

Observed:
- mean REL_24H: **+165.5784 bps**
- median REL_24H: **+210.2776 bps**
- negative-event fraction: **35.29%**
- UTC-week clustered bootstrap 95%: **[-16.2838, +373.7313] bps**
- asset means negative: **1/4 = 25%**
- every leave-one-episode-out mean remained **positive**, range +126.0071 to +216.4068 bps

By year:
- 2023: N=10, mean **+123.5604 bps**
- 2024: N=7, mean **+225.6040 bps**

By asset:
- COMPUSDT: N=6, mean **+357.8291 bps**
- ETHUSDT: N=3, mean **-64.1317 bps**
- LINKUSDT: N=4, mean **+174.6086 bps**
- UNIUSDT: N=4, mean **+40.4546 bps**

## Gate adjudication

- sample_pass: PASS
- mean_negative: FAIL
- bootstrap_upper_negative: FAIL
- >=75% asset means negative: FAIL
- both years negative: FAIL
- leave-one-episode-out all negative: FAIL

## Scientific verdict

**DISCOVERY_FAIL_NO_SUPPORT**

The frozen bearish inventory-overhang mechanism is contradicted by the Discovery evidence.

The exact child is terminally closed:
COMPOUND-INVENTORY-PERSISTENCE-001 / 24h asset-vs-BTC bearish response.

No direction inversion is authorized.
No 1h/6h/12h/48h horizon rescue is authorized.
No ETH-only selection is authorized.
No protocol-event subset or inventory-duration threshold rescue is authorized.
No 2025 OOS is opened because Discovery did not survive.

The positive observed sign is diagnostic only and earns zero promotion credit. Testing the opposite sign now would be post-outcome rescue of the same mechanism/corpus.

## What remains scientifically true

This failure does **not** erase the source finding that Compound frequently carries observable seized collateral inventory beyond the liquidation block.

It establishes only that this state did not support the prospectively frozen bearish 24h asset-vs-BTC hypothesis.

Any future Compound research must satisfy Governance V4's new-mechanism gate and cannot inherit credit from the positive diagnostic sign.

## Firewall

2025_plus_opened=false
fees_or_pnl_computed=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
paid_data=false
main_merge=false
post_outcome_tuning=false

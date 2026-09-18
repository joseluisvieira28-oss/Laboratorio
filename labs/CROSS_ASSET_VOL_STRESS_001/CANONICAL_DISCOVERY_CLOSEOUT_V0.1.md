# CROSS-ASSET-VOL-STRESS-001 — CANONICAL DISCOVERY CLOSEOUT V0.1

Date: 2026-09-18
Branch: `cross-asset-vol-stress-v0.1`
Lab: `CROSS-ASSET-VOL-STRESS-001`
MVE: `CAVS-VXSETTLE-W1-001`

## Canonical execution recovered

The one-shot Discovery had already executed successfully before the later execution-state audit.

Canonical GitHub Actions run:
- run: `35060815694`
- workflow: `CROSS-ASSET-VOL-STRESS-001 Discovery V0.1`
- head: `eb45a83f3e28250e93b0c0113e2157d346cae473`
- conclusion: `success`
- artifact: `cross-asset-vol-stress-001-discovery-35060815694-1`
- artifact ID: `10432536731`
- artifact digest: `sha256:6255bcaa5eacd923fb05fc482106f6f4a5ab24d9b0b0656e6f5741e12cd04a30`

No rerun was performed during this recovery.

## Frozen source binding

- Cboe canonical settlement SHA256:
  `48c16e171c06f61378ac216d75d76a22491b417ae904936c3538a34dfb6ab1be`
- source settlements: 366
- Binance Data Vision BTCUSDT spot 1d archives verified: 84
- BTC market manifest SHA256:
  `356cecbb48ba1ed1564d5b8b983e1be8afa9d921eb9f78ce662974eed8a0abfe`
- latest market date opened: 2024-12-31
- 2025 accessed: false
- 2026 accessed: false

## Frozen result

Classification: **DISCOVERY_FAIL_NO_PROMOTION**

Population:
- candidate signals: 363
- resolved trades: 350
- suppressed overlap: 13
- dropped outside window: 2
- dropped missing bar: 0
- longs: 191
- shorts: 159

Economics:
- mean gross: **-27.313237 bps/trade**
- median gross: **-23.332250 bps/trade**
- mean NET10: **-37.313237 bps/trade**
- mean NET20: **-47.313237 bps/trade**
- PF NET10: **0.8930577**
- win rate NET10: **48.2857%**

Frozen block bootstrap:
- repetitions: 5,000
- seed: 230911
- block length: 4 resolved trades
- 95% CI mean NET10: **[-132.113633, +50.706200] bps**

Calendar-year NET10 means:
- 2018: +46.663792 bps (N=49)
- 2019: -207.312893 bps (N=50)
- 2020: +58.601135 bps (N=49)
- 2021: +77.504329 bps (N=51)
- 2022: -125.115525 bps (N=51)
- 2023: -78.713603 bps (N=51)
- 2024: -28.763368 bps (N=49)

Non-negative years:
- 2018-2024: 3/7
- 2021-2024: 1/4

## Frozen promotion gates

PASS:
- N >= 300
- source binding
- 2025 firewall
- 2026 firewall
- no live trading
- no exchange mutation

FAIL:
- mean NET10 > 0
- PF NET10 > 1
- bootstrap 95% lower bound > 0
- >=5/7 non-negative years
- >=3/4 non-negative years in 2021-2024

All frozen promotion conditions were required.

## Scientific decision

The exact `CAVS-VXSETTLE-W1-001` hypothesis is **closed**.

The mechanism did not merely miss statistical significance: its aggregate gross and after-cost expectancy were negative, PF was below 1, and the recent 2021-2024 block was negative in three of four years.

No timing, sign, threshold, cost, weekly/monthly subset, year, or direction rescue is authorized.

2025 remains unopened. 2026 remains unopened.

## Safety

- orders submitted: false
- live trading: false
- exchange mutation: false
- full OOS/live promotion authorized: false
- merge to main: not authorized

This closeout resolves the later `DISCOVERY_AUTHORIZED_EXECUTION_STATE_UNVERIFIED` operational state: the prior one-shot existed and is now canonically recovered without duplication.

# USOPEN-VOL-001 / USOV-PREETF-001 — DISCOVERY CLOSEOUT

Date: 2026-09-23
Canonical execution branch: `us-open-volatility-shock-v0.1a-runner22`
Canonical run: `35920465721`
Scientific classification: `DISCOVERY_MECHANISM_SURVIVES_PREETF_ONLY`
Maturity: `M3 DISCOVERY`
Production impact: NONE
Live execution: FALSE

## Frozen question

Before U.S. spot Bitcoin ETFs existed, did the 09:30 America/New_York U.S. equity core open coincide with a reproducible cross-asset crypto volatility shock relative to immediately adjacent 30-minute windows?

## Frozen design

Discovery: 2022-01-01 through 2023-12-31 only.
Venue/source: Binance Data Vision USD-M Futures 5m monthly archives.
Universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT.
Timezone: America/New_York, DST-aware.
PRE: 09:00–09:30 ET.
OPEN: 09:30–10:00 ET.
POST: 10:00–10:30 ET.
RV: sum of squared 5m close-to-close log returns.
No direction, no PnL.

Source bundle SHA256:
`a2b15380cc5cf6e71750db8a9af07abd2086df5dbd183cf96406d51b2746cc70`

Protected periods opened: NONE.

## Sample

Distinct U.S. trading dates: **501**
Total symbol-days: **3,002**

Per-symbol:
- BTCUSDT: 501
- ETHUSDT: 501
- BNBUSDT: 501
- DOGEUSDT: 501
- SOLUSDT: 499
- XRPUSDT: 499

Source/data exclusions were minimal:
- no gap exclusions;
- 1 missing-clock day for BTC/ETH/BNB/DOGE;
- 2 missing-clock days for SOL/XRP;
- zero nonpositive-RV exclusions.

## Primary result — OPEN / PRE

Pooled median ratio: **1.9646630326×**
Date-cluster bootstrap 95%: **[1.7904141965×, 2.1087443208×]**

Frozen gate:
- median >= 1.20× — PASS
- bootstrap lower > 1.05× — PASS

Per-symbol median OPEN/PRE:
- BTCUSDT: **2.586161×**
- ETHUSDT: **2.473165×**
- BNBUSDT: **1.813721×**
- SOLUSDT: **1.775078×**
- DOGEUSDT: **1.720221×**
- XRPUSDT: **1.624950×**

Frozen breadth gate >=4 symbols above 1.10×:
**6 / 6 PASS**

## Confirmatory result — OPEN / POST

Pooled median ratio: **1.2492851263×**
Date-cluster bootstrap 95%: **[1.1310018802×, 1.3482725431×]**

Frozen gate:
- median >= 1.10× — PASS
- bootstrap lower > 1.00× — PASS

Per-symbol median OPEN/POST:
- BTCUSDT: 1.337098×
- ETHUSDT: 1.314022×
- XRPUSDT: 1.282301×
- DOGEUSDT: 1.250259×
- SOLUSDT: 1.200375×
- BNBUSDT: 1.081816×

## Temporal breadth

2022 pooled date-median OPEN/PRE: **2.463691×**
2023 pooled date-median OPEN/PRE: **1.595339×**

Frozen gate: both years >1.05×.
Result: **2 / 2 PASS**.

## Descriptive volume corroboration

Median OPEN/PRE base-volume ratios:
- BTC 1.7825×
- ETH 1.8362×
- SOL 1.4249×
- BNB 1.3838×
- XRP 1.3630×
- DOGE 1.4610×

Volume was diagnostic only and carried no pass/fail authority.

## Scientific verdict

**DISCOVERY_MECHANISM_SURVIVES_PREETF_ONLY**

The exact pre-ETF 09:30 ET mechanism passed every prospectively frozen Discovery gate. The U.S. cash-open clock is associated with a large, broad and temporally repeated concentration of crypto realized variance during 2022–2023.

This does NOT establish:
- directional predictability;
- profitable trading;
- implied-vs-realized-volatility monetization;
- ETF causality;
- a post-2024 effect;
- Tier 3/2/1 promotion;
- live eligibility.

## Critical interpretation boundary

Recent literature known before execution suggests the New-York-clock effect changed after U.S. spot Bitcoin ETFs launched in 2024. USOV-PREETF-001 intentionally did not access that regime.

Therefore:
- 2024 remains an untouched prospective replication/structural-break candidate;
- 2025 and 2026 remain closed;
- the exact next scientific action requires a separate pre-outcome replication freeze;
- no threshold/window/asset tuning is permitted.

## USORB relationship

USORB-001 directional continuation was NO_EDGE.

USOPEN-VOL-001 shows that the same clock can contain a strong **second-moment** effect while carrying no demonstrated directional continuation edge.

This distinction is scientifically important and must be preserved.

## Technical execution chain

Original run `35919992368` remained queued before outcome access.
Technical supersession changed only hosted runner label from ubuntu-latest to ubuntu-22.04.
Canonical successful run: `35920465721`.

Duplicate later executions, if any, receive zero additional scientific credit.

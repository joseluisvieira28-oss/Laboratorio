# CED-1D AVAX20 — V3 TIER-2 EXECUTION RE-ADJUDICATION CLOSEOUT — 2026-09-18

**Status:** HISTORICAL VERDICTS PRESERVED / RE-ADJUDICATED UNDER PROMOTION POLICY V3  
**Candidate:** `CED1D-0031` — AVAXUSDT Momentum 20D CONTINUATION H1D  
**Current V3 classification:** **TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE**  
**Scope:** exactly 100 USDT research notional per entry/exit leg.  
**This closeout does not authorize live trading, capital, orders, wallets, exchange mutation, alerts/webhooks or merge to main.**

## 1. Historical lineage preserved

The historical strict V0.2 Confirmation verdict remains immutable:

`V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`

The earlier V3 state after the 2025 one-shot was:

`TIER 3 HIGH — WATCHLIST / NOT TIER 2`

That earlier state was caused by unresolved execution realism plus strict V0.2 uncertainty/stability/neighbour gates. It is not deleted or rewritten.

Promotion Policy V3 is applied additively here after a prospectively frozen execution-feasibility program completed.

## 2. Independent 2025 OOS parent

One-shot Confirmation:
- run: `35340971526`
- artifact ID: `10545241942`
- artifact digest: `sha256:43984d73541085b76c9071e959de34284a8940e5968e10f04664cf56369987b5`
- receipt fingerprint: `848e3979ee97b7a247750afdf482e496c2efbb6cae25af0274805329ebaf4d32`

CED1D-0031 independent 2025 lower funded path:
- inference N: **357**
- complete signal-week clusters: **51**
- active months: **12**
- BASE mean: **+8.550675 bps/event**
- BASE PF: **1.047736**
- STRESS mean: **+2.550675 bps/event**
- positive months: **7 / 12**
- concentration gate: PASS
- 2026 accessed: NO

Classical uncertainty remained weak:
- one-sided bootstrap p: **0.4010**
- Holm-adjusted p: **1.0**
- 95% bootstrap CI: **[-41.012511, +56.040451] bps**
- leave-one-month-out all positive: FALSE
- immediate-neighbour support: 0 / 2

Those fragilities remain disclosed. V3 does not reinterpret them as a strict V0.2 PASS.

## 3. First execution proxy — immutable aggTrades result

Methodology freeze:
`governance/CED_1D_AVAX20_V3_EXECUTION_FEASIBILITY_FREEZE_2026-09-18.md`

Implementation freeze:
`governance/CED_1D_AVAX20_V3_EXECUTION_IMPLEMENTATION_FREEZE_2026-09-18.md`

Synthetic QA:
- run: `35342357307`
- conclusion: SUCCESS
- real AVAXUSDT 2025 aggTrades accessed by QA: false

Real deterministic execution audit:
- run: `35342472136`
- artifact ID: `10546145535`
- artifact digest: `sha256:5b784d64aa9d2741f9c16c331d7e75f9d428bf5912e5fe8e59815292df288d84`
- receipt fingerprint: `8d776b3a2387d3ae9711c522278a95f77d1d4590264a7bb1f7fc6c1e48309a25`
- receipt raw SHA256: `8171ea989017acc7da71fba34de8a7dc748c765957531fd4037aeb6660e34aa6`
- legs CSV SHA256: `54949867308986e4aedebc6dc07dd758b930c4aab24299a7a7b1f458bf18a7e8`

Frozen proxy:
- Binance USD-M AVAXUSDT 2025 monthly aggTrades
- 100 USDT per leg
- exact 00:01 UTC reference timestamp
- same-side observed taker prints
- maximum 5,000 ms accumulation
- BASE taker fee floor: 4 bps/fill = 8 bps RT
- STRESS fee floor: 5 bps/fill = 10 bps RT
- no maker/VIP/BNB discount
- no price interpolation or favourable substitution

Result:
- required legs: 714
- observed-print proxy legs: **674 / 714 = 94.3978%**
- complete observed-print pairs: **320 / 357 = 89.6359%**
- original 99% print-visibility gates: FAIL
- median leg latency: **516 ms**
- p95 leg latency: **3,406.65 ms**
- mean total nonfunding BASE proxy: **7.0435 bps**
- p95 total nonfunding BASE proxy: **8.7297 bps**
- BASE executable funded mean on observable pairs: **+24.1642 bps**
- BASE PF: **1.133893**
- STRESS executable funded mean: **+22.1642 bps**
- STRESS PF: **1.122151**
- concentration: PASS

The first result remains exactly:
`EXECUTION_FEASIBILITY_FAIL`

It failed because an observed same-side aggressive print was not visible often enough inside the frozen 5-second window. That FAIL is preserved permanently as a print-observability fragility.

## 4. Orthogonal bookDepth capacity corroboration

Because absence of an aggressive print does not prove absence of opposite-side passive capacity, an orthogonal capacity gate was frozen before opening real bookDepth data.

Methodology freeze:
`governance/CED_1D_AVAX20_V3_BOOKDEPTH_CAPACITY_CORROBORATION_FREEZE_2026-09-18.md`
- Git blob: `7711e728304ebc9eadd760990f38b7a6d6e0f947`

Implementation freeze:
`governance/CED_1D_AVAX20_V3_BOOKDEPTH_CAPACITY_IMPLEMENTATION_FREEZE_2026-09-18.md`
- Git blob: `9f5e11f98156d3bb17daf0fcdf2e4aaa087fe95d`

Frozen runner:
- `ced_1d_avax20_bookdepth_capacity_v01.py`
- Git blob: `dc804f77b608be98963eb654b51292e7fbefbee6`

Frozen synthetic QA:
- Git blob: `e548676679148b27d0b3d766241c6e9582aae6e0`
- run: `35344682797`
- conclusion: SUCCESS
- real bookDepth accessed by QA: false

Real all-714-leg capacity run:
- run: `35344769991`
- head: `946051da5eabe3d4068d2da7b07814e528d4934b`
- artifact ID: `10546238956`
- artifact digest: `sha256:041514940dc9036669c49a13bc746a73961104057ef2c8bbad022e79c08edba7`
- receipt fingerprint: `3eae9166255698ab41e631392ff43a906b1287a7a7c1241f3d7b10d4871b1dca`
- receipt raw SHA256: `ef3ee79721be12203d3f44f7c7cc5e85c01124dfc6b44fa9d3907bf60b3284c9`
- capacity legs CSV SHA256: `6f9c5045094685e765dcbc1b7be98e860a6b22b8eb1db7963094913475193ea0`

Frozen capacity semantics:
- official Binance USD-M daily AVAXUSDT bookDepth 2025
- all 714 immutable legs
- BUY -> +1% cumulative ask-side band
- SELL -> -1% cumulative bid-side band
- latest snapshot <= reference timestamp
- maximum snapshot age 60 seconds
- no future snapshot, interpolation, exact-BBO inference or fill-price inference
- required cumulative notional >=100 USDT

Result:
- source failures: **0**
- valid prior snapshots: **710 / 714 = 99.4398%**
- capacity >=100 USDT: **710 / 714 = 99.4398%**
- every active month capacity coverage >=95%: **PASS**
- June: 58/60 = 96.6667%
- November: 58/60 = 96.6667%
- all other active months: 100%
- minimum observed cumulative ±1% notional: **241.387 USDT**
- p05: **1,884,794.36615 USDT**
- median: **3,529,797.8565 USDT**
- p95: **5,338,699.35745 USDT**
- median snapshot age: **8,000 ms**
- p95 snapshot age: **51,000 ms**
- max snapshot age: **52,000 ms**
- prior aggTrades print-miss legs with bookDepth capacity: **39 / 40 = 97.5%**

BookDepth status:
`BOOKDEPTH_CAPACITY_PASS`

Frozen composite field:
`composite_execution_feasible = true`

## 5. Promotion Policy V3 adjudication

Universal eligibility relevant to this candidate:
- clean immutable provenance: PASS
- no post-outcome signal/lookback/horizon/direction/event change: PASS
- independent 2025 OOS sample adequate: PASS, N=357
- independent OOS BASE economics positive: PASS
- independent OOS PF >1: PASS
- expected sign: PASS
- major temporal support: PASS, 7/12 positive months
- catastrophic concentration: NO
- execution feasibility at frozen 100-USDT research notional: PASS by prospectively frozen composite gate
- first aggTrades print-observability FAIL: preserved as a fragility, not deleted

### Current V3 decision

**TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE**

This is a Promotion Policy V3 Standard Replication Path promotion. It is additive only.

It is **not Tier 1** because:
- no genuinely prospective post-freeze shadow/forward validation has yet demonstrated operational integrity;
- classical uncertainty in the 2025 OOS remains weak;
- strict V0.2 Confirmation remains FAIL;
- first 5-second same-side-print visibility remains materially below 99%;
- capacity evidence is established only for the fixed 100-USDT research notional and may not be extrapolated to larger capital.

## 6. Mandatory fragility flags

1. **Observed-print visibility fragility:** aggTrades 674/714 legs and 320/357 complete pairs.
2. **Statistical fragility:** p=.401, Holm=1.0, CI crosses zero.
3. **Temporal fragility:** LOMO all-positive failed.
4. **Neighbour fragility:** immediate-neighbour support 0/2.
5. **Capacity scope:** composite feasibility is valid only for exactly 100 USDT/leg under the frozen public-data proxies.
6. **Public-data limitation:** bookDepth ±1% is capacity corroboration, not exact historical BBO/order-book replay.
7. **No Tier-1 operational evidence yet:** shadow is still required prospectively.

## 7. Next gate

Prospectively freeze a non-live AVAX20 shadow/preflight specification.

No historical 2026 backfill is authorized by this closeout. Any shadow observation must begin strictly after the shadow freeze and use:
- unchanged CED1D-0031 signal;
- unchanged 20D continuation / H1D;
- unchanged 100-USDT research-notional execution envelope;
- unchanged or more conservative fees;
- no live orders or exchange mutation.

## 8. Stop / firewall

- no second 2025 OOS shot
- no retrospective 2026 backfill
- no signal or parameter tuning
- no fee reduction
- no maker rescue
- no larger-notional extrapolation
- no live trading
- no orders
- no wallets
- no exchange mutation
- no alerts/webhooks that execute
- no merge to main

**Final current state:** CED1D-0031 is a V3 Tier-2 Promoted Candidate / Quase Diamante with execution-print-observability and statistical fragility, eligible to proceed only to frozen shadow/preflight research.

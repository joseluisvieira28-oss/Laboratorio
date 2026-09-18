# CED-1D V3 — FINAL RECOVERY / CONFIRMATION / EXECUTION CLOSEOUT — 2026-09-18

**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`  
**Status:** FINAL V3 ADJUDICATION COMPLETE  
**Main merge:** NOT AUTHORIZED / NOT PERFORMED

## 1. Scientific lineage preserved

Historical V1/V2 verdicts are immutable. This closeout adds only:

**HISTORICAL VERDICT PRESERVED / RE-ADJUDICATED UNDER PROMOTION POLICY V3**

No signal, direction, lookback, horizon, event population or cost was changed after outcomes.

2026+ remained closed throughout this mission.

## 2. Discovery reproduction / recovery status

Canonical 2021-2024 Discovery reproduction completed before 2025 was opened:
- byte-exact source recovery: PASS
- 480/480 Discovery monthly USD-M 1m sources authenticated
- original V0.3 runner regression: PASS
- exact daily fingerprint reproduced
- historical three Momentum survivors preserved:
  - CED1D-0031 AVAXUSDT Momentum 20D CONTINUATION H1
  - CED1D-0241 SOLUSDT Momentum 20D CONTINUATION H1
  - CED1D-0251 SOLUSDT Momentum 60D CONTINUATION H1

## 3. Independent 2025 one-shot Confirmation

GitHub Actions run: `35340971526` — SUCCESS  
Artifact ID: `10545241942`  
Artifact SHA256: `43984d73541085b76c9071e959de34284a8940e5968e10f04664cf56369987b5`

The 2025 block was opened exactly once after the protocol, source, funding and implementation freezes.

### CED1D-0031 — AVAX20

N = 357.

Conservative funded path:
- BASE14 mean: **+8.550675 bps/event**
- BASE14 PF: **1.047736**
- STRESS20 mean: **+2.550675 bps/event**
- positive active months: **7/12**
- positive quarters: **2/4**
- max month absolute-PnL share: **12.303%**
- top-5 absolute-PnL share: **6.574%**
- max day absolute-PnL share: **2.062%**

Strict V0.2 Confirmation remains FAIL:
- one-sided bootstrap p = **0.4010**
- 95% bootstrap CI = **[-41.0125, +56.0405] bps**
- Holm adjusted p = 1.0
- leave-one-month-out = FAIL
- neighbour stability = FAIL

This historical strict failure is not rewritten.

### CED1D-0241 — SOL20

N = 356.
- funded BASE mean: approximately **-14.91 bps/event**
- BASE PF: approximately **0.913**

Independent 2025 materially contradicts the exact candidate.

### CED1D-0251 — SOL60

N = 357.
- funded BASE mean: approximately **-37.86 bps/event**
- BASE PF: approximately **0.793**

Independent 2025 materially contradicts the exact candidate.

## 4. AVAX20 execution evidence — first frozen aggTrades proxy

GitHub Actions run: `35342472136` — SUCCESS  
Artifact ID: `10546145535`  
Artifact SHA256: `5b784d64aa9d2741f9c16c331d7e75f9d428bf5912e5fe8e59815292df288d84`  
Receipt fingerprint: `8d776b3a2387d3ae9711c522278a95f77d1d4590264a7bb1f7fc6c1e48309a25`

Frozen tiny-notional assumptions:
- AVAXUSDT USD-M
- 100 USDT per leg
- taker-only
- 5-second observed same-side print window
- BASE fee floor = 4 bps/fill = 8 bps round-trip
- STRESS fee floor = 5 bps/fill = 10 bps round-trip
- no maker/VIP/BNB rescue

Immutable first-proxy result:
- observed leg fill visibility: **674/714 = 94.3978%** — FAIL versus frozen 99%
- complete pairs: **320/357 = 89.6359%** — FAIL versus frozen 99%
- median observed latency: **516 ms** — PASS
- p95 observed latency: **3406.65 ms** — PASS
- mean total nonfunding proxy: **7.0435 bps** — PASS versus 14
- p95 total nonfunding proxy: **8.7297 bps** — PASS versus 20
- BASE executable funded mean on 320 complete pairs: **+24.1642 bps**
- BASE executable funded PF: **1.13389**
- STRESS executable funded mean: **+22.1642 bps**
- STRESS executable funded PF: **1.12215**
- concentration: PASS

The first proxy verdict remains:
**EXECUTION_FEASIBILITY_FAIL**

Reason: print-observability fill coverage only. This failure is preserved and disclosed.

## 5. Orthogonal bookDepth capacity corroboration

Methodology and implementation were frozen before AVAXUSDT 2025 bookDepth access.

GitHub Actions run: `35344769991` — SUCCESS  
Artifact ID: `10546238956`  
Artifact SHA256: `041514940dc9036669c49a13bc746a73961104057ef2c8bbad022e79c08edba7`  
Receipt fingerprint: `3eae9166255698ab41e631392ff43a906b1287a7a7c1241f3d7b10d4871b1dca`

All 714 immutable entry/exit legs were evaluated; the prior 40 print misses were not selectively substituted.

Frozen capacity target:
- 100 USDT per leg
- latest prior bookDepth snapshot only
- max snapshot age 60s
- ±1% cumulative side-specific notional
- BUY -> ask +1%
- SELL -> bid -1%
- no future snapshot/interpolation
- no BBO/fill-price claim from bookDepth

Result:
- valid prior snapshots/capacity: **710/714 = 99.4398%**
- source/checksum failures: **0**
- every active month: **>=95%**
- June: 58/60 = 96.67%
- November: 58/60 = 96.67%
- all other active months: 100%
- median snapshot age: **8 seconds**
- p95 snapshot age: **51 seconds**
- maximum admitted snapshot age: **52 seconds**
- minimum observed side-specific ±1% notional: **241.387 USDT**
- p05 capacity: **1,884,794.37 USDT**
- median capacity: **3,529,797.86 USDT**
- p95 capacity: **5,338,699.36 USDT**
- prior aggTrades print-miss legs with capacity observed: **39/40 = 97.5%**

Result:
**BOOKDEPTH_CAPACITY_PASS**

Composite frozen adjudicator:
**COMPOSITE_EXECUTION_FEASIBLE = TRUE**

The first aggTrades print-visibility FAIL remains a mandatory fragility and is not overwritten.

## 6. Final V3 adjudication

Final routing rule was frozen before the bookDepth outcome in:
`governance/CED_1D_V3_FINAL_ADJUDICATION_RULE_FREEZE_2026-09-18.md`

### CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1

**TIER 2 — PROMOTED CANDIDATE / QUASE DIAMANTE**

Basis:
- immutable identity/provenance: PASS
- no rescue/hindsight/sign flip: PASS
- genuinely independent 2025 OOS: PASS
- N=357: adequate under mechanism-specific Confirmation floor
- independent OOS BASE funded mean >0: PASS
- independent OOS PF>1: PASS
- STRESS20 mean >0: PASS
- at least half of major monthly blocks positive: 7/12 PASS under V3
- catastrophic concentration: absent
- execution-cost economics under frozen tiny-notional proxy: PASS
- capacity corroboration across all immutable legs: PASS
- composite execution feasibility at 100 USDT research notional: PASS
- no independent block materially destroys BASE economics: PASS

Mandatory fragilities:
- strict V0.2 statistical Confirmation FAIL remains immutable
- p=0.401 and CI crosses zero
- only 7/12 positive months, 2/4 quarters
- leave-one-month-out FAIL
- neighbour stability FAIL
- first 5-second same-side print-visibility proxy fails its 99% fill requirement
- bookDepth is a capacity surface, not historical exact BBO
- execution evidence is valid only for the frozen **100 USDT tiny research notional**, not production scaling

This is **not Tier 1** and does not establish permanence of edge.

### CED1D-0241 — SOL20

**TIER 4 — REJECTED**

Independent 2025 materially negative under realistic frozen BASE economics.

### CED1D-0251 — SOL60

**TIER 4 — REJECTED**

Independent 2025 materially negative under realistic frozen BASE economics.

## 7. Live / capital boundary

Tier 2 is research promotion only.

Still forbidden:
- live trading
- orders
- exchange mutation
- wallets
- production capital
- leverage deployment
- alerts/webhooks
- merge to main

## 8. Next scientific stage

The exact AVAX20 Tier-2 candidate may proceed to:
1. frozen shadow specification;
2. read-only execution preflight;
3. prospectively defined shadow/forward operational validation.

No 2026 outcome data is authorized by this closeout.

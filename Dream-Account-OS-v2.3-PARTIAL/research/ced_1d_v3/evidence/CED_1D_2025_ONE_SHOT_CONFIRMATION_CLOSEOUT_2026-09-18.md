# CED-1D-V1 / MVE-CED1D-MOMENTUM-01 — 2025 ONE-SHOT CONFIRMATION CLOSEOUT — 2026-09-18

**Status:** ONE_SHOT_2025_CONFIRMATION_COMPLETE / APPEND-ONLY CLOSEOUT  
**Historical verdicts preserved / re-adjudicated under Promotion Policy V3.**  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`

## Execution identity

- one-shot GitHub Actions run: `35340971526`
- authorization commit: `0c24e455b626ca8fbfb64fad02223fc035345dd6`
- implementation freeze commit: `c8788eeab2f3de3d965b59cd5b81a9f48143b9e8`
- artifact ID: `10545241942`
- artifact name: `ced1d-2025-one-shot-confirmation`
- artifact digest: `sha256:43984d73541085b76c9071e959de34284a8940e5968e10f04664cf56369987b5`
- one-shot receipt fingerprint: `848e3979ee97b7a247750afdf482e496c2efbb6cae25af0274805329ebaf4d32`
- one-shot receipt file SHA256: `71f39472645c941aebb08ea9ae0cf0cf66479fe1a29d953e622b5710faa9c60e`
- event ledger SHA256: `4163dc34f063364fa05077d18a7a48d3694a0cb3b28cb38b62321158052aaab2`
- summary SHA256: `c57d22175db7d62192f00684308a0c5cf17da75c32de97fbd7349ee6a2b73787`

Governance preserved:
- 2025 opened exactly once: YES
- 2026+ accessed: NO
- second 2025 shot: NOT AUTHORIZED
- post-outcome tuning: NO
- live trading / orders / exchange mutation / wallets / alerts-webhooks: NO
- merge to main: NO

## Source and funding provenance

Price source gate:
- 32 / 32 AVAXUSDT + SOLUSDT monthly Binance USD-M 1m archives PASS
- warm-up: 2024-09 through 2024-12
- Confirmation: 2025-01 through 2025-12
- source-gate run: `35339925864`
- source-gate artifact digest: `sha256:34b0bd7ef27c2ea4532124dfa6ae90b3adaa72e5321d74ea2840ac624bd76f95`
- source receipt fingerprint: `f6b488fbc2562df29916a30e651f48a4af48b19106ff623dc977d32fbf66cac7`

Funding-rate source:
- 1095 / 1095 AVAXUSDT 2025 funding settlements PASS
- 1095 / 1095 SOLUSDT 2025 funding settlements PASS
- funding source run: `35339781808`
- artifact digest: `sha256:95f20a1a01589dfde441d0499b752f472d2e3d7611c88f2d5ba76abe26a47227`
- receipt fingerprint: `85cb288d811e65d1bfb2d4b104b1f7b807a9b35c6ec89b21dfaa5e111c78fc90`

Funding mark-price interval source:
- official Binance USD-M 1m markPriceKlines
- settlement binding: floor(fundingTime / 60000) * 60000
- AVAXUSDT: 1095 / 1095 settlements bound
- SOLUSDT: 1095 / 1095 settlements bound
- missing settlements: 0
- point estimate selected: NONE
- source-supported LOW/HIGH interval preserved
- source-gate run: `35340535553`
- artifact digest: `sha256:47478799d70a1c2b30265b48ab0950e3b1d56a0b3c457011314845189e71e8dc`
- receipt fingerprint: `c7552387cad825063f7e238cd2c4939fabd08891710be2f70e1b74b8fa5504d0`

## Frozen confirmatory family

Primary targets:
1. CED1D-0031 — AVAXUSDT — Momentum 20D — CONTINUATION — H1D
2. CED1D-0241 — SOLUSDT — Momentum 20D — CONTINUATION — H1D
3. CED1D-0251 — SOLUSDT — Momentum 60D — CONTINUATION — H1D

Fixed Holm-8 family:
- CED1D-0031
- CED1D-0033
- CED1D-0041
- CED1D-0241
- CED1D-0243
- CED1D-0251
- CED1D-0253
- CED1D-0261

Frozen costs:
- BASE funded nonfunding floor = 14 bps round-trip + funding
- STRESS funded nonfunding floor = 20 bps round-trip + funding

Funding uncertainty was adjudicated on:
- LOWER conservative funded path
- UPPER optimistic funded path

The lower/upper interval did not change any target verdict.

## Target 1 — CED1D-0031 — AVAXUSDT 20D CONT H1D

Sample:
- inference N = 357
- active days = 357
- complete signal-week clusters = 51
- active months = 12
- sample gate = PASS

Conservative LOWER funded path:
- BASE mean = **+8.550675 bps/event**
- BASE PF = **1.047736**
- BASE median = -16.866716 bps
- win rate = 48.7395%
- STRESS mean = **+2.550675 bps/event**
- bootstrap p = **0.4010**
- 95% bootstrap CI = **[-41.012511, +56.040451] bps**
- Holm-adjusted p = **1.0**
- positive active months = **58.33%**
- positive quarters = **2**
- leave-one-month-out all positive = FALSE
- neighbour support = **0 / 2**
- concentration ratio = 0.410100 — PASS

Optimistic UPPER funded path:
- BASE mean = +8.555831 bps/event
- BASE PF = 1.047765
- STRESS mean = +2.555831 bps/event
- bootstrap p = 0.4009
- 95% CI = [-41.007665, +56.045605]
- Holm-adjusted p = 1.0
- same strict routing failure

Frozen V0.2 verdict:
`V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`

Promotion Policy V3 adjudication:
**TIER 3 HIGH — WATCHLIST / NOT TIER 2.**

Reason:
- independent 2025 economics remain base-positive and PF>1;
- stress remains slightly positive;
- therefore the independent block does NOT materially contradict/destroy the exact AVAX target and Tier 4 is not warranted;
- however the strict Confirmation failed uncertainty, Holm, temporal stability, leave-one-month-out and neighbour-support gates;
- execution remains reference-price research rather than independently verified executable fills;
- universal Tier-2 eligibility is therefore not met.

No Quase Diamante promotion. No shadow/micro-live authorization.

## Target 2 — CED1D-0241 — SOLUSDT 20D CONT H1D

Sample:
- inference N = 356
- active days = 356
- complete signal-week clusters = 51
- active months = 12
- sample gate = PASS

Conservative LOWER:
- BASE mean = **-14.911125 bps/event**
- BASE PF = **0.912854**
- STRESS mean = **-20.911125 bps/event**
- bootstrap p = 0.7847
- 95% CI = [-57.950820, +26.592173]
- Holm-adjusted p = 1.0
- positive active months = 50%
- positive quarters = 1
- neighbour support = 0 / 2
- LOMO all positive = FALSE

Optimistic UPPER:
- BASE mean = **-14.906760 bps/event**
- BASE PF = **0.912879**
- STRESS mean = **-20.906760 bps/event**
- bootstrap p = 0.7847
- 95% CI = [-57.946460, +26.598985]
- Holm-adjusted p = 1.0

Frozen V0.2 verdict:
`V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`

Promotion Policy V3 adjudication:
**TIER 4 — REJECTED / EXACT CANDIDATE CLOSED.**

Reason:
- adequate genuinely independent 2025 sample;
- materially negative BASE expectancy;
- PF materially below 1;
- STRESS materially negative;
- even the optimistic funding-bound path remains negative;
- independent validation materially contradicts the exact target.

Historical positive Discovery evidence remains preserved. No parameter/lookback/asset/cost/subperiod rescue.

## Target 3 — CED1D-0251 — SOLUSDT 60D CONT H1D

Sample:
- inference N = 357
- active days = 357
- complete signal-week clusters = 51
- active months = 12
- sample gate = PASS

Conservative LOWER:
- BASE mean = **-37.856067 bps/event**
- BASE PF = **0.792964**
- STRESS mean = **-43.856067 bps/event**
- bootstrap p = 0.9272
- 95% CI = [-90.789755, +12.813798]
- Holm-adjusted p = 1.0
- positive active months = 58.33%
- positive quarters = 0
- neighbour support = 0 / 3
- LOMO all positive = FALSE

Optimistic UPPER:
- BASE mean = **-37.851706 bps/event**
- BASE PF = **0.792984**
- STRESS mean = **-43.851706 bps/event**
- bootstrap p = 0.9272
- 95% CI = [-90.784972, +12.816885]
- Holm-adjusted p = 1.0

Frozen V0.2 verdict:
`V02_CONFIRMATION_FAIL_ROBUST_TO_MARK_INTERVAL`

Promotion Policy V3 adjudication:
**TIER 4 — REJECTED / EXACT CANDIDATE CLOSED.**

Reason:
- adequate independent 2025 sample;
- strongly negative BASE expectancy;
- PF materially below 1;
- STRESS strongly negative;
- optimistic funding-bound path remains materially negative;
- independent validation destroys the exact target.

Historical Discovery evidence remains preserved. No rescue.

## Neighbour diagnostics

- CED1D-0033 AVAX20 H3: N=119 — sample FAIL; BASE LOWER +45.6491 bps
- CED1D-0041 AVAX60 H1: N=357 — sample PASS; BASE LOWER -14.0634 bps
- CED1D-0243 SOL20 H3: N=118 — sample FAIL; BASE LOWER -21.4936 bps
- CED1D-0253 SOL60 H3: N=119 — sample FAIL; BASE LOWER -25.4908 bps
- CED1D-0261 SOL120 H1: N=357 — sample PASS; BASE LOWER -23.3796 bps

Neighbour cells remain dependency diagnostics only. None may be promoted or substituted for a failed primary target.

## Family closeout

MVE-CED1D-MOMENTUM-01 family-wide strict Confirmation: **FAIL**.

Current V3 composition:
- CED1D-0031 AVAX20/H1D: **TIER 3 HIGH — WATCHLIST**
- CED1D-0241 SOL20/H1D: **TIER 4 — REJECTED**
- CED1D-0251 SOL60/H1D: **TIER 4 — REJECTED**

Family-level Tier 2 / Quase Diamante: **NO**.

The AVAX exact target remains scientifically alive only as positive-but-unconfirmed Tier-3 evidence. Advancement requires materially new, prospectively frozen independent evidence under a new authority; the 2025 block cannot be reopened or reused as a second shot.

The two SOL exact targets are closed under V3 and cannot be resurrected by post-outcome tuning, fee reduction, timeframe switching, subperiod selection or parameter rescue.

## Stop rule

- no second 2025 execution
- no 2026 access under this closeout
- no post-outcome tuning
- no new CED1D cell admitted from the Holm neighbours
- no live trading
- no orders / wallets / exchange mutation
- no alerts/webhooks
- no main merge

Any materially new research must receive a new prospective hypothesis/authority and preserve this closeout unchanged.

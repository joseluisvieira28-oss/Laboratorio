# OPTIONS-EXPIRY-REVERSAL-001 — DISCOVERY CLOSEOUT — 2026-09-14

## Final status

**Classification: NO_STATISTICAL_EDGE**

**Promoted: NO**

This MVE is closed. No rescue, inversion, threshold change, horizon change, cost change, favorable-period selection, or post-outcome tuning is authorized.

## Identity

- Lab: `OPTIONS-EXPIRY-REVERSAL-001`
- MVE: `OER-BTC-EXPIRY-INTENSITY-30M-001`
- Branch: `options-expiry-reversal-v0.1`
- Final valid Discovery run: `34900690132`
- Final valid Discovery job: `104165658449`
- Final run HEAD: `9e7c5a80d19a0fcafccb5f1ec0f06e3a4f1b94cf`
- Discovery artifact: `options-expiry-reversal-001-discovery-34900690132-1`
- Artifact ID: `10370099840`
- Artifact ZIP SHA256: `a0554f607d6dd523d2b7bf48dab27a4dc78ff4d433217a5d40631298b6e8cbb4`

## Frozen source chain

- Source run: `34899455218`
- Source classification: `SOURCE_DATASET_PASS`
- Source artifact digest: `ca1e77088a0b9d46d481d7737047b8117ceab3ad728f3266657970ae54a269be`
- Source CSV SHA256: `36e9926b4dc5981345412b5be9676dcaea3b3f73c603490233d8fc405a99293b`
- Protocol SHA256: `f8a3059436c4f78a981410a9d4dd1df6f25f5a7c731b622ce83fa0df4a328853`
- Execution semantics SHA256: `d5237d9829a3f187f977c5fdad568e3eea4e2ae9f68e0caa6a763fffc5662388`

Source gate evidence before outcomes:
- 13,579,608 Deribit BTC option trades read;
- 2,093/2,093 raw pages hash-verified;
- 1,340 source days;
- 675 HIGH expiry-pressure days;
- no 2025 access;
- no 2026 access;
- no BTC outcome data in source gate;
- no OI/GEX fabrication.

## Pre-outcome technical failures and remediation

Two attempts terminated during BTC price acquisition before any `r_pre`, `r_post`, regression, bootstrap, trade return, PnL, or promotion metric was computed:

1. run `34900018454` — monthly Binance Spot BTCUSDT 1m archive lacked the four exact required points on 2021-09-29;
2. run `34900340495` — same-source official daily Binance archive also lacked those points.

These are preserved as `TECHNICAL_FAILURE_PREOUTCOME`, not scientific outcomes.

Pre-outcome authorities:
- `PRE_OUTCOME_TECHNICAL_REMEDIATION_001.md` SHA256 `1820eed5602e04821dc40ca9a2b7679943f1b5bc3ea0e30b37c72183fcef58c3`
- `PRE_OUTCOME_MARKET_CLOSURE_EXCLUSION_001.md` SHA256 `9b2b00b86545247cab61df1583fad7d53603eee961d4a426b82ac5ed42e1755f`

2021-09-29 was excluded before outcome construction as `NON_EVALUABLE_MARKET_CLOSED`, based on the documented Binance Spot trading suspension covering the frozen execution window. No replacement exchange, interpolation, nearest-minute substitution, or synthetic price was used.

Final protected evaluable rows: **1,339**.

## Frozen hypothesis

On HIGH expiry-pressure days, the BTC movement from 07:30 to 08:00 UTC was expected to reverse more strongly from 08:01 to 08:31 UTC.

Primary interaction coefficient expected direction: `beta_int < 0`.

Bootstrap:
- block length: 7 rows;
- replications: 20,000;
- seed: 20260914;
- one-sided alternative: `beta_int < 0`.

Companion reversal strategy:
- HIGH days only;
- reverse the sign of `r_pre` for the 08:01→08:31 window;
- frozen cost diagnostics: NET10 and NET14.

## Final statistical result

OLS coefficients:
- alpha: `-0.00003225978904768506`
- beta_pre: `-0.027000890102648323`
- beta_high: `+0.0001322989058513968`
- **beta_int: `+0.024125214373706384`**

The interaction coefficient is opposite the frozen expected direction.

Bootstrap:
- beta_int mean: `+0.0325332410794652`
- beta_int median: `+0.032405696430823985`
- **one-sided p(beta_int < 0): `0.6475176241187941`**

Primary statistical gate fails.

## Final economics

Trades: **675**

- mean gross: **+0.4511109100263239 bps/trade**
- mean NET10: **-9.548889089973677 bps/trade**
- mean NET14: **-13.548889089973676 bps/trade**
- NET14 profit factor: **0.33861813661996254**
- NET14 win rate: **30.5185185185%**
- cumulative NET14 return: **-60.1596294415%**
- max drawdown NET14: **-60.5130707983%**
- positive-gross max yearly concentration: **29.0877581909%**

## Calendar partitions

| Year | N | Mean gross bps | Mean NET14 bps | NET14 nonnegative |
|---|---:|---:|---:|---|
| 2021 | 126 | -4.7451 | -18.7451 | NO |
| 2022 | 180 | +0.6803 | -13.3197 | NO |
| 2023 | 187 | +3.6913 | -10.3087 | NO |
| 2024 | 182 | +0.4926 | -13.5074 | NO |

Result: **0/4** yearly partitions nonnegative at NET14.

## Promotion gates

- source_pass: PASS
- beta_int_negative: **FAIL**
- bootstrap_p_le_005: **FAIL**
- mean_net10_positive: **FAIL**
- mean_net14_positive: **FAIL**
- pf_net14_gt_1: **FAIL**
- calendar_partitions_3_of_4_nonnegative_net14: **FAIL**
- positive_gross_concentration_le_60pct: PASS

Only 2/8 gates pass. This is not a near miss.

## Final decision

`OPTIONS-EXPIRY-REVERSAL-001 / OER-BTC-EXPIRY-INTENSITY-30M-001` is **FAILED AND CLOSED** as `NO_STATISTICAL_EDGE`.

Forbidden rescues include:
- inverting the observed interaction sign;
- changing HIGH/LOW definition or trailing window;
- moving 07:30/08:00/08:01/08:31 timestamps;
- changing costs;
- selecting only 2022, 2023, 2024, or favorable months;
- adding OI, gamma, volatility, trend, funding, sentiment, or price filters to this MVE after seeing outcomes;
- opening 2025 or 2026 to attempt rescue.

Any future options-expiry research must be a materially different mechanism and a new prospectively frozen MVE.

## Integrity hashes

- `DISCOVERY_DAILY_ROWS.csv`: `fec05be244218e3c46668d272d321c6e8551a8f7397a1e8351c564eeffee9ac1`
- `DISCOVERY_TRADES.csv`: `6de344f9a22932e67c250282c0cb657a7d86e797a4bedd371bd79a70dc40c029`

## Governance

- research-only;
- no live trading;
- no exchange mutation;
- no 2025 access;
- no 2026 access;
- no merge to main;
- no deployment;
- no post-outcome tuning.

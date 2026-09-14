# ETF-SHORTFLOW-001 — DISCOVERY CLOSEOUT — 2026-09-14

STATUS: **COMPLETE / DISCOVERY_FAIL_NO_PROMOTION**

LAB: `ETF-SHORTFLOW-001`
MVE: `ESF-IBIT-SHORTVOL-5D-001`

## Canonical execution

- GitHub Actions run: `34869565123`
- GitHub artifact: `10357789977`
- Artifact ZIP SHA256: `3561e5d8c12dcf64596eacd4c383bef11255833db7c305997c01b6af2fd57048`
- Drive evidence ZIP ID: `1jEXCVmAlr9pxqSxgwVRQLZjVxGSReXnJ`
- Drive human closeout ID: `1fykqPUni9lDwZASlRfxUJhf3Jfs9UnR0RVs_SGa5MIo`

## Pre-outcome integrity

The regenerated FINRA Source/Data Gate passed before BTC market access:
- 245/245 expected FINRA files;
- 245/245 IBIT rows;
- parsed-row SHA256 exactly matched parent gate: `8ad8797f43347038c4f39f3f99d8bd95c6576e412055c6f4fb329ab31a960f13`;
- frozen protocol SHA256 matched exactly: `5adde8f691ac762752547437d225a7ce90ac11ce1c9e34b96ea8d93f5adecb5c`;
- 2025 access=false;
- 2026 access=false.

## Frozen Discovery result

N = 221 evaluable events.

Primary regression, frozen hypothesis beta < 0:
- beta = `+0.04541944082407648`;
- HAC lag-5 SE(beta) = `0.044355125371746254`;
- one-sided p(beta<0) = `0.8470812574283939`.

Companion strategy:
- mean gross = `-24.5899995 bps/event`;
- mean NET10 = `-34.5899995 bps/event`;
- mean NET20 = `-44.5899995 bps/event`;
- NET10 PF = `0.8675581745`;
- NET20 PF = `0.8326996371`;
- NET10 win rate = `46.6063%`.

Quarterly BASE10 aggregate:
- Q1: `+0.5246454779`;
- Q2: `-0.6144264412`;
- Q3: `-0.5988947395`;
- Q4: `-0.0757632865`.

Non-negative quarters: 1/4.
Largest positive-month gross contribution share: `0.4815676898` versus frozen ceiling `0.35`.

## Promotion gates

PASS only:
- N >= 180.

FAIL:
- beta < 0;
- one-sided HAC p <= 0.05;
- mean NET10 > 0;
- NET10 PF > 1.00;
- >=3/4 non-negative quarters;
- positive-month concentration <= 0.35.

## Final decision

`DISCOVERY_FAIL_NO_PROMOTION`.

The coefficient is opposite the frozen expected direction and the companion strategy is negative gross and net. This is not a near-miss.

No direction inversion, alternate ETF, baseline change, thresholding, horizon change, cost rescue, favorable-month selection, extra filter, subperiod selection, 2025 validation or other post-outcome rescue is authorized under this MVE ID.

2025 remained unopened. 2026 remained unopened. No live trading, exchange mutation, main merge or deployment occurred.

Any future ETF short-flow hypothesis requires a new materially distinct MVE and new prospective authority.

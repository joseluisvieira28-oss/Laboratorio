# BNB-LAUNCHPOOL-DEMAND-001 — RED TEAM PHASE C PRE-POSITIONING CLOSEOUT V0.1

**Protocol freeze:** `ad84beaf221d02ada107c039764ef99c4869e9a4`  
**Role:** POST-HOC DIAGNOSTIC ONLY / ZERO PROMOTION CREDIT  
**Status:** EXECUTED ON ALREADY-OPEN CANONICAL HISTORICAL RAW

Phase C exists because the pre-frozen Phase B time-shift attack discovered that the 24h immediately before the canonical entry clock were stronger than the 24h after it. This follow-up may explain fragility; it cannot promote, rescue or change the candidate.

## C01 — Paired pre vs post

Common complete cohort: 65/66 events.

- T−24h→T0 BASE20 mean: **+221.024 bps**, PF **7.934**
- T0→T+24h BASE20 mean: **+73.409 bps**, PF **1.607**
- mean paired difference POST − PRE: **−147.615 bps**
- post > pre: **25/65**
- 10,000 paired sign-flip permutations, seed 20260927: two-sided empirical fraction **0.0083**

The pre-event move is materially stronger than the post-event move on the same events.

This is evidence of a pre-event state. It is **not proof** of leakage, informed trading or manipulation.

## C02 — Is the pre-event anomaly itself just a few whales?

No.

- remove largest pre-event winner: **+166.760 bps/trade**, PF **6.151**
- remove five largest pre-event winners: **+125.064 bps/trade**, PF **4.621**

The pre-event phenomenon is much less tail-dependent than the original post-event pooled economics.

## C03 — Where is the move?

Gross mechanism decomposition:

| Window | N | Mean | Median | Positive |
|---|---:|---:|---:|---:|
| T−24h→T−12h | 65 | +7.35 bps | −37.53 | 36.9% |
| **T−12h→T0** | **65** | **+232.13 bps** | **+204.71** | **83.1%** |
| T0→T+12h | 66 | +72.69 bps | +40.14 | 56.1% |
| T+12h→T+24h | 66 | +24.80 bps | +18.06 | 54.5% |

The pre-event strength is concentrated overwhelmingly in the **last 12 hours before the public announcement/entry boundary**.

## C04 — Does ordinary pre-event momentum explain the post-event return?

We froze a second placebo before executing it:

- same YYYY-MM;
- same UTC quarter-hour;
- actual date ±1 day excluded;
- complete pre24h and post24h required;
- for each event use its 5 nearest control dates by pre24h return;
- 10,000 random matched portfolios;
- seed 20260927;
- one-active-trade overlap preserved.

Coverage: **65/66 = 98.48%**.

Result:

- actual common-cohort post BASE20 mean: **+73.409 bps**
- matched placebo mean: **−11.981 bps**
- matched placebo median: **−13.496 bps**
- placebo 5th–95th percentile: **[−65.984, +46.027] bps**
- placebo >= actual: **1.05%**
- actual percentile: **98.95%**

So the large pre-event momentum **does not by itself reproduce** the positive post-announcement result.

## Red interpretation

The historical mechanism now looks more complicated than the original one-sentence story.

The data are consistent with a **two-stage event structure**:

`strong pre-event positioning/anticipation → public Launchpool announcement → additional positive post-event BNBBTC response`

But only the measured timing pattern is established. The reason for the pre-event move is unresolved.

Do **not** infer insider information, leakage or manipulation without external evidence.

Do **not** turn T−12h/T−1d into a new trading rule from these outcomes. Any such idea would require a separately named prospective candidate and untouched validation data.

## Current Red state

BNB is **not falsified** by Phase C.

The strongest Red problems remain:

- original post-event economics fail remove-best-5;
- historical temporal instability remains;
- frozen block bootstraps have negative lower bounds;
- RT-006 asset placebo remains unresolved;
- RT-017 exact volatility-matched placebo remains BLOCKED under its frozen availability gate;
- live execution/capacity evidence remains incomplete;
- final Diamond V0.2 prospective first-25 evidence is not yet adjudicated.

Existing V3 Tier-2 / Quase-Diamante status remains historical authority. Diamond status is not granted.

No live trading, capital, orders, exchange mutation, strategy mutation or main merge is authorized.

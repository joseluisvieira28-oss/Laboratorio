# BINANCE-LISTING-FIRST-SECONDS-CASCADE-002
## V0.1 2025 DEVELOPMENT AUTHORITATIVE CLOSEOUT
Date: 2026-10-05
Status: CLOSED — HFT_ONLY_OR_TOO_FAST

### Authority
Parent freeze:
5110f7ebda90809de56155b4605b9621bd8fb781

Identity/pre-history resolution:
9744ce8e12b99e644a0f9bee55b1d89689a9b0dd

Metric implementation spec:
c805e09e4ab879438b8ea98ca025a439cd22b22f

Development activation:
45d82eebe301041bfc39bb51298095d58f8259e6

Label clarification:
12ef98b1f72ca0650a1f6e47e1c579b279c42637

Latency full-sample clarification:
0e6619b9e0fdb7066841f0fbf6c8379899795280

Authoritative one-shot runner commit:
e16e1db9e34821e625ecb4f36edcfbde077caf06

Authoritative GitHub Actions run:
37364051777

A delayed duplicate run was caused by GitHub workflow registration latency after the system initially reported no run object. It is NON-AUTHORITATIVE and is not used for any scientific decision.

### Source sample
Eight source-valid 2025 DEVELOPMENT observations:
COOKIE, 1000CHEEMS/CHEEMS, KMNO, PUMP, AVNT, GIGGLE, F/SynFutures, MET/Meteora.

All eight had frozen exact identity, >=24h Gate Spot pre-history, Gate deals archive coverage, a pre-T0 trade inside the frozen 10-second P0 window, post-T0 trades, and sub-second timestamps.

### Announcement-time effect
Observed cross-event medians:
- R1s: +0.0208% among 5 events with a post trade by 1s; hit 60%
- R5s: +24.3770%; n=8; hit 100%
- R10s: +29.3659%; n=8; hit 100%
- R30s: +9.5712%; n=8; hit 100%
- R60s: +10.1238%; n=8; hit 100%

The R5/R10 medians exceeding R60 indicate substantial early overshoot and partial reversion by 60s.

Median time to reach 50% of the signed R60 displacement:
2.248051 seconds.

Median time to reach 80%:
2.3421815 seconds.

### Activity shock
Among events with positive nonzero baseline medians:
- median 5s trade-count shock: 110.0x
- median 5s quote-volume shock: 221.73x
- median 10s trade-count shock: 100.625x
- median 10s quote-volume shock: 131.916x
- median 60s trade-count shock: 54.042x
- median 60s quote-volume shock: 32.139x

This is descriptive development evidence of an extreme contemporaneous activity burst.

### Frozen latency-grid results
250ms threshold:
- actual median entry latency: 0.566s
- median gross capture to 60s: +10.1080%
- gross hit: 100%
- median net50: +9.5588%
- net50 hit: 100%
- net50 LOO positive: PASS
- net50 positive concentration: 39.3326%
- not eligible for ACTIONABLE gate because latency <1s

500ms threshold:
- actual median entry latency: 0.683s
- median gross: +10.0482%
- gross hit: 100%
- median net50: +9.4993%
- net50 hit: 100%
- net50 concentration: 39.3236%
- not eligible for ACTIONABLE gate because latency <1s

1s threshold:
- actual median entry latency: 1.416s
- median gross: +9.9755%
- gross hit: 87.5%
- gross LOO positive: PASS
- gross concentration: 38.9177% -> FAIL frozen <=35% gate
- median net50: +9.4270%
- net50 hit: 87.5%
- net50 LOO positive: PASS
- net50 concentration: 39.3949% -> FAIL frozen <=35% flag

2s threshold:
- actual median entry latency: 2.170s
- median gross: +9.8884%
- gross hit: 87.5%
- gross LOO positive: PASS
- gross concentration: 38.9958% -> FAIL
- median net50: +9.3403%
- net50 hit: 87.5%
- net50 LOO positive: PASS
- net50 concentration: 39.4754% -> FAIL

5s threshold:
- median gross: -1.0720%
- gross hit: 37.5%
- median net50: -1.5654%
- FAIL

10s threshold:
- median gross: +0.4648%
- gross hit: 50%
- median net50: -0.0363%
- FAIL

30s threshold:
- median gross: +0.7906%
- gross hit: 50%
- median net50: +0.2879%
- FAIL hit/LOO/concentration.

60s threshold:
- valid_n = 0 by the frozen entry/exit boundary semantics.

### Concentration diagnosis
At the 1s threshold, GIGGLE is the largest positive contributor:
- gross capture to 60s: +71.8529%
- net50: +70.9958%

Other 1s net50 outcomes include:
- 1000CHEEMS +45.5331%
- COOKIE +38.4338%
- KMNO +13.5446%
- F +5.3094%
- MET +4.2433%
- AVNT +2.1556%
- PUMP -0.8302%

No event is removed or downweighted after outcome inspection.

### Frozen development verdict
- actionable_latency_buckets_ms = []
- cost_robust_50bps_buckets_ms = []
- median R60 > 0 and R60 hit >=60%

Therefore, by the pre-outcome label priority:

HFT_ONLY_OR_TOO_FAST

### Interpretation
The first-seconds effect is real and extremely large descriptively in this 2025 development sample, but the frozen >=1s actionable gate does not pass because positive capture remains too concentrated. The useful capture window also collapses sharply by ~5 seconds.

This result is DEVELOPMENT ONLY. It is not a confirmatory trading edge and does not authorize live or micro-live trading.

### 2026 firewall
2026 remains UNOPENED.

Because V0.1 did not produce ACTIONABLE_WINDOW_CANDIDATE under its frozen rule, this family does not earn automatic promotion to a 2026 confirmatory holdout.

Any future work must either:
1. remain descriptive/engineering work without opening 2026 outcomes; or
2. define a genuinely new economic/execution hypothesis under a new pre-outcome freeze, without changing V0.1 gates post hoc to rescue it.

No post-outcome tuning.
No merge to main.
No live trading.
No orders.
No private exchange endpoints.
No account reads.
No wallets.

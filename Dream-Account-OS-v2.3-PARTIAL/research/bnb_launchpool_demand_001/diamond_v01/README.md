# BNB Launchpool Diamond V0.2 — measurement layer

This directory is **measurement-only** and inherits the parent BNB-LAUNCHPOOL-DEMAND-001 rule unchanged.

- Minimum final Diamond sample: 25 complete genuinely prospective events, reusing the already-frozen 2026-09-16 forward floor.
- Public/read-only data only.
- No authenticated API, order, wallet, leverage, exchange mutation, alert, webhook or capital authority.
- The causal layer measures BNBBTC 15m/60m response plus BNBUSDT same-clock volume shock.
- A causal event is unusable for Diamond adjudication if its frozen 20-prior-valid-day baseline cannot be constructed.
- Final survival requires the parent economic/integrity gates **and** the V0.2 causal gates.
- No early survival and no post-outcome rescue.

Global Diamond standard authority: commit `2c23c73bcbf12adbbddb99893f19ec0401055dbc` on branch `diamond-test-v1-prospective-validation-2026-09-24`.

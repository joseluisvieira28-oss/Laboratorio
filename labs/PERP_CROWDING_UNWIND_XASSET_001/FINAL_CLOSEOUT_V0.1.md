# PERP-CROWDING-UNWIND-XASSET-001 — FINAL CROSS-ASSET CLOSEOUT V0.1

Date: 2026-09-19
Canonical run: `35474040531`
Canonical head: `74fc843025435619cad891319fc283c09550b64a`

## Frozen battery

Independent exact-rule replications of the BTC/ETH PCU mechanism on:
- SOLUSDT
- BNBUSDT

Period: 2022-01-01 through 2024-12-31

No threshold, horizon, cost, sign, rolling-history or overlap rule was changed from the frozen parent mechanism. BTC and ETH verdicts were not rewritten.

## SOLUSDT

Verdict: **DISCOVERY_FAIL_NO_PROMOTION**

- N = 141
- mean net10 = +0.7588%
- median net10 = +0.3764%
- hit rate = 56.74%
- PF net10 = 1.3710
- bootstrap 95% CI = [-0.2098%, +1.7609%]
- mean net20 = +0.6588%
- PF net20 = 1.3155
- positive years = 2 / 3
- max losing streak = 7
- 2022 = +1.5985%
- 2023 = +1.0442%
- 2024 = -0.8566%

Failed frozen gates:
- bootstrap lower bound > 0
- all 3 years positive

## BNBUSDT

Verdict: **DISCOVERY_FAIL_NO_PROMOTION**

- N = 119
- mean net10 = +0.5885%
- median net10 = +0.4745%
- hit rate = 57.98%
- PF net10 = 1.5250
- bootstrap 95% CI = [-0.1755%, +1.3445%]
- mean net20 = +0.4885%
- PF net20 = 1.4197
- positive years = 2 / 3
- max losing streak = 5
- 2022 = +1.0280%
- 2023 = +0.8285%
- 2024 = -0.8766%

Failed frozen gates:
- bootstrap lower bound > 0
- all 3 years positive

## Family conclusion

**XASSET_NO_INDEPENDENT_PASS_CLOSE_FAMILY**

Across the exact frozen PCU rule:
- BTC: positive aggregate point estimate, 3/4 positive years, 2024 negative, bootstrap lower bound below zero.
- ETH: positive aggregate point estimate, only 2022 positive, 2023–2024 slightly negative, bootstrap lower bound below zero.
- SOL: positive aggregate point estimate, 2022–2023 positive, 2024 negative, bootstrap lower bound below zero.
- BNB: positive aggregate point estimate, 2022–2023 positive, 2024 negative, bootstrap lower bound below zero.

This repeated positive-average / 2024-break pattern is scientifically interesting but does not satisfy the frozen promotion standard. Per the pre-frozen family stop rule, the exact same-rule PCU family is now closed from further asset hopping.

No 2025/2026 data, post-outcome tuning, live trading, exchange mutation, wallet access, or merge to main occurred.

# PERP-CROWDING-UNWIND-ETH-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-19
Canonical run: `35472449366`
Canonical head: `359e76af629cf5e5dc97cef3dd9ec2f575ad830d`

## Source coverage

**PCU_ETH_COVERAGE_FULL**
- 36 / 36 full months
- 2022: 12 / 12
- 2023: 12 / 12
- 2024: 12 / 12

The original 2021 start was source-blocked before any ETH outcome was opened. V0.1A prospectively re-froze the test to the continuous 2022–2024 source era without changing the economic rule.

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Results:
- N = 129
- long N = 26
- short N = 103
- mean net10 = +0.3530%
- median net10 = +0.0664%
- hit rate = 51.94%
- PF net10 = 1.2978
- bootstrap 95% CI mean net10 = [-0.2071%, +0.9529%]
- mean net20 = +0.2530%
- PF net20 = 1.2049
- max losing streak = 9

Year means net10:
- 2022: +1.2583%
- 2023: -0.0990%
- 2024: -0.1010%

Passed frozen gates:
- N >= 60
- mean net10 > 0
- PF net10 >= 1.10
- mean net20 > 0
- PF net20 > 1

Failed frozen gates:
- bootstrap 95% lower bound > 0
- >=3 positive years

## Interpretation

ETH independently reproduces the same broad shape seen in BTC — positive point estimates and PF > 1 after 10/20 bps cost stress — but it does not provide robust statistical/year stability. Under the frozen rules it is not promotable.

This does not rescue or rewrite the BTC result. It does justify a prospectively frozen cross-asset replication battery using unchanged rules on additional assets, with family-level adjudication fixed before opening those outcomes.

No 2025/2026 data, live trading, wallet access, exchange mutation or merge to main was opened.

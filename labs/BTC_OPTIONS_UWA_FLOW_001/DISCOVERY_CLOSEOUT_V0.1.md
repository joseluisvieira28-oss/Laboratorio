# BTC-OPTIONS-UWA-FLOW-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-19
MVE: `UWA-SIGNED-OPTION-FLOW-24H-001`
Source: browser-recovered canonical `Deribit_w_IV.csv`
Source SHA256: `47af56f73630b54a025b554088c03771404af15bbe9091dddee7d1c644c903b2`

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Only the prospectively frozen Discovery period 2017-01-01 through 2018-12-31 was opened. The locked 2019 replication and 2020 period were not opened.

Results:
- N = 89 non-overlapping 24h events
- mean net10 return = +0.2597%
- median net10 return = +0.2287%
- hit rate = 51.69%
- profit factor net10 = 1.1590
- bootstrap 95% CI for mean = [-0.6083%, +1.1570%]
- mean net20 return = +0.1597%
- profit factor net20 = 1.0950
- 2017 mean net10 = +1.3807%
- 2018 mean net10 = -0.0050%
- positive Discovery years = 1 / 2
- max losing streak = 5

Passed:
- N >= 60
- mean net10 > 0
- PF net10 >= 1.10
- mean net20 > 0
- PF net20 > 1

Failed:
- bootstrap lower bound > 0
- both Discovery years positive

## Interpretation

There is a weak positive directional-flow hint in this exact MVE, but the uncertainty interval crosses zero and the year stability gate fails. Under the frozen rules this is not enough to open the 2019 replication.

This does not invalidate the UWA source or the broader options-information family. It closes only this exact 4h premium-weighted continuation implementation.

No post-outcome threshold change, sign inversion, IV/DTE/strike filter, 2019 rescue, 2020 rescue, live trading, exchange mutation, wallet access or merge to main is authorized.

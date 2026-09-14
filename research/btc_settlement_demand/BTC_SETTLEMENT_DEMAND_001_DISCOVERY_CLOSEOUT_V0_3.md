BTC-SETTLEMENT-DEMAND-001 — DISCOVERY CLOSEOUT V0.3

FAMILY_ID: BTC-SETTLEMENT-DEMAND-001
MVE_ID: BSD-WOW7D-1D-001
DATE_CLOSED: 2026-09-14
SCIENTIFIC_STATUS: DISCOVERY_FAIL_NO_PROMOTION

FROZEN HYPOTHESIS
Bitcoin confirmed-transaction settlement demand was measured as the sign of the week-over-week acceleration in 7-day mean confirmed transaction counts: RECENT7 / PRIOR7 - 1. Positive acceleration => LONG BTC; negative acceleration => SHORT BTC. A full one-calendar-day publication buffer was required. Entry was BTCUSDT daily open at t+2; exit was daily open at t+3; hold exactly one UTC day. Discovery entries were restricted to 2018-01-01 through 2024-12-30. NET10 was the primary cost case.

AUTHORITY AND SOURCE LINEAGE
Discovery Authority Drive ID: 1uE1QmcrIWUG-aV0kkFg1qXllQoQ5OJcX
Authority SHA256: 18a45507ac36e15a5824043b46e7a4f43e377cc2775e54893e88b26395b12c7e
Authority Git blob: 821e7d2eff241796aa948f8b90bea4b2fd0e7b1b
Source Gate: BSD-TXCOUNT-002 / run 34864390599 / artifact 10355248843
Source raw SHA256: e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f
Source manifest SHA256: 108525b5d3c3f331f8aef4dbcfcec05c8ab0221ba7c8cbc179d8c944c239b9cd

PREOUTCOME TECHNICAL ATTEMPT
Run 34865461388 stopped before market outcomes because GITHUB_TOKEN received HTTP401 while downloading a prior-run artifact. Classification: TECHNICAL_FAILURE_PREOUTCOME. Discovery was skipped. price_values_opened=false; returns_computed=false; pnl_computed=false; access_2025=false; access_2026=false. Artifact 10355744621, SHA256 e0b976651eca027db73cb1d5482a3bc3a6c240c3cec1e56b73d2c96dc12b9a75. Drive archive: 1DB06qDCWiIDug0QvcoKukl5jCCAmR_-c.

PREOUTCOME REMEDIATION
Only source-binding transport was remediated under BSD-SOURCE-BIND-REM-001. All scientific rules remained unchanged. Technical remediation authority Drive ID: 1P3QiWrtWQuky7POsWUYieZzfIdMR7IFG. The exact frozen Blockchain.com source call was reacquired and was required to match raw SHA256 e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f before market outcomes. Canonical preoutcome rebinding passed.

CANONICAL DISCOVERY RUN
GitHub Actions run: 34865803217
Job: 104049234651
Artifact: 10356746983
Artifact ZIP SHA256: 5069961ea427481d9e0bb7cc498e1ee3f9b03db1edc962bf4fa9cbaa8cdf3635
Drive evidence ZIP: 1yTwTqz8KGx4BvaSKp26Qll1NbQXOd7p5
Human-readable closeout Drive ID: 1pCx-FHOcUEiFaItdJJQpEznZsFx_nJvz

RESULTS
N: 2556
Long: 1289
Short: 1267
Mean gross: +2.8237818087990263 bps/trade
Median gross: +1.5578066229138265 bps/trade
Mean NET6: -3.1762181912009737 bps/trade
Mean NET10: -7.176218191200974 bps/trade
Mean NET20: -17.176218191200974 bps/trade
NET10 profit factor: 0.9420192647025645
NET10 win rate: 48.47417840375587%
Bootstrap p(mean NET10 <= 0): 0.8451
Bootstrap 95% CI mean NET10: [-21.042336034923736, +6.892764851116238] bps
Non-negative NET10 years 2018-2024: 3/7
Non-negative NET10 years 2021-2024: 2/4
Maximum positive-year gross contribution share: 31.99871774242353%
Compounded NET10 diagnostic: -97.01637226461634%
Maximum drawdown NET10 diagnostic: -98.66763776763569%

CALENDAR-YEAR MEAN NET10 BPS
2018: +3.625330070233082
2019: -0.5495331400012221
2020: -26.1055114442908
2021: -17.46051181936101
2022: -18.586921766364313
2023: +2.265339038357964
2024: +6.630142800425207

PROMOTION GATES
PASS: N >= 1000
FAIL: mean NET10 > 0
FAIL: NET10 PF > 1
PASS: median gross > 0
FAIL: >=5/7 calendar years non-negative at NET10
FAIL: >=3/4 years 2021-2024 non-negative at NET10
FAIL: bootstrap p(mean NET10 <= 0) <= 0.20
PASS: positive-year gross concentration <=70%
PASS: source binding / timing firewall / protected-period firewall

VERDICT
DISCOVERY_FAIL_NO_PROMOTION. This is not a near-miss. Gross expectancy was slightly positive but insufficient to survive the prospectively frozen 10 bps primary cost, and the evidence was statistically weak and unstable across years. The exact MVE BSD-WOW7D-1D-001 is CLOSED.

NO RESCUE
Do not invert the signal, add thresholds, change 7/7 windows, remove the publication buffer, switch to long-only, alter hold/cost, remove years, add fee/volume/price/regime filters, change market source, or select favorable subperiods under this MVE ID. Any materially different settlement-demand mechanism requires a NEW MVE ID and a NEW prospective authority before outcomes.

GOVERNANCE
2025 remained unopened in the canonical Discovery. 2026 remained unopened. No live trading, exchange mutation, merge to main or Render deployment occurred or is authorized by this closeout.

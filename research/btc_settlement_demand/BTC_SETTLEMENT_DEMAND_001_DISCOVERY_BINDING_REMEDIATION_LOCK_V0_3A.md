BTC-SETTLEMENT-DEMAND-001 — DISCOVERY BINDING REMEDIATION LOCK V0.3A

FAMILY_ID: BTC-SETTLEMENT-DEMAND-001
MVE_ID: BSD-WOW7D-1D-001
BINDING_ROUTE_ID: BSD-SOURCE-BIND-REM-001
DATE_LOCKED: 2026-09-14
STATUS: PRE-OUTCOME TECHNICAL REMEDIATION FROZEN / READY FOR ONE RETRY

Original Discovery authority remains unchanged:
- Authority SHA256: 18a45507ac36e15a5824043b46e7a4f43e377cc2775e54893e88b26395b12c7e
- Authority Drive ID: 1uE1QmcrIWUG-aV0kkFg1qXllQoQ5OJcX
- Authority Git blob: 821e7d2eff241796aa948f8b90bea4b2fd0e7b1b

Failed preoutcome run:
- Run 34865461388
- Classification: TECHNICAL_FAILURE_PREOUTCOME
- Market outcomes: NOT OPENED
- Failed artifact 10355744621 / SHA256 e0b976651eca027db73cb1d5482a3bc3a6c240c3cec1e56b73d2c96dc12b9a75

Technical remediation authority:
- Drive ID: 1P3QiWrtWQuky7POsWUYieZzfIdMR7IFG
- SHA256: e92920abd21f8e6969ac55e89e63b2c4785db3111a9aeabd7a2931218e5727e8
- Remediation wrapper Git blob: ffd1f8f1cddd77b5c929352a8bc61282c3a207f5
- Embedded canonical manifest SHA256: 108525b5d3c3f331f8aef4dbcfcec05c8ab0221ba7c8cbc179d8c944c239b9cd
- Canonical raw source required SHA256: e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f
- Workflow preparation commit before this lock: 9c05da82433b1e0ee7c37bf8eb1beee6f015e344

Scientific rules are unchanged: signal, direction, 7/7 windows, one-day publication buffer, one-day hold, Binance BTCUSDT 1d source, 2018-2024 Discovery window, 6/10/20 bps costs and every promotion gate remain exactly as frozen in V0.3.

The next commit is authorized to add ONLY:
.github/btc-settlement-demand-discovery-v03-bindfix.trigger

2025 and 2026 remain locked. No live trading, exchange mutation, merge to main, Render deployment or post-outcome tuning.

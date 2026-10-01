# CRYPTO-INDEX-REBALANCE-CONTINUATION-002 — HOLDOUT IMPLEMENTATION RECEIPT V0.1

Date: 2026-10-01
Status: FROZEN_IMPLEMENTATION_BEFORE_OUTCOME

Authority:
- protocol commit: b7c976451ad5659147728832e353c3379e61692a
- holdout freeze commit: 2cba5abfacc01f4ddd0c41d8459f90b7cd83b86f
- route identity: a5411273d65be311d40fea168f3b616375cb41f23cf4322f353abffdef7216f0

Runner:
- path: research/crypto_index_rebalance_continuation_002/run_holdout_v01.py
- Git blob SHA: 91363a8afccea70adb31a1ba26dfc90eb994ac13
- creation commit: 910a8aaad7faebe1b9ac7af40eedbeefd8e8b307

Implementation mapping:
- only route rows with primary_confirmatory_eligible=true
- exact 32-leg assertion before market fetch
- entry = implementation date 06:00:00Z
- exit = source-frozen implementation timestamp
- exact 1m OPEN, no nearest fill
- ADD sign +1; REMOVE sign -1
- equal-notional token-vs-BTC relative log return
- costs: 20 fee-floor / 30 BASE / 50 STRESS bps
- primary statistical unit = change month
- 10,000 bootstrap reps; seed 20261001
- classification logic implements the frozen A-K gates
- 2026-09 cannot enter the primary holdout

No market price had been fetched by this child when this receipt was created.
No live trading / orders / mutation.
Trading authority: NONE.

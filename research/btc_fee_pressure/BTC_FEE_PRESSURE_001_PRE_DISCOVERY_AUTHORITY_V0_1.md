# BTC-FEE-PRESSURE-001 — PRE-DISCOVERY AUTHORITY V0.1

Status: FROZEN PRE-OUTCOME / SOURCE-DATA GATE ONLY  
Drive authority ID: 1U02j24GmixrBTu26vNxoC9nUje7qKmQXH_floOFpeqo  
Branch: btc-fee-pressure-v0.1

## Anti-duplication
Drive and GitHub searches found no canonical Bitcoin transaction-fee pressure or mempool-congestion lab. Verdict: NOT DUPLICATE.

## Frozen MVE
- Family: BTC-FEE-PRESSURE-001
- MVE: BFP-TOTALFEES-7D-001
- Variable: daily total BTC transaction fees paid to miners, excluding coinbase rewards
- Hypothesis: unusually high block-space fee pressure precedes positive BTC return
- Trigger: value strictly above trailing 90-observation 80th percentile, excluding day t
- Direction: LONG BTC
- Entry: next UTC daily open
- Hold: 7 calendar days; no overlap
- Costs: 10 bps base, 20 bps stress

## Frozen source
Blockchain.com Charts API, GET /charts/transaction-fees, annual bounded requests for 2021-01-01 through 2024-12-31 UTC, rollingAverage=1day, format=json, sampled=false. Only fee-series fields may be inspected. USD charts, stats, exchange APIs and all market-price sources are prohibited.

Minimum 1,400 clean observations across 2021–2024. Enumerate missing, duplicates, malformed and out-of-window rows; no fill.

Only Source/Data Gate is authorized. Discovery, prices, returns, PnL, 2025, 2026, live trading and exchange mutation remain prohibited.

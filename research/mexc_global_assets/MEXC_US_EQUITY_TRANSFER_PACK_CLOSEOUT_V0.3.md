# MEXC U.S. EQUITY TRANSFER PACK — CLOSEOUT V0.3

Date: 2026-10-04
Run: 37230242026

Frozen rule for all assets:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS

## META — PASS
- alpha=0.003125
- N=523
- wins=345
- win rate=65.9656%
- mean gross=+3.424088 bps
- median=+3.200299 bps
- thirds=+2.452923 / +4.476458 / +3.343347
- p=1.2330e-13

## AMZN — PASS
- alpha=0.0015625
- N=300
- wins=209
- win rate=69.6667%
- mean gross=+3.791634 bps
- median=+3.161993 bps
- thirds=+2.616928 / +5.053534 / +3.704439
- p=3.8579e-12

## MSFT — FAIL
- alpha=0.00078125
- N=97
- wins=48
- win rate=49.4845%
- mean gross=+0.531801 bps
- median=-0.200325 bps
- thirds=+0.896302 / +0.404895 / +0.301406
- p=0.580393

Artifact SHA256:
`8eddb8a3662faaffeac11fc2c925e8745156871bf50680eff27d60718490fafd`

## Family-level interpretation

Exact 5/3/1m FOLLOW evidence:
- NVIDIA: discovery survivor under 64-cell Holm
- TESLA: transfer PASS
- APPLE: transfer PASS
- PLTR: transfer PASS
- META: transfer PASS
- AMZN: transfer PASS
- MSFT: transfer FAIL

The mechanism generalizes across multiple MEXC stock-futures contracts but the replicated gross effect is typically only a few bps.

Current practical classification:
`MULTI_ASSET_REPLICATED_SIGNAL__STANDARD_API_EXECUTION_FEE_BLOCKED`

Further cloning of the same low-threshold cell to more equities is scientifically lower priority.

Next economically distinct hypothesis should target only sufficiently large external shocks / lag gaps on untouched assets, with thresholds frozen from the known execution-cost requirement rather than chosen from outcomes.

No tuning, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.

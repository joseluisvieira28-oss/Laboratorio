# DEFI-LIQUIDATION-SHOCK-001 — SOLANAFM RENDER SOURCE PROBE V0.2

Date: 2026-09-22
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

Purpose:
Re-test the already-frozen SolanaFM time-bounded indexed route from the canonical Render Frankfurt runtime after the GitHub-hosted probe returned HTTP 502 for all four frozen protocol program addresses.

Frozen window:
2024-12-15T00:00:00Z through 2024-12-15T23:59:59Z.

Frozen program addresses:
- Kamino Lend: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
- marginfi v2: MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA
- Drift v2: dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH
- Save/Solend: So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo

Endpoint family:
GET https://api.solana.fm/v0/accounts/{program}/transactions

Query:
utcFrom=1734220800
utcTo=1734307199
limit=5
page=1

PASS means only that the time-bounded indexed route is technically accessible and parseable from Render. It does NOT establish census completeness, liquidation discriminator correctness, first-success boundary, SOURCE_DATA_PASS, predictive edge, returns or PnL.

Firewalls:
prices=false
returns=false
pnl=false
direction=false
market_response=false
source_data_pass=false
first_success_boundary=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
main_merge=false

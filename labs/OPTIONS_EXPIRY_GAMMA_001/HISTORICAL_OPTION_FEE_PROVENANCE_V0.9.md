# OPTIONS-EXPIRY-GAMMA-001 — HISTORICAL OPTION FEE PROVENANCE V0.9

Date: 2026-09-19
Status: PRE-EXECUTION PROVENANCE / NO PNL AUTHORITY

## HISTORICAL BASE FEE

Deribit announced that effective 2020-08-24 it reduced BTC and ETH option trading fees from 0.04% to 0.03% of underlying per option contract:
https://insights.deribit.com/exchange-updates/deribit-lowers-option-trading-fees-to-make-the-market-more-accessible-to-retail-traders/

Independent research using Deribit market data from 2021-04 through 2022-04 also records BTC option trading fees as 0.03% of underlying / 0.0003 BTC per option contract, capped at 12.5% of option value:
https://doi.org/10.3390/risks11050085

Therefore the frozen execution research model uses 0.03% per option trade side as the historical standard-account base fee for 2021-2024, with the 12.5%-of-premium cap applied per trade. It does not assume any VIP discount, maker rebate, combo discount or affiliate discount.

## CURRENT DOCUMENTATION CHECK

Current Deribit documentation remains relevant for fee mechanics/cap semantics but is not used to overwrite historical rates:
https://support.deribit.com/hc/en-us/articles/25944746248989-Fees

## LIMIT

This provenance note does not open any option premium, execution PnL or BTC outcome. The execution MVE remains NOT AUTHORIZED until its frozen parent gates pass.

No live trading, orders, wallet access, exchange mutation, 2025/2026 access or merge to main.

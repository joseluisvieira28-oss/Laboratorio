# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — PRIMARY POPULATION READINESS FREEZE V0.1

Date: 2026-09-28
Status: SOURCE-ONLY / ECONOMIC FREEZE ALREADY LOCKED

Purpose:
Before any protected market outcomes are opened, count the exact 2025 predictor population implied by the already frozen Economic Discovery V0.1.

Allowed:
Compound BuyCollateral logs, Ethereum block numbers/timestamps, event asset and baseAmount.

Forbidden:
market prices, returns, funding, basis, volatility, PnL, Binance kline values.

Primary addresses and proxy mappings are copied verbatim from the economic freeze.

Readiness outputs:
- eligible raw BuyCollateral event count;
- proxy/block cluster count;
- unique ISO weeks containing eligible clusters;
- clusters by proxy;
- events by proxy;
- FLOW_USDC distribution summaries using source event baseAmount only.

Readiness PASS requires:
- >=100 proxy/block clusters;
- >=12 ISO weeks.

Readiness does not establish edge.

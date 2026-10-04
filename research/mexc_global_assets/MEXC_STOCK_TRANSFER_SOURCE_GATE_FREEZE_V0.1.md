# MEXC STOCK TRANSFER OPERATIONAL FAMILY — SOURCE GATE V0.1

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME

Objective:
Identify a fixed set of MEXC stock-futures pairs for which the exact NVIDIA/TESLA 1-minute lead-lag mechanism can be tested without changing its parameters, with an explicit execution-aware economic gate.

Candidate universe is frozen before outcomes and comes from previously announced MEXC stock-futures families, excluding NVIDIA and TESLA from later outcome testing because their outcomes are already open.

Candidates:
INTC, HOOD, META, GE, BABA, RDDT, SNOW, COP, CVNA, MCD, CSCO, LLY, ONDS, AMD, TSM, JPM, CVXSTOCK, ACN, QCOM, CRWD, BAC, MELI, MRVL.

Source verification date:
2026-09-30

Source verification window:
14:30–19:00 UTC

A source PASS requires:
- MEXC target contract exists;
- MEXC 1m history transport works for the window;
- Binance official 1m Futures Vision archive works;
- Bitget public 1m futures history works.

No returns, shocks, gaps, signals, directions, wins, losses or PnL are computed at this stage.
The verification date is burned from later outcomes.

No private endpoints, account reads, orders, wallets, exchange mutation or live trading.

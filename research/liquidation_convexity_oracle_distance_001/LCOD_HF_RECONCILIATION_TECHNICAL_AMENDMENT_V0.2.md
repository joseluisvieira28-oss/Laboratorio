# LCOD HF RECONCILIATION TECHNICAL AMENDMENT V0.2

Date: 2026-09-24
Stage: SOURCE CALIBRATION ONLY
Market/liquidation outcomes: CLOSED

## Reason

V0.1 reconstructed component health from item balanceUsd values.
The 47-position source calibration passed the sample gate but showed one 1.3178% relative-error outlier on a position with only 0.0025 USD displayed debt.

Aave documentation explicitly warns that aggregate USD figures are rounded to four decimals and should not be compared against dust, recommending per-item principal and interest for precision.

V0.2 corrects source precision only:
- supply USD = item.balance (main units) * reserve.priceUsd;
- debt USD = (item.principal + item.interest) * reserve.priceUsd;
- collateral capacity applies reserve.collateralFactorPct only to isCollateral=true supply legs.

## Unchanged

- borrower sampling route;
- >=25 complete debt-bearing position gate;
- no market prices beyond Aave's own reserve valuation source;
- no liquidation outcomes;
- no BTC/ETH/crypto returns;
- no PnL;
- no shock-grid changes;
- no edge/promotion gate.

V0.1 remains immutable evidence. V0.2 is a source-precision remediation, not a rescue of an economic result.

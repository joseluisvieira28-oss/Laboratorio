# AAVE-RISK-PARAMETER-SHOCK-001 — DISCOVERY SQD CONTINUATION REMEDIATION V0.1A

Date: 2026-09-18
Status: FROZEN BEFORE ANY DISCOVERY LIQUIDATION OUTCOME ACQUISITION
MVE: ARPS-LT-DOWN-LIQCOUNT-H24-001

## Trigger

Static audit before Discovery execution identified the same SQD continuation defect already proven in the primary mechanism census V0.1:

The prepared Discovery acquire_liquidations() advances cursor directly to request_to + 1 after each response.

SQD stream responses can terminate at an internal continuation block before the requested toBlock. Advancing to request_to would skip unreturned portions of the frozen envelope.

No LiquidationCall outcome has been acquired by this Discovery runner.

## Exact remediation

Change transport continuation only:

- track the last returned block header in each SQD response;
- require returned block monotonicity and exact request-range integrity;
- when one or more rows are returned, continue from last_returned_block + 1;
- only when a healthy response returns zero rows may the exact requested window be treated as covered and cursor advance to request_to + 1.

Unchanged:
- MVE ID ARPS-LT-DOWN-LIQCOUNT-H24-001;
- exact mechanism episodes from the primary mechanism census;
- clean-episode treatment timing;
- PRE24h / POST24h windows;
- affected-asset union;
- canonical Aave Pool;
- LiquidationCall event signature;
- expected canonical LiquidationCall population 5,539;
- sample gates;
- mean/median/randomization/bootstrap rules;
- all PASS gates;
- 2025/2026 firewall.

## Activation

The contingent FINAL PRE-DISCOVERY PROTOCOL remains authoritative:

Discovery executes only if the exact primary mechanism census returns MECHANISM_CENSUS_PASS.

If the mechanism census is insufficient or fails provenance/technical gates, this remediated runner remains unused.

## Firewall

No market prices.
No market returns.
No PnL/PF/win-rate/drawdown.
No 2025/2026.
No live trading/orders/wallets/exchange mutation/main merge.

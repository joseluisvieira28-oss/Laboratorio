# AAVE-LIQUIDATION-OVERHANG-001 — D0 GLOBAL MAPPING BOUNDARY AMENDMENT V0.1.1

Date: 2026-09-18
Branch: `aave-liquidation-overhang-discovery-v0.1`
Status: **FROZEN BEFORE CORRECTED D0 GLOBAL RERUN / OUTCOME-BLIND**

## Trigger

D0 Global V0.1 run `35393867040` terminated as
`D0_GLOBAL_TECHNICAL_FAILURE` before any snapshot map, eMode state, predictor,
LiquidationCall outcome, market return or PnL was materialized.

The V0.1 mapper incorrectly applied the final 2023 scientific timestamp ceiling
to the **upper block-header bracket** used only by binary search.

A valid first-block-at-or-after mapping for 2023-12-31T00:00:00Z requires an
upper block whose timestamp is after the target. The upper bracket is not a
scientific snapshot and no event/log/state value from that bracket is used.

## Exact correction

V0.1.1 changes only snapshot-map bracketing:

- fixed upper bracket: block `19,007,945`;
- the mapper may read only `eth_getBlockByNumber` header metadata for bracketing
  up to `2024-01-02T00:00:00Z`;
- no 2024 log, contract call, reserve state, oracle price, liquidation event,
  market value or outcome may be requested under this amendment;
- every final mapped D0 snapshot must still have timestamp <=
  `2023-12-31T23:59:59Z`;
- exact final population remains 334 dates, 2023-02-01 through 2023-12-31;
- independent provider hash/timestamp verification remains mandatory.

Everything after snapshot mapping remains byte/semantics-identical to D0 Global V0.1.

## Firewalls unchanged

No LiquidationCall outcome values.
No 2024 scientific state/outcomes.
No 2025/2026 access.
No market returns.
No PnL.
No live trading/orders/wallets/exchange mutation.
No main merge.

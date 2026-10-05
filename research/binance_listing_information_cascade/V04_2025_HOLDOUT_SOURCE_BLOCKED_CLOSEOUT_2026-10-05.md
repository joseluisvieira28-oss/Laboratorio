# V0.4 — 2025 HOLDOUT SOURCE-BLOCKED CLOSEOUT
Date: 2026-10-05
Status: AUTHORITATIVE CLOSEOUT

## Upstream scientific state
V0.3 clean 2022-2023 discovery remains authoritative:
SURVIVES_INFORMATION_DISCOVERY.

V0.4 2025 holdout was preregistered before any 2025 market-outcome inspection.
The holdout itself was never opened.

## Source-gate state
The outcome-blind 2025 census produced 12 candidate observations after frozen mechanical exclusions and identity checks.

Eleven observations were fully source-metric usable under the frozen KuCoin -> Bitget hierarchy.

SYRUP was the only unresolved observation:
- KuCoin: required price coverage present, but the frozen baseline-volume median was zero.
- Bitget: required historical coverage absent.
- V0.4.1 froze Gate as the THIRD AND FINAL venue before any 2025 outcome.
- Gate public REST historical candlesticks were operationally inaccessible for the required May-2025 window because of the current rolling-history restriction.
- V0.4.2 was then frozen before any 2025 outcome to change only the Gate transport from REST to the official Gate Historical Quotation archive.

## V0.4.2 authoritative source-only result
V0.4.2 freeze commit:
f5db2454f0fa14eb451e62239b8ae76b63fddeca

Archive-probe implementation commit:
72e577332829674fdb7ba997e1f67e4dfbc031a6

Pinned diagnostic trigger commit:
bd80bbc6f68218a98c8569e5658266d2cec196b8

GitHub Actions run:
37358562560

The pinned run checked out exactly:
bd80bbc6f68218a98c8569e5658266d2cec196b8

Frozen official Gate target:
https://download.gatedata.org/spot/candlesticks_1m/202505/SYRUP_USDT-202505.csv.gz

Observed source-only transport result:
HTTP 404 Not Found.

No price, return, PnL, MFE, MAE, information-return or delayed-return outcome was inspected.

## Frozen decision rule applied
V0.4.2 explicitly froze:
- if the official Gate archive supplies source-valid SYRUP data, freeze exact 12-asset bindings and open V0.4 once;
- if the archive is unavailable, malformed, identity-incompatible, or cannot satisfy mandatory source metrics, close V0.4 as SOURCE_BLOCKED.

The official frozen archive target is unavailable.

## Authoritative verdict
SOURCE_BLOCKED

This is:
- NOT NO_EDGE.
- NOT NO_EXECUTABLE_EDGE_HOLDOUT.
- NOT SURVIVES_EXECUTION_HOLDOUT.
- NOT an execution-cost failure.
- NOT a scientific rejection of the Binance listing information-cascade hypothesis.

The 2025 execution holdout remains unopened and scientifically uncontaminated.

## Governance
No fourth venue may be added to V0.4.x.
No thresholds, horizons, events, cost assumptions or source-selection rules may be changed to rescue V0.4.
2024 remains quarantined.
2026 remains unopened.
No post-outcome tuning occurred.
Research-only.
No merge to main.
No trading, orders, private endpoints, account reads or wallets.

## What remains valid
V0.3 clean 2022-2023 remains:
SURVIVES_INFORMATION_DISCOVERY.

Any future attempt to obtain executable confirmation must be a new, separately preregistered protocol/family and must not reinterpret this V0.4 closeout.

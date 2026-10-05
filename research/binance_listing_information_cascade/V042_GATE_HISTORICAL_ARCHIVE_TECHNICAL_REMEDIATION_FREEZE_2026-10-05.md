# V0.4.2 — GATE HISTORICAL ARCHIVE TECHNICAL SOURCE-TRANSPORT REMEDIATION FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2025 RETURN/PNL OUTCOME

## Scope
This freeze changes only the transport used to retrieve the already-authorized Gate spot source for SYRUP.

V0.4.1 already froze Gate as the THIRD AND FINAL venue after KuCoin -> Bitget for source usability only.
No 2025 return, PnL, MFE, MAE, information-return or delayed-return outcome has been computed or inspected.

## Technical blocker being remediated
The Gate public REST endpoint /api/v4/spot/candlesticks rejects the required May-2025 1m history because the requested candles are older than the endpoint's current rolling historical limit.

This is a transport/runtime limitation, not a scientific source failure.

## Frozen transport remediation
For Gate spot / SYRUP_USDT only:

OLD TRANSPORT:
- https://api.gateio.ws/api/v4/spot/candlesticks

NEW TRANSPORT:
- Gate official Historical Quotation archive
- biz = spot
- type = candlesticks_1m
- month = 202505
- market = SYRUP_USDT
- canonical path pattern documented by Gate:
  https://download.gatedata.org/(biz)/(type)/(YYYYMM)/(market)-(YYYYMM).csv.gz
- frozen target:
  https://download.gatedata.org/spot/candlesticks_1m/202505/SYRUP_USDT-202505.csv.gz

Official Gate documentation states that spot candlestick historical downloads are available from January 2023 and documents the monthly archive path.
Official Gate historical-format documentation defines SPOT candlesticks as:
timestamp, volume, close, high, low, open.

This transport change does NOT add a venue and does NOT change asset identity.

## Source-only probe outputs permitted before holdout
The V0.4.2 probe may emit ONLY source-coverage / source-metric feasibility counts and booleans:
- bars
- witness
- near
- first5
- hist_minutes
- hist_5m_chunks
- hist_gaps
- baseline_median_volume_positive
- strict_source_ok
- volume_metric_possible

It MUST NOT emit or persist:
- prices
- returns
- PnL
- MFE/MAE
- information-return outcomes
- delayed-entry returns
- cost-adjusted outcomes

## Scientific rules preserved unchanged
- 2025 event universe and T0s: unchanged.
- Frozen venue hierarchy: KuCoin -> Bitget -> Gate.
- Gate remains third and final venue.
- No fourth venue.
- No outcome-dependent venue selection.
- Entry rule: unchanged (first full minute boundary >=60s after T0).
- Primary horizon: unchanged (15 full minutes).
- Cost stress: unchanged (50 bps round-trip primary; frozen sensitivities unchanged).
- Survival gates: unchanged.
- 2024 remains quarantined.
- 2026 remains unopened.
- No post-outcome tuning.

## Decision rule
If the official Gate historical archive supplies source-valid SYRUP data under the existing V0.4 rules:
1. Freeze the exact 12-asset venue bindings before opening outcomes.
2. Execute V0.4 once under the already-frozen holdout protocol.

If the archive is unavailable, malformed, identity-incompatible, or cannot satisfy the mandatory source metrics:
- close V0.4 as SOURCE_BLOCKED.

Research-only.
No merge to main.
No trading, orders, private endpoints, account reads or wallets.

# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.3 SOURCE/METRIC TECHNICAL REMEDIATION SPEC
Date: 2026-10-05
Status: LOCKED TECHNICAL REMEDIATION; SCIENCE UNCHANGED
Parent freeze: 08b83cb2bbf10d3806425c833f648032fcaaee23

## Observed technical defects
1. Historical pagination used end=cur+step and next= end+60s, creating deterministic one-minute holes.
2. For Bitget-bound LDO/PEPE/PENDLE this removed one of the five event-volume minutes.
3. KuCoin-bound STG had a zero median baseline volume, so the mandatory frozen volume-shock metric was not computable there.
4. The pre-outcome source gate had already established STG source coverage on BOTH KuCoin and Bitget.

## Locked remediation rules
- Frozen eligible universe remains exactly:
  IMX, API3, WOO, ASTR, LDO, STG, FLOKI, PEPE, PENDLE, ORDI, BLUR, BONK.
- Frozen venue hierarchy remains KuCoin first, Bitget second.
- A venue is source-usable only if all mandatory Layer-A metrics can be computed:
  strict >=24h witness, near-T0 price data, first five event minutes, non-empty baseline 5m buckets with strictly positive median volume.
- If KuCoin is not source-usable for mandatory metrics, use Bitget ONLY if Bitget passed the pre-outcome source gate for that same asset.
- No return/PnL value may influence fallback.
- Pagination is transport-only correction:
  KuCoin chunks cover [start,start+699m], next=start+700m.
  Bitget chunks cover [start,start+89m], next=start+90m.
  Deduplicate by timestamp.
- Layer A/B definitions, T0s, prices, horizons, thresholds, direction, gates and BTC-relative reporting remain unchanged.
- 2024 remains quarantined; 2025-2026 remain unopened.
- Original V0.3 outputs are retained. Remediated outputs are written separately.
- No main merge, live trading, orders, private endpoints, wallets or account reads.

This remediation is source/transport qualification only and cannot rescue an event by selecting a venue based on its outcome.

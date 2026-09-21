# CED1D-0031 — PROSPECTIVE SHADOW COLLECTOR TRANSPORT REMEDIATION V0.2B — 2026-09-21

**Status:** OUTCOME-BLIND TRANSPORT REMEDIATION BEFORE FIRST SUCCESSFUL REAL SHADOW COLLECTION
**Candidate:** CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
**Parent branch:** `ced-1d-v3-byte-recovery-2026-09-17`
**Remediation branch:** `ced1d-funding-endpoint-transport-fix-v0.2b`

## Incident evidence

- 2026-09-20 run 35490686184: no eligible T+3 day; real collection step skipped.
- 2026-09-21 run 35546300715 first attempt: fail-closed before outcome collection because Binance Vision daily AVAXUSDT 1m file for 2026-09-20 was not yet published (HTTP 404).
- Authorized rerun, job 106455030819: the daily file had become available; collection then fail-closed at the funding transport URL `https://data-api.binance.vision/fapi/v1/fundingRate` (HTTP 404).
- No successful real prospective shadow outcome was produced or inspected before this amendment.

## Exact transport correction

The frozen candidate, signal, costs, funding formula, execution proxy, notional, horizon and thresholds are unchanged.

Only the USD-M public funding REST base host changes:

- invalid transport: `https://data-api.binance.vision/fapi/v1/fundingRate`
- documented USD-M public transport: `https://fapi.binance.com/fapi/v1/fundingRate`

The path `/fapi/v1/fundingRate`, symbol AVAXUSDT, inclusive start/end timestamps, limit, parsed fields, funding bounds and mark-price settlement logic are unchanged.

No authenticated endpoint is introduced.

## Prospective reset — no rescue/backfill

To prevent the failed 21 September collection from being reconstructed after the fact, V0.2B resets the forward evidence start to:

- first admissible signal day: **2026-09-21**
- first admissible signal completion: **2026-09-22T00:00:00Z**
- first admissible reference entry: **2026-09-22T00:01:00Z**
- normal T+3 source-readiness guard remains unchanged.

Signal days 2026-09-18 through 2026-09-20 are not admissible V0.2B forward outcomes. They may only appear as lookback/path inputs where required by the frozen 20-valid-observation calculation.

The 2026-09-21 MICRO-LIVE decision remains **NO-GO** and may never be rescued by this amendment.

## Scientific identity preserved

- symbol: AVAXUSDT
- family: A_MOMENTUM
- lookback: 20 calendar days / exact frozen valid-observation implementation
- direction: CONTINUATION
- horizon: H1 / 1 day
- CED-1D V0.3 hypothesis ZIP and hypotheses.py hashes unchanged
- BASE reference cost: 14 bps
- STRESS reference cost: 20 bps
- research notional: 100 USDT
- aggTrades and bookDepth rules unchanged
- Tier-1 and operational thresholds unchanged

## Governance

research_only = true
public_read_only = true
authenticated_exchange_api = false
orders = false
wallets = false
exchange_mutation = false
live_capital = false
micro_live_rescue = false
retrospective_2026_trade_backfill = false
post_outcome_tuning = false
merge_main = false

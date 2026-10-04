# MEXC GLOBAL ASSET LAB — SOURCE GATE V0.1

Date: 2026-10-04
Branch: `mexc-global-assets-crossvenue-v0.1-source-gate-2026-10-04`
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Mission

Test whether MEXC Global Asset Futures expose defensible public/free market data for:

- NAS100 -> `NAS100_USDT`
- SP500 -> `SPX500_USDT`
- NVIDIA -> `NVIDIA_USDT`
- GOLD(XAU) -> `XAU_USDT`

The first economic target is cross-venue information propagation. No directional or profitability outcome may be opened before a source gate and a pre-outcome freeze.

## Hard boundaries

- no merge to main;
- no live trading;
- no orders;
- no account reads;
- no wallets;
- no private endpoints;
- no exchange mutation;
- no post-outcome parameter tuning;
- raw source bytes and SHA-256 hashes must be preserved for any activation run.

## Official MEXC evidence

MEXC documents Global Asset Futures as derivatives on metals, indices, stocks, commodities and FX.

Current public trading pages identify the target contracts as:

- `NAS100_USDT`
- `SPX500_USDT`
- `NVIDIA_USDT`
- `XAU_USDT`

MEXC Futures market endpoints are documented as public/no-auth. The relevant endpoints are:

- `GET /api/v1/contract/detail`
- `GET /api/v1/contract/index_price/{symbol}`
- `GET /api/v1/contract/kline/{symbol}`
- `GET /api/v1/contract/kline/index_price/{symbol}`

As of 2026-01-19 the active Futures API domain is `https://api.mexc.com`.

## Session caveat

MEXC marketing describes Global Asset Futures as broadly 24/7, but its own FAQ explicitly says specific opening/closing times and holiday schedules vary by asset and that during market close users may only cancel orders or add margin.

Therefore a study MUST infer actual data availability from timestamps/gaps and MUST NOT assume continuous tradability.

## Cross-venue real-time reference audit

### CME

CME public website quotes are officially delayed by at least 10 minutes.

Verdict for short-horizon real-time leader signal:

`CME_PUBLIC_WEB = FAIL_FOR_1M_5M_REALTIME_LEADER`

Reason: using a delayed reference as though it were contemporaneous creates a clock-invalid lead/lag study.

### Yahoo Finance chart endpoint

The unauthenticated `query1.finance.yahoo.com/v8/finance/chart` endpoint is a useful public/free secondary research source and returns timestamped OHLCV for symbols such as `^NDX`, `^GSPC`, `NVDA`, and `GC=F`.

However it is an unofficial interface with vendor-specific delay/retention behavior and no exchange-grade delivery guarantee.

Verdict:

`YAHOO = SECONDARY_SANITY_SOURCE_ONLY`

It cannot by itself activate a primary short-horizon cross-venue trading signal.

## Source-gate verdicts

1. `GLOBAL-ASSET-CROSSVENUE-RT-001`
   - Status: `SOURCE_BLOCKED_PRIMARY_REFERENCE`
   - MEXC leg: documented public source exists.
   - external real-time primary reference: not yet defensibly proven public/free.
   - outcomes: CLOSED.

2. `GLOBAL-ASSET-INDEX-BASIS-001`
   - Status: `PREACTIVATION_DOCS_PASS_RUNTIME_CAPTURE_REQUIRED`
   - contract-price and MEXC index-price legs are both documented public/no-auth sources with timestamps.
   - this is not a claim that the MEXC index equals one named external venue.
   - activation requires a fresh raw runtime capture for all four symbols with zero timestamp/source violations.
   - outcomes: CLOSED.

## Why the index-basis family is allowed to proceed

The economic mechanism is price-convergence, not chart-pattern mining:

`MEXC traded contract price - MEXC external-market-derived index price`

A temporary premium/discount may contain information about:
- local order-flow pressure;
- stale/fast contract repricing;
- index update lag;
- liquidity dislocation around session transitions.

The pre-outcome hypothesis is FADE/convergence only. FOLLOW is not opened as a rescue mode after outcomes.

## Next required action

Run `global_asset_source_probe_v01.py`.

Only if its receipt returns `MEXC_MARKET_SOURCE_PASS` may the frozen `GLOBAL-ASSET-INDEX-BASIS-001` historical runner open the authorized discovery data.

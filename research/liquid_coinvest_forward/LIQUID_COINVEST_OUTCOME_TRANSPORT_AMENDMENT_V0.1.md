# LIQUID CO-INVEST FORWARD — OUTCOME TRANSPORT AMENDMENT V0.1

Date: 2026-10-05
Branch: liquid-coinvest-forward-v0.1-prereg-2026-10-05
Status: ACTIVE / FROZEN BEFORE ANY OUTCOME WAS OPENED

This amendment is subordinate to:
- LIQUID_COINVEST_FORWARD_PREOUTCOME_FREEZE_V0.1.md
- LIQUID_COINVEST_OUTCOME_RESOLUTION_FREEZE_V0.1.md

It changes transport only. It does not change the scientific source, venue, symbols, price clock, horizons, event population, features, or return definitions.

## Triggering incident

GitHub Actions run 37307456467 attempted the first matured +1h outcome resolution from the frozen public Binance USD-M 1m source.

Pre-outcome validation passed:
- 4 durable observation receipts
- 12 observations
- 12 unique IDs
- no outcomes opened by the validator

The outcome resolver then failed before producing an outcome because the GitHub-hosted runner in Azure centralus received HTTP 451 when requesting:
- BTCUSDT
- Binance USD-M /fapi/v1/klines
- exact entry minute 2026-10-05T10:39:00Z

Classification:
TRANSPORT_BLOCKED_TEMPORARY

This is not NO_EDGE and is not scientific evidence.

## Canonical scientific source remains unchanged

Canonical source remains:
Binance USD-M perpetual 1-minute klines.

Canonical underlying API family remains:
/fapi/v1/klines

The official Binance Public Data repository documents that USD-M Futures kline archive files contain data from /fapi/v1/klines.

## Authorized transport routes

### Route A — primary
https://fapi.binance.com/fapi/v1/klines

Use the exact frozen symbol, 1m interval, and exact required minute.

### Route B — official deferred archive fallback
https://data.binance.vision/

Only official Binance Public Data USD-M Futures daily kline archives are allowed.

Frozen archive identity:
data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM-DD}.zip

Requirements:
- the archive date must be strictly earlier than the current UTC date;
- the matching .CHECKSUM file must be fetched;
- SHA256 of the downloaded ZIP must match the official checksum;
- only the exact row whose open time equals the frozen required minute may be used;
- no interpolation, nearest-row substitution, or alternate venue is allowed;
- archive data must preserve the same /fapi/v1/klines semantics.

Binance documents that daily archive data become available the next day. Therefore an outcome blocked by Route A on the current UTC date remains PENDING_ARCHIVE_PUBLICATION rather than being reconstructed from another source.

## Fail-closed rules

If Route A fails and Route B is not yet officially available:
- do not create an outcome receipt;
- classify operationally as PENDING_ARCHIVE_PUBLICATION.

If the ZIP, checksum, checksum verification, archive schema, exact timestamp, or exact row fails:
- do not impute;
- do not switch venues;
- classify SOURCE_BLOCKED for that resolution attempt.

No third-party proxy, exchange mirror, alternate exchange, mark price, close price, nearest candle, or retrospective manual price is authorized.

## Existing science unchanged

Unchanged:
- BTC -> BTCUSDT
- ETH -> ETHUSDT
- SOL -> SOLUSDT
- entry = OPEN of next exact whole UTC minute strictly after observation
- +1h = OPEN at entry + 60 minutes
- +4h = OPEN at entry + 240 minutes
- simple_return_pct = 100 * (exit_open / entry_open - 1)
- append-only outcome receipts
- BASELINE_ONLY / EVENT_ELIGIBLE / DUPLICATE_SOURCE_SNAPSHOT / SOURCE_TIMESTAMP_ONLY / SOURCE_INTEGRITY_CONFLICT semantics
- no threshold fishing
- no live trading or account mutation

This transport amendment was frozen before any outcome receipt existed.

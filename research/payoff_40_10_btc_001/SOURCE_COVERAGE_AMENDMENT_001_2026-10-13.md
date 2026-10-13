# SOURCE COVERAGE AMENDMENT — PAYOFF-40-10-BTC-001 — 2026-10-13

**Only observed failure from run 38353963429:** the original monthly public Binance USD-M markPriceKlines BTC 1h archives verified and loaded, but the merged month series has missing hours beginning 2021-07-01 00:00 UTC. The workflow failed `HOURLY_SOURCE_GAPS_mark` before *any* strategy outcome was opened (no diagnostic.json). All 12 synthetic QA passed.

**Pre-price-outcome technical source coverage amendment**, no filtering by trading results, no strategy or parameter changes:

1. Still obtain and SHA256-check each required official 2020-02..2025-12 monthly klines, monthly markPriceKlines and monthly fundingRate archive.
2. **Only for every missing mark-price 1h timestamp**, identify its UTC date (no selection by outcome). Download its matching official Binance Vision `data/futures/um/daily/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-YYYY-MM-DD.zip` and official `.CHECKSUM`, verify SHA256, parse OHLC.
3. Compare overlapping daily/monthly candles for exact timestamp and OHLC consistency; if any conflict, fail closed. Fill **only previously missing exact UTC hours** from verified daily files. Preserve daily ZIP identities and count. No interpolation, nearest-price joins or invented marks. If daily data missing, fail closed.
4. This correction applies symmetrically to **all missing dates** within original predeclared date range and is not contingent on strategy outcome; do not change taker rates, fee model, signals, 60-day expiry or nominal 4:1 barriers.
5. Preserve 2026 holdout exclusion and zero promotion credit. No orders, accounts, private exchange APIs, network mutation or main merge.

The original run SOURCE_BLOCKED verdict remains historically true; the next run will distinguish SOURCE_OK from remaining source gaps. Report all coverage failures even if inconvenient.

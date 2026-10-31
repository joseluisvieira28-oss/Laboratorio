# BTC10M OKX SPOT x USDT SWAP L2 OFFICIAL PREFIX GATE V0.2 — 2026-10-31
BEFORE any archive file prefix bytes opened in this study. Historical archive metadata collected in prior study GitHub CI #41240149050, original first-party responses read/replayed independently #41240229754; dates/instruments exactly 2024-01-01 and 2025-01-01. Four official static.okx.com URLs listed below are immutable, from SHA-checked official API. This is new microstructure family, NOT the original MEXC L2 model.

FIXED 4 tiny HTTP Range first 524,288 bytes requests, order:
2024 SPOT https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20240101/BTC-USDT-L2orderbook-400lv-2024-01-01.tar.gz
2024 SWAP https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20240101/BTC-USDT-SWAP-L2orderbook-400lv-2024-01-01.tar.gz
2025 SPOT https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20250101/BTC-USDT-L2orderbook-400lv-2025-01-01.tar.gz
2025 SWAP https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20250101/BTC-USDT-SWAP-L2orderbook-400lv-2025-01-01.tar.gz

Each GET Range bytes=0-524287, timeout 18s, no retries, no alternative dates, no redirects off original static.okx.com, cap read bytes to 524288+1 and fail if over. Preserve original partial bytes, byte SHA256, HTTP 206 or HTTP200 (if origin ignored range flag but stop reading at exact cap); only output compression/tar member and NDJSON column shapes, first timestamp type, exchange action field, no price levels/returns or outcome data accessed or printed. Allow zlib decompress first gzip member safely without CRC since range partial, require valid gzip magic, tar magic/header and at least one complete JSON row if NDJSON. If schema remains unknown mark SOURCE_PREFIX_SCHEMA_UNKNOWN not ZERO_PREDICTIONS. Quota max 2MB partial raw responses across all four; never download full files without another frozen hypothesis + budget. STOP after this one finite gate.

Earlier 2025 Binance FLOW55 49.29%, FLOW60 50.20% already rejected independently. This source is true archived OKX L2 top 400 levels but NOT automatic new 10min profit. Any future statistical model must be pre-registered before price/outcomes and must separately justify original OKX spot–OKX swap economic mechanism. Zero account, orders, payments, main merge, protected 2026 outcomes.

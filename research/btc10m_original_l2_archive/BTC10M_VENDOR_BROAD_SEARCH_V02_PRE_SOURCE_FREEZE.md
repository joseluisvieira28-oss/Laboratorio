# BTC10M ORIGINAL HISTORICAL L2 ARCHIVE V0.2 — FINAL BROAD INSTRUMENT METADATA DISCOVERY PRE-SOURCE FREEZE
31 October 2026. First V0.1 SOURCE_PAIR_IDENTITY_UNPROVEN, original CI #41234699496, artifact SHA256 084ef518c3ce42b5e124e498dd41f2a3a03614d46c5bef7dfe6bcaf856e1570e, unchanged. V0.1 read ONLY public metadata, no historic prices or market outcomes. Offline source audit CI #41234783421 read original three public JSON files, confirmed q=BTCUSDT returned zero exact venue-filtered listings, and free sample response wrapper was 'files'.

New V0.2 strictly TWO new public no-account GETs:
1. https://cryptostruct.com/api/search?q=BTC&venue=okx&class=spot
2. https://cryptostruct.com/api/search?q=BTC&venue=mexc&class=perp
Optional up to TWO additional official GETs /api/instrument/{id}/coverage ONLY if exact market ID (one and only one) is confirmed from first-party vendor search data. NO other search queries/URLs, no retries or alternate endpoint/domain, no payments/quotes/checkout, paid data, trade execution, market prices, account, wallet, keys, credentials, future market outcomes, 2026 holdout, or main merge. Total GET <=4, 12s timeout each, <=3MB JSON per reply, raw sha256 and UTC timestamps preserved.

Exact identity requires exchange_code OKEX and type SPOT and BTC vs USDT symbol (normalized BTC-USDT, BTCUSDT), and exchange_code MEXC type PERPETUAL/SWAP and BTC/USDT underlying (BTCUSDT-PERP, BTC_USDT-SWAP), never MEXC SPOT. Source result cannot be declared PASS if response does not show exchange, symbol and class explicitly. Count matches and fail SOURCE_IDENTITY_AMBIGUOUS if multiple; no ID cherry pick. Require full 2025 calendar span in both coverage metadata to infer a potential joint historical window; metadata NEVER proves actual matched tick files or data completeness, not yet a backtest. If source blocked or no IDs, record source unknown, do not proclaim the dataset impossible.

Original Nov2026 3 x OKX/MEXC opposite top5 book >=25% remains unchanged and has ZERO resolved forward events, regardless of metadata results. This is the LAST public vendor API metadata source attempt before closing this search.

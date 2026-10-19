# CRYPTO LAB — CONVEX L1 CAPACITY FRONTIER V04 — ANALYSIS FREEZE

Date 2026-10-19 UTC. PRE-ANALYSIS freeze for a **new interpretation** of previously observed immutable original V03C Binance Futures bookTicker source, not a pre-2023 market or original signal outcome freeze.

## Source identity and all-episode population
- EXACT prior V03C [Actions 39027126160](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39027126160), artifacts `CONVEX-V03C-STREAMING-ONLY-SIZE-BLOCKED-SOLUSDT` and `CONVEX-V03C-STREAMING-ONLY-SIZE-BLOCKED-BNBUSDT`.
- EXACT files `V03C_STREAMING_SOURCE_CAP_REMEDIATION.json` inside artifacts, do NOT rescan market, download publisher ZIPs or query venue APIs.
- SOL1h original BASE 33 eligible episodes in 2023-05-16 to 2024-03-30 inclusive, BNB4h original BASE 6. Each original source model 20% of separate modeled 10k account equity 1x, no account combining, no 2026 protected holdout.
- Existing known source: SOL 32/33 fresh valid <=2s and 15/32 single-best-ASK sufficient at full 20% model notional; BNB 6/6 fresh and 3/6 sufficient at full 20% notional. Those previous 20% results are already OPEN; new smaller-size ratios not yet evaluated. This is retrospective conditional inference and **NOT OOS**, no alpha certification.

## Exact static position-size frontier, frozen before reviewing ratios
- Only predefined **four** proportional notional fractions (relative to original modeled order quantity, not an account backtest): **0.25, 0.50, 0.75, 1.00**, corresponding to **5%, 10%, 15%, 20% of original modeled equity** if quantities scaled linearly while entry timestamp, equity and price are hypothetically held constant.
- For each fresh causal `BOOK_QUOTE_CAUSAL_CANDIDATE` or `TOP_OF_BOOK_SIZE_INSUFFICIENT`, compute top-ASK size to original model quantity ratio exactly with Decimal; finite qty >0, quote age integer 0 to 2000ms, original quote ask >0, no crossed best book, require has `ask_vs_modeled_entry_bps`.
- For each frozen ratio, count fresh entries where `best_ask_qty >= ratio * original_model_qty`. Keep SAME denominator of all fresh quotes (32 SOL, 6 BNB). Report full-population metrics too (33 SOL /6 BNB) and all invalid episodes by status, no survivor omission.
- Asset-level source gate retains existing >=95% fresh coverage. Size gate >=90% sufficient **among fresh** (the exact original gate) per asset and per size tier. Report all 4 tier pass/fail, including when insufficient.
- **No** post-observed ratio interpolation, optimal free-size fitting, reweighted win/loss, adjusted V5 returns, reduced fees, reduced funding, stop-loss rescue, per-trade price impact or new exit/backtest. The *largest of the four predeclared tiers with capacity >=90%* is labeled `L1_CAPACITY_SCREEN_ONLY` not execution approval; no pass means `NO_TIER_PASSES`.
- Risk of placing an actual taker order: quote displayed previously may vanish, queue can change, higher level consumption and market orders/slippage/fees/funding/gaps cannot be inferred. This is Binance Futures source, not MEXC/Kraken/OKX.
- Strict source custody: read unchanged archive original SHA256 hash and source-run metadata, keep their hashes in new output; 33+6 mandatory, status `trading_authority=NONE`, `cross_venue_execution_proven=false`, `protected_2026_opened=false`. Schema loss, duplicate/missing episodes, negative or invalid price/qty, non-finite numeric or no source tags -> fail-closed.
- Do not archive personal account info, keys, wallet data. Source remains pure public original market historical receipts.

## Meaning of verdict
Only a **descriptive conditional quote-depth observation** on in-sample original signals. Even a 100% source/size tier PASS cannot imply executable fills, net positive PnL or LIVE GO; OOS and broker-native stop roundtrip remain the main blocker. Parent V5 historical results unchanged. No main merge, Render, Windows change, cost, or trade.

Authoritative intended run: one offline GitHub Actions job with immutable artifact inputs and synthetic no-network CI; no repeating original expensive market source downloads.

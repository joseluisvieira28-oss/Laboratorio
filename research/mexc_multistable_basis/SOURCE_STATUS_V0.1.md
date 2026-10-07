# MEXC-MULTI-STABLE-BASIS-001 — SOURCE STATUS V0.1

Date: 2026-10-07

Verdict: `SOURCE_DOC_PASS__RUNTIME_PROBE_PENDING`

Confirmed from current official MEXC product pages: BTC_USDT, BTC_USDC, BTC_USD1, ETH_USDT, ETH_USDC, ETH_USD1 exist. MEXC Spot also exposes USDC/USDT and USD1/USDT markets, so later normalization need not assume stablecoin parity.

Official MEXC Contract API documentation provides public/no-auth market routes for contract metadata, depth, ticker, trades, funding, index/fair price and K-lines. Official Spot API documentation provides public exchangeInfo, bookTicker and K-lines.

The committed source-only probe is `research/mexc_multistable_basis/source_gate_v01.py`. It has not run because this chat environment could not create the new GitHub Actions workflow and direct JSON API access was unavailable. Therefore this is not yet SOURCE_PASS and no economic outcomes, basis, PnL or thresholds were opened.

Next gate: run the committed source probe in an internet-enabled runner; only after full runtime SOURCE_PASS may a separate immutable pre-outcome freeze be created.

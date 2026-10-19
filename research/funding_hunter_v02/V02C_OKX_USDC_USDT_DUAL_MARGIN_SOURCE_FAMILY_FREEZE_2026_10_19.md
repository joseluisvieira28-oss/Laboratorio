# FUNDING HUNTER V02C — SAME-VENUE USDT/USDC CONTRACT DATA AVAILABILITY FREEZE

2026-10-19 UTC, before any June 2025 USDC family archive metadata queries; no USDC rate, quote or outcome ever previously examined in V02.

Reason: cross-venue MEXC/Binance and Binance/OKX exact BID/ASK trade-entry/exit price history missing on the Binance/MEXC leg. As a structurally different and strictly SOURCE-ONLY escape route, test the existence of **both legs at the same provider OKX**: BTC/ETH/SOL USDT-margined linear SWAP versus their USDC-margined linear SWAP. OKX docs map e.g. BTC-USDC family to BTC-USDC-SWAP. This is NOT necessarily delta-neutral in USDT accounting because USDC/USDT FX basis, margin collateral, contract sizes, fee tiers, mark prices, funding changes, cross-currency conversions and liquidation risk remain. No risk-free/edge claim.

Only new-source archive metadata requests, zero outcomes:
- Fixed OKX UTC month **2025-06-01** funding archive catalogue: `module=3,instType=SWAP,instFamilyList=BTC-USDC,ETH-USDC,SOL-USDC,dateAggrType=monthly,begin=end=2025-06-01`.
- Three fixed L2 day **2025-06-02** catalogues, one per USDC family `module=4,instType=SWAP,instFamilyList=<family>,dateAggrType=daily,begin=end=2025-06-02`.
- Query at most 4 official unsigned public `www.okx.com` metadata GETs, no raw funding events, no archived BID/ASK, no private account, key, fee, transfer, paid data, wallet, order, 2026 historical holdout or future.
- Require valid API code0, six official `static.okx.com` links in expected archive extensions, independently verifiable correct underlying instrument and UTC date within archives in later separate preregistration. Any unavailable/missing/mismatched family source -> `SOURCE_BLOCKED_USDC_PAIR`, not reduce asset universe after looking.
- A catalogue success means only `SOURCE_DISCOVERY_CANDIDATE_NOT_ECONOMIC_EDGE`; further exact historical mark/settlement (funding archive contains `instrument_name,funding_rate,funding_time` without price), contract lot/ctVal, 2025 fees and collateral FX risk gates required *before* economic exercise. New true backtest rules must be frozen before opening outcomes.
- No alteration of existing V01 Binance/MEXC mechanism or retroactive substitution claiming replication. This is independent new research hypothesis, currently source candidate ONLY; no OOS 2026 or live trading.

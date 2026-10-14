# BTC REALIZED VOLATILITY V1 — PRE-OUTCOME SCIENTIFIC FREEZE
Date UTC: 2026-10-14
Authority: explicit operator "AUTORIZADO ATACA COM TUDO", research/science-only.
Branch: research/btc-realized-volatility-v01-2026-10-14
State: RULES_FROZEN_BEFORE_THIS_FAMILY_MARKET_OUTCOME / NO TRADING AUTHORITY.
DO NOT: change main, order, trade, authenticate, access accounts, wallets, Render, paid services, protected 2026 holdout, or tune after outcomes.

## Hypothesis
A trend-filtered **BTC realized-volatility expansion** at confirmed 4-hour closes may change forward return distribution net of friction relative to an exactly matched EMA50 crossover comparator. This is NOT the unavailable exlux/BitMEX BVOL7D original, is not a copy of its backtest, and does not inherit its 4H/1D positive CSV returns. Our indicator uses only *past Binance BTCUSDT perpetual price closes*; no BitMEX/Coinbase. Its added predictive value, if any, must be demonstrated, not assumed.

## Fixed scope / time
- USD-M BTCUSDT futures, Binance public market archive, UTC.
- Historical analysis: 2021-01-01 00:00 UTC to 2025-12-31 23:59 UTC, with full 2020 warm-up. 2026 is closed, not downloaded, and protected lab 2026 holdout stays locked. 2021–2025 BTC has been studied elsewhere in Crypto Lab, so NONE of this is independent OOS even if the freeze precedes this new family’s outcomes.
- Canonical Binance Vision BTCUSDT 1h market OHLCV: monthly ZIP + publisher ZIP .CHECKSUM SHA256, full consecutive 1h bars and no manufactured gaps. Resample to UTC 4h using only four finished 1h candles: O=first O, H=max H, L=min L, C=last C. WARMUP complete before 2021; no time changes/selection.
- Full official public BTCUSDT monthly USD-M fundingRate archive 2021–2025 + CHECKSUM. The exchange funding event timestamp must exist (no substitute zero). If the official archive yields usable exact historical markPrice, use that for notional settlement; otherwise pre-frozen **1h market OPEN** at funding event time as a FUNDING PRICE PROXY (labeled, not venue exact). No financing exemption. Fail-closed on missing monthly zip, SHA, timestamps, rate, duplicates or invalid funding. Do not assume exchange real fill or fee tier.
- One hour archive is the single canonical market source for both 4h signal and 1h stop/next-market-open fill. No 2026 data. Use run-time SHA256 receipts for all sources, version and parameters.

## Frozen signals at completed 4h close T (data through T only), next 1h open T+moment, no same-bar entries
EMA50 on confirmed 4h closing prices, alpha=2/51, first EMA value = SMA of first 50 complete 4h closes. Trend filter: close[T] > EMA50[T] AND EMA50[T] > EMA50[T-3]. EMA crossover: previous completed bar close <= previous completed EMA50 AND current completed bar close > current EMA50, plus trend filter. Log returns r_i=ln(close_i/close_{i-1}) calculated on confirmed completed 4h bars. RVshort = population STD of last 24 r_i; RVlong = population STD last 126 r_i; ratio=RVshort/RVlong, requires both fully observed, nonzero denominator. RV expansion = ratio > 1.35 AND ratio > prior completed ratio.
Three independent 10,000 USDT virtual paper accounts, all unchanged execution/cost rules:
- E0 / EMA50_BENCH: new LONG only on bullish EMA crossover plus trend filter; exit rules below.
- E1 / EMA50_RV_FILTER: exact E0 signal AND RV expansion at same witnessed bar (strict conditional subset).
- E2 / RV_EXPANSION_ENTRY: RV ratio crosses from <=1.35 to >1.35 at completed T, trend filter true and RVshort rises; distinct event entry, same exit policy.
All signal decisions from fully completed 4h candles, no cross-timeframe forward security, no lookahead; entry at first 1h market OPEN after signal bar confirmed, not at signal CLOSE. Only one open LONG position per paper account; ignore entries when already long; no short, scaling, pyramiding or leverage.

## Frozen exits and risk
- Position traded notional at entry 20% of **current independent paper equity**, 1x isolated-equivalent book, no portfolio cross-collateral assumption. Start 10,000 USDT; no real broker min-lot proof.
- Initial protective risk reference at entryFill × 0.96 (4% downside); on subsequent hourly bars, stop if hourly low touches. Conservative gap handling: if hourly open below stop, SELL at that open with adverse execution slip; else sell at stop with adverse execution slip. No intrahour order queue proof. Stop stays fixed and does NOT move; no take-profit. Stop floor based on entered execution price, never calculated before fill.
- EXIT on first 1h OPEN after fully confirmed 4h CLOSE falls below EMA50, OR max 180 completed 4h bars (30 calendar days) since entry, OR the protective hourly stop; exit decision only uses fully available completed candles. If EMA exit coincides with stop event at first same hour, apply market open exit then conservative stop check; no favorable intrahour assumption.
- At funding event timestamp strictly after entry and before exit, apply funding **-position_qty * frozen price-reference * fundingRate** for LONG, positive or negative as observed. Financing is not simply ignored if small. Interpret funding timestamp and settlement semantics explicitly. PnL at fill based on simulated traded quantity.
- Entry/exit simulated adverse slippage BASE 2bps per side and STRESS 5bps per side (multiplies executed price), taker fee 8bps per side both scenarios, transaction fee on EXECUTED notional; publish gross price, each fee, slippage, funding, terminal mark and open position reconciliation.
- Stop and funding margin/real maker queue/liquidation not proven; do not claim executable risk certification.

## Prespecified controls and falsification
1. Same source/years, risk/size/stops/time cap/fees, identical engine code for all E0/E1/E2 and BASE/STRESS; strict source fail-closed. No other symbols, windows, R-threshold sweeps, TP tuning, or cost changes to rescue losses.
2. Run unit tests BEFORE reading any market result: no future-bar leakage, post-confirmation fill, 4h aggregation, RV calculation, EMA, stop and gaps, financing signs/time, order fees/slippage, no same-position duplicates, end-of-history open marking. Verify zero-cost price-only economics separated from slippage and fees.
3. For each arm give all 5 calendar years, complete ledgers, PF, trades/yr, realized and terminal net returns, intrahour conservative MTM drawdown, peak/trough and worst observed trade, concentration: static remove top-three positive closed trades (label NON-CAUSAL), compare 2024–2025 diagnostic not OOS.
4. Predeclared **strict historical candidacy** (still NEVER live authority): E1 or E2 has >=60 closed total, >=8 exits in both 2024 and 2025, positive terminal marked return in BASE AND STRESS, PF>1.15 in both, worst simulated MTM DD <=20% in BASE and <=25% STRESS, at least 4/5 profitable net realized calendar years, and static closed PnL excluding top3 winners positive in BASE. E1 must outperform E0 baseline on expectancy/trade after costs AND exhibit a value improvement despite lower sample; E2 must outperform E0 in equity return AND PF to claim incremental economic effect. If insufficient sample, INSUFFICIENT, not PASS. Any winner would be research priority only, not OOS/real edge.
5. If E0/E1/E2 all fail or missing source, close this exact child / archive. No tuning on already-seen 2021–2025 BTC to save it. A new family needs materially different causal hypothesis and freeze before new outcomes.

## Execution procedure
Freeze this document and its GitHub commit PRIOR to creating/running replay workflow or reading market outcomes. Add Python engine + tests on this isolated branch. Workflow optional only research-only on research branch or draft PR, no default-branch scheduling or secret/account access. GitHub-hosted public anonymous archive access may be unavailable; if so record SOURCE_BLOCKED with exact filename/network failure, never invent results or trade receipts.

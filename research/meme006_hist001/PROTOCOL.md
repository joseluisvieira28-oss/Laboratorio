# MEME-006 HIST-001 — Price-only retrospective falsification (READ ONLY)

**Frozen before acquiring historical outcomes: 19 Nov 2026 UTC.**
**Separate from the prospective MEME-006 main workflow.** Do not modify, retrain, tune, stop, or merge into the deployed forward protocol.

## Question and data
User asks whether *the exact two price thresholds in the 006 protocol* worked in the past. Historical complete reproduction is impossible with free hourly GeckoTerminal bars alone: historical 1h DEX Screener buy/sell counts, real SOL liquidity at that time, pool cross-source reconciliation at that instant, and Raydium buy/sell execution quotes at that instant are NOT available in OHLCV. This script tests **price-only necessary conditions** to try to reject the idea before investing further in data sources; it is NOT a historical economic backtest of the original strategy.

### Frozen population
The same 6 *currently surviving* Solana memecoin mint/pool identities, verified from the immutable MEME005 snapshot (#44362407659, SHA256 39ee74fb7521ca699b7e3bbbb83b37fcd133ac05fe8ee2349c79c360043889e4). No substitutes, no cherry-picking, keep API failures visible. Selection by 18 Nov 2026 cap leads to **retrospective survivorship/selection bias** for Oct 2026.

### Frozen observation window / availability
- UTC 2026-10-01T00:00:00 to 2026-11-15T00:00:00 (exclusive), strictly BEFORE MEME-005/006 selection and deployment.
- Source: GeckoTerminal public historical pool hourly OHLCV (USD base-token price, USD traded volume), /api/v2/networks/solana/pools/{POOL}/ohlcv/hour?aggregate=1&currency=usd&token=base&limit=1000&before_timestamp=UNIX_SECONDS; walk back at most three pages per pool. Max 6 pools x3 =18 source GETs. Public GET only, no credentials.
- Bar timestamps are **bar-open** time. UTC observation times are HH:37 for even hours (0,2,...); use the last fully CLOSED hourly candle HH-1:00, which closed 37 minutes before observation. Never use HH:00 candle that is still open at HH:37.
- Need exactly contiguous closes for h1/h6 and h4/h24 (no interpolation, no forward-fill); skip missing bars. Only count outcomes when exit bar exists at exact horizon.
- At most 1 signal per 4 hours per mint **per policy** (simulates spacing, but not actual settled risk). Do not tune thresholds after reading returns.
- Discovery window: 01 Oct to 23 Oct (22 days); holdout window: 23 Oct to 15 Nov (23 days). Date split fixed pre-run. This is a chronological score partition, but NOT unbiased holdout due Nov18 cohort selection.

### Hypotheses as requested
- Price-only REVERSAL: observed price return over 6h <= -4.0% AND 1h >= +1.5%.
- Price-only MOMENTUM: observed 6h return >=+5.0% AND 1h >=+2.0%.
- Original additional requirements: h1 buys >= sells AND at least 20 h1 transactions, pool >=7d, liquid >=150k USD, historical 24h volume>=50k, 24h trades>=200, verified cross-source price and same-time 0.05 SOL router roundtrip cost <=2.5% and slippage <=50bps. **NOT validated** from these historical price bars; do not treat an OHLCV price signal as an original full signal.
- Use full-run every-other-hour price-only baseline and no-trade 0%. For comparability report whole-population unconditional per token, discovery/holdout and 4h/24h horizon. Candle close-to-close returns are not executable quotes.
- Apply *hypothetical* 0%, 1%, 2.5%, and 5% simple roundtrip cost stresses to OHLC close ratio, i.e. `net_pct = gross_pct - cost_pct`. These are **not** reconstructed historical execution fees or Raydium quotes. Do not import future 18-Nov Raydium fees into prior dates.

### Reporting
All six pool IDs and per-source data hashes, fetched/reception timestamps, HTTP failure status, hourly candle counts, coverage gaps and qualifying raw-price signal counts. Per-signal gross and assumed cost stress net by 4h/24h; p(win), mean, median, day-cluster bootstrap 95% CI; sample sizes by coin/discovery/holdout. Split date and cohorts frozen. Neither tuning nor selection of best subgroup post-hoc allowed.

### Gates
Any *historical proxy* mean <0 with sufficient data makes **price-only evidence adverse** (not logical proof exact strategy loses, since buy/sell and liquidity gates might select winners). If favorable, it is **only preliminary** because all original buyer, depth, router, final fill gates were NOT validated and retrospective survivor bias persists. Under no circumstance can this generate a trade signal/financial GO. MEME006 prospective independent evidence remains primary.

No trading, no private API, no buys, no selling, no accounts, no signing, no auto-merge. Artifacts internal research only; retain JSON report, not redistribute raw third-party dataset.

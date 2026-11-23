# BINANCE-DIAMANTE-001 — Stage 1: independent Binance Spot source gate

**Frozen at design / 23 November 2026.** Isolated read-only acquisition and provenance test, **not an alpha experiment**, bot, deployment, economic backtest, or live/paper trading system.

## Scope locked before source outcome
- Venue: Binance **Spot only**, not Binance USD-M, futures or options.
- Exactly three symbols: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`.
- Exactly one preselected UTC integrity day: **2026-11-12**, 1m.
- Canonical official public source: `https://data.binance.vision/data/spot/daily/klines/<SYMBOL>/1m/<SYMBOL>-1m-2026-11-12.zip` plus corresponding `.CHECKSUM`; no geographic restrictions bypassed.
- Exactly six public HTTPS GET requests, at most 4 MB/archive and 1 KB/checksum; timeout 20s; no keys, accounts, payment or private endpoints.
- Archive originals and official checksums only in temporary isolated Actions artifact; report per-symbol raw SHA256, CSV hash, 1,440 1m timestamps/day and integrity, with SHA256 manifest. Do not emit price/returns/entry signals/PnL.
- Official Binance public data specifies **Spot timestamps from Jan 2025 in microseconds**. Reject millisecond-looking 2026 data, rather than silently changing units.
- Fail closed on HTTP error/451, missing/checksum mismatch, invalid ZIP, duplicates/gaps/out-of-order/out-of-day timestamps, oversized payloads, invalid columns. Partial pass remains SOURCE_BLOCKED.

## Existing studies must remain independent
- [DIGUI-011 PR #362](https://github.com/joseluisvieira28-oss/Laboratorio/pull/362): **USD-M** BTC/ETH/SOL 1h/4h study, already with cost/chronology rules; no PnL transfer to Spot.
- [CARRY-001 PR #356](https://github.com/joseluisvieira28-oss/Laboratorio/pull/356) and [CARRY-002 PR #359](https://github.com/joseluisvieira28-oss/Laboratorio/pull/359): funding/ETH margin, distinct instruments.
- [BTC 10m Spot-vs-Perp flow PR #313](https://github.com/joseluisvieira28-oss/Laboratorio/pull/313): prior historical **NO EDGE**, do not retune into invented edge.
- [Reactive Shock PR #350](https://github.com/joseluisvieira28-oss/Laboratorio/pull/350), [MRCR PR #90](https://github.com/joseluisvieira28-oss/Laboratorio/pull/90): macro event/timing rules, not proof of predictable direction.
- MEME-006 and all prospective frozen studies: untouched.

## Stage gates
1. **Stage 1 SOURCE_ONLY**: retrieve original source and verify SHA/time/schema offline. `SOURCE_PASS_ONLY_NO_ECONOMIC_INFERENCE` authorizes only data-engineering follow-up.
2. **Stage 2**: recover original 112 macro event corpus and source hashes; independently obtain pre-release, timestamped CPI/NFP consensus as known at the time. No revised hindsight values. Freeze a *new* hypothesis before opening target returns.
3. **Stage 3**: independent chronological backtest, venue-appropriate fees/spread/slippage, baselines, event bootstrap, multiple-testing adjustment, excluded failures documented and OOS kept sealed.
4. **Stage 4**: prospective shadow/paper, real executable bid/ask and eligibility/account costs verification; this is **not** trade authorization.

## Safety and interpretation
No orders, exchange API keys, accounts, wallets, deposits, paid sources, trading, futures activation, Render, Telegram, production alerts, main merge or other branch changes. Do not represent a green CI or SOURCE_PASS as profitability. If source blocked, report original error without circumvention or fabricated replacement. Preserve run ID, source hashes and raw artifact for audit.

Official docs: https://github.com/binance/binance-public-data/blob/master/README.md ; https://developers.binance.com/en/docs/products/spot/rest-api .

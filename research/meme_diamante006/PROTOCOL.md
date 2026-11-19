# MEME-DIAMANTE-006 — prospective frozen experiment v0.1

**Frozen UTC 2026-11-19, before first independent observation.**
**Research only. Not an auto-trader, alert service, or recommendation.**
Previous evidence MEME-003/004: negative/inconclusive. MEME-005: 6/15 top-cap memecoins qualified for a *screen*, with 0.05 SOL read-only reverse quotes but zero realized PnL.

## Population fixed before testing
- Exactly the 6 mints with `SCREEN_PASS_ONLY` in the **existing** immutable CoinGecko top-15 snapshot from [MEME-005 run #44362407659](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44362407659), `snapshot.json` SHA-256 `39ee74fb7521ca699b7e3bbbb83b37fcd133ac05fe8ee2349c79c360043889e4`.
- Never substitute, drop or backfill a different coin mid-study when a coin fails. Record missing markets, broken mint/pool mapping, migrations and quote failures as censored.
- Population is explicitly **survivor-selected by market cap**; generalizations to new launches are invalid.

## Frozen run cadence and horizons
- `GitHub Actions` schedule at minute 37 every 2 hours UTC from 2026-11-19 to 2026-12-23 inclusive (only on repo default branch, bounded runtime date guard).
- GitHub schedule can be late/skipped. **Actual artifacts**, not planned schedule, constitute sample. Dedicated one-shot workflow can also test offline.
- Entry *eligibility* at most once per mint per **4 hours**; observations at every successful run. It is an opportunity sample, not independent trades. Cluster results by UTC day and mint.
- Exit-quote horizons: **4h** (within 4–6h) and **24h** (within 24–28h) from entry quote receipt. Missed windows are `CENSORED_WINDOW_MISSED`. First available quote *after* target is used; never interpolate or fill forward.

## Signal definitions (all inputs point-in-time and read before quote)
A common quality gate on the exact preselected pool:
1. age >=7d, reported liquidity >=$150,000, volume24h >=$50,000, 24h swaps >=200;
2. DEX Screener pool base mint and pair address *exact match* to frozen snapshot;
3. GeckoTerminal base price <=3% different from DEX Screener price at observation; else `SOURCE_UNVERIFIED` (these are not simultaneous executable quotes);
4. successful Raydium quote **SOL->mint** (size 0.05 SOL, `slippageBps=50`), then **mint->SOL** with the first quote's *minimum output tokens*; discard as entry if estimated conservative immediate roundtrip cost >2.50% or quote age/latency excessive (>30 seconds each). All quote receipts hashed, including failed calls.

Policies applied to the same eligible observation:
- **H_REVERSAL**: `priceChange.h6 <= -4.0%`, `priceChange.h1 >= +1.5%`, `txns.h1.buys >= txns.h1.sells`, h1 swaps >=20.
- **H_MOMENTUM**: `priceChange.h6 >= +5.0%`, `priceChange.h1 >= +2.0%`, `txns.h1.buys >= txns.h1.sells`, h1 swaps >=20.
- **CONTROL_UNCONDITIONAL**: all eligible observations at same opportunity slots regardless of return pattern. Distinguish no-signal from no-trade baseline (net PnL=0).
No tuning or threshold revisions after freeze. Report each policy **separately**; no winner-picking.

## Counterfactual quote settlement
- Buy `otherAmountThreshold` of first SOL->token quote defines **minimum hypothetical token inventory**, not filled tokens.
- Future Raydium token->SOL `GET /compute/swap-base-in` with *that exact raw token quantity*, take resulting SOL `otherAmountThreshold` (50bps floor). Subtract illustrative 0.0001 SOL fixed network/priority overhead per roundtrip, in addition to route fees in the quotes (do **not** add them again).
- `net_proxy_pct = 100 * (exit_min_SOL_lamports - 50_000_000 - 100_000) / 50_000_000`. A negative result is a mathematical opportunity loss **if** both quotes could be reached; a positive result is only a **counterfactual quote**, never executed profit.
- First network/source failure at settlement remains `PENDING` until its upper-window limit; after that mark **CENSORED**, never winners. Failure source totals are preserved and reported. Do not substitute DEX price or future OHLC into a missing quote.
- Timing, fee route, liquidity, frontrunning, wallets, gas or failed transaction **are not verified by this study**.

## Scientific/economic gates
Prospective evidence **cannot** mature before >=30 distinct elapsed calendar days, >=200 fully settled policy signal/horizon observations (not just controls), no post-hoc selection. Compare H_REVERSAL, H_MOMENTUM to identical-hour unconditional entries and no-trade, with by-day bootstrap CIs and missing-as-loss sensitivity. An insufficient sample is **INCONCLUSIVE**, not GO.
- If conservative daily block-bootstrap 95% **lower** bound <=0 or controls outperform, NO EDGE.
- If positive, classify **scientific proxy candidate** only, **not** permission to trade: marketable fill/MEV/latency and real transaction costs must be validated independently prior to financial GO.
- NO-GO real capital at all stages without independent actual fill evidence; 0 trading enabled.
- Allow no more than one position per token per 4h to reduce fictitious exposure; 24h shadow outcomes overlap and must not be called independent trade results.

## Data integrity and safety
- Source snapshots are immutable workflow artifacts (`state.json` + `state.sha256`, SHA-256 verified on subsequent run), previous hash linked in state metadata.
- If any prior artifact that is needed cannot be fetched or verified, the run MUST fail with `CONTINUITY_BLOCKED`; no reset or overwrite.
- Actions `GITHUB_TOKEN` only accesses prior repo artifacts; **no wallet keys, no signature, no user funds, no trading/swap submission endpoints, no paid requests**. GET requests only.
- Hard shutoff after 2026-12-23 UTC; no actions that can place orders.
- Retention 90 days; archive meaningful results separately before expiry if needed.
- A merged scheduled workflow is required before cron works; PR CI alone does NOT activate observations. Scheduled runs are not guaranteed by configuration.

## Sources
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.dexscreener.com/api/reference
- https://github.com/raydium-io/raydium-docs-v1/blob/main/sdk-api/trade-api.mdx

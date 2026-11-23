# BINANCE-DIAMANTE-006B — FREE OFFICIAL SPOT 1-SECOND CANDLE FLOW PROXY / 90 DAYS

**Separately frozen 2026-11-23 BEFORE downloading/reading ANY 006B market archive bytes.**
Research ID `BINANCE006B-SPOT-1S-SELLFLOW-60S-OOS-V01`.

## Why 006B is separate, never a rescue
- BINANCE006 V01 on PR #377 was **SOURCE_SIZE_BLOCKED**: the first official BTC Spot 2026-08 `aggTrades` monthly ZIP was **357,661,918 bytes**, above its fixed 250MB limit. No original data downloaded and no economic results. Do NOT revise or silently disregard its report.
- This NEW study uses **1-second SPOT klines**, with Binance's `quote asset volume` and `taker buy quote asset volume` fields as a **coarser 1-second proxy** of sell-initiated volume; it does NOT represent individual trades, book changes, or an executable fill. No L2 absorption finding. This is a different information set from V01; never pool.
- Independent from BINANCE-004/005 (exact L2 resilience) and BTC10m spot/perp NO_EDGE #313. Do NOT edit previous PRs, protocols, or 005 multi-day automation.

## EXACT pre-frozen public archive
- Binance official `https://data.binance.vision/data/spot/monthly/klines/{symbol}/1s/{symbol}-1s-{YYYY-MM}.zip` + original `.CHECKSUM`, symbols exactly BTCUSDT, ETHUSDT, SOLUSDT, months 2026-08,09,10, only 2026-08-01T00Z <= bar.open_time < 2026-10-30T00Z. 9 ZIPs (not 18). 2025+ Spot CSV times are **microseconds**.
- Verify all 9 official SHA256, all 1-second bars for 90 calendar days per asset (7,776,000 bars each, 23,328,000 bars across 3), strict 1,000,000-microsecond spacing, proper unique candle timestamps, 12-column official CSV, finite OHLC prices, nonnegative quote volumes, quote buy volume <= total and implied sell>=0.
- Before any ZIP GET: 9 public HEAD, 9 small public original CHECKSUMs. If any file missing or >250MB each, or total compressed size >900MB: **SOURCE_BLOCKED**, no full price-history downloads. Read-only standard `ubuntu-latest` public GitHub Actions runner. Max runtime 35 minutes, no retries.
- Raw original file SHA256 in receipt manifest. Do NOT store paid/restricted datasets or make private API requests. Do NOT silently skip months, symbols, seconds or incomplete files.

## Frozen hypothesis, timing and groups
- At each UTC-aligned 30-second bin close, use **only 1-second bars that completed by that close**. Total `quote_asset_volume >=5,000 USDT`; implied seller-initiated share `(quote - taker_buy_quote)/quote >=65%`. A bar whose close occurs after the decision is never included in that decision.
- LONG hypothetical at **close price of FIRST NEXT COMPLETED 1-second candle**, <=3 seconds after decision; at first completed 1s bar close >=entry_time+60s, <=3 seconds after target. Each BUY+SELL represented by two trade-print-derived *1s close proxies*, NOT executable orderbook bid/ask; 1sec compression introduces extra uncertainty.
- Per symbol 120s cooldown separately for SELL_FLOW primary and BASELINE. BASELINE is long every fourth **fully observed 30-sec bin** with quote volume >0, regardless of aggressive-flow share, same entry/exit/costs. Control can overlap with primary, so no summing win counts.
- Fixed reference notionals 1,000 USDT per hypothetical trade; no compounding/capital model; no shorting or per-asset winners.
- BASE costs taker **10bps** + adverse slippage **2bps** per side; STRESS taker 10bps + adverse slippage **5bps** each side; computes net exit/entry price ratio adjusted both sides. **Spread, price impact, queue priority and user-specific effective fees UNOBSERVED** => even a positive scenario is *not executable profitability*.
- Train: 2026-08-01..2026-08-30 (30 days); validation: 2026-08-31..2026-09-29 (30 days); untouched OOS test: 2026-09-30..2026-10-29 (30 days). **No parameter tuning in either group in V01**, and cross-split exit is censored, not transferred. All 3 symbols evaluated together, per-symbol and per-day breakdown retained.
- Preserve EVERY decision including late/censored outcomes. Report source gaps as blocked, not as clean samples.

## Minimum independent scientific evidence
TEST OOS-only >=200 matured SELL_FLOW and >=20 independent UTC days, stress net average >0, **10,000 fixed-seed (20261123) bootstrap whole-day clusters** lower 95% >0, no single UTC day >20% of total positive gains, mean stressed primary > unconditional baseline. Need further **new forward replication** regardless of historical GO. NO real trade/account/order, no executable fills, NO live GO, no subscriptions/payments, no production, no merges to main.

Only one 90-day attempt. If blocked from public source, report `SOURCE_BLOCKED`, do not tamper with filters. Historical source timestamp as-of vs real-world market data timestamp not identical due publication; the model assumes completed bars visible after close.

Official schema and documented `1s` cadence: https://github.com/binance/binance-public-data/blob/master/README.md .

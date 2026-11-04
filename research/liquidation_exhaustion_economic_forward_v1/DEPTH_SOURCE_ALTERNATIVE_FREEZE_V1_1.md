# LIQUIDATION EXHAUSTION — MEXC DEPTH SOURCE ALTERNATIVE V1.1
Frozen 2026-11-04 UTC BEFORE any V1.1 observation. Public source-only technical amendment, NOT strategy tuning.

## V1.0 immutable failure (do not rescue)
Forward V1 original frozen economic model commit 88e7632c, new 240s source-only run 41872000026; raw artifact 13344184977. Bybit 9366 contiguous book deltas, 5903 executed trade children, zero BTC liquidation children observed in this 240s; MEXC ticker 94 valid-symbol BBO frames, 64 older than frozen 1500ms max receive lag, 30 fresh, 18 after initial quarantine. Source verdict **MEXC_EXECUTABLE_QUOTE_SOURCE_BLOCKED**. No economic triggers, prices at decisions, PnL or outcomes opened. Preserve without changing the 1500ms freshness limit.

## NEW distinct quote-source alternative: depth snapshots
Official MEXC Futures WS public sub.depth.full BTC_USDT limit 5; compare separately with sub.ticker on same public socket, endpoint wss://contract.mexc.com/edge. Capture native frames with local receive UTC ms and monotonic ns and original exchange envelope timestamp, raw SHA256, no auth, order, private account, capital, output ROI or return.
Depth accepted only when channel push.depth.full and symbol BTC_USDT, data contains nonempty bids/asks (each price/quantity>0), best bid < best ask; receive-source latency in [-250,+1500] ms. Require three consecutive fresh valid snapshots before quoting eligible. Never substitute current receive time for a stale/missing publisher timestamp.
A source-only 120-second probe has two subscriptions on ONE public socket. Mandatory: subscription acknowledgments, no transport error, >= 30 complete fresh depth updates AFTER 3-frame warmup; min 2 pongs; zero stale frames *after* quarantine for quality pass; no crossed book and no timestamp violations. Report tickers separately as descriptive, never count as fresh depth. Note: true bid/ask from a 5-level snapshot is not proof of executable fill at desired position size.
If transport works but quote count insufficient, SOURCE_INSUFFICIENT_DEPTH. If timestamp quality errors, MEXC_DEPTH_SOURCE_BLOCKED. A PASS is MEXC_DEPTH_SOURCE_WINDOW_TECHNICAL_PASS ONLY — not simultaneous Bybit+MEXC positive liquidation event nor economic EV. Do not open PnL.
If new depth source passes, future genuinely new economic-forward capture must freeze source replacement version explicitly before observing any outcomes. Original numerical trigger, 5/15/30s, 60s horizon, 20/36bps scenarios, 1500ms quote threshold and holdout requirements remain UNCHANGED. Do not retroactively relabel V1.0 successful.
One bounded public-only GitHub Actions run, branch only, no recurring schedule, no trading or main merge.
Refs:
https://mexcdevelop.github.io/apidocs/contract_v1_en/
https://www.mexc.co/api-docs/futures/update-log
Parent research PR #333, source-qualified PR #332.

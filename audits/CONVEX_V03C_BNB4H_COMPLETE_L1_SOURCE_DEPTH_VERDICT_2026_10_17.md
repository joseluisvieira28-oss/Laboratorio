# CONVEX V03C — BNB4H EXACT SIX HISTORICAL SOURCE CAP REMEDIATION — FINAL VERDICT
Date 2026-10-17 UTC. The frozen source-only V03C ran [GitHub Actions #39027126160](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39027126160), BNB job 117380215853, SUCCESS. No market strategy changes, no OOS, no broker fills, no account data, no orders.

**Prior V03B:** 6 original BNB4h BASE entries in historical publisher Binance bookTicker availability window, 3 fresh, 2 with adequate quoted single-best-ASK quantity, 3 resource cap BLOCKED. Root-cause artifacts proved previous three failures due solely to researcher-imposed download/uncompressed size caps, NOT absence of exchange market data.

**V03C correction:** only exact original 3 date sources restored, same URLs, publisher SHA256 sibling checks, bounded 320MB disk-stream ZIP reader + 2.5GB uncompressed cap. All THREE originally blocked archive dates:
- 2024-01-08: ZIP 67,674,558 bytes, publisher SHA256 PASS, 961,498 causal events read up to the original entry.
- 2024-03-05: ZIP 87,476,655 bytes, publisher SHA256 PASS, 5,301,143 events.
- 2024-03-19: ZIP 114,532,192 bytes, publisher SHA256 PASS, 5,287,344 events.

The three valid V03B dates were **not re-read or reclassified**. Prior source receipts preserved in separate immutable artifact. Final full denominator original 6/6: 
- `BOOK_QUOTE_CAUSAL_CANDIDATE`: **3/6**.
- `TOP_OF_BOOK_SIZE_INSUFFICIENT`: **3/6**.
- SOURCE_BLOCKED 0 / missing past quote 0 / stale 0.
- **Fresh publisher-verified L1 quote coverage: 6/6 = 100%**, passes frozen >=95%.
- **Single-best-ask-size sufficiency: 3/6 = 50%**, fails frozen >=90%.
- Fresh best ASK vs original modeled BASE entry difference: median -1.90214bps, min -1.99960bps, max -1.58348bps. Original V5 entry assumes market 5m OPEN + 2bps slip, no actual broker fill. Negative simply means past-only public best ask was slightly below the modeled entry price at the timestamp; this does not resolve executable market impact when size > top-ask quantity.

**Operational/Scientific verdict:** `L1_HISTORICAL_SOURCE_GATES_INSUFFICIENT` specifically from **best-ASK quantity depth**, not data availability. Does not mean BNB model is losing or cannot fill via multiple L2 levels; to model full quantity requires synchronized historical 2-sided L2 book and market impact/stop exits, absent here. No credible portability to Kraken/OKX/MEXC, no native stop ACK, no new OOS, protected 2026 remain locked, NO LIVE GO.

The 2023-25 historical BNB4h V5 returns remain unmodified descriptive evidence and not a money-machine claim.

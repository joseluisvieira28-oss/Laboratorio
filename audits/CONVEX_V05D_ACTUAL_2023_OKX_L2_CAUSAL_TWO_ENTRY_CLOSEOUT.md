# CONVEX V05D — REAL OKX PORTAL L2 SOURCE CLOSEOUT (2026-10-19)

Two operator-supplied official 2023 perpetual-swap 400-level tar.gz files were processed privately, never committed to GitHub. The archives contain one .data JSON-lines member with snapshots and incremental book updates, without seqId/prevSeqId. The previous V05C assumed a different schema; V05D fixes that offline parser.

Previously frozen original Binance V5 LONG entry timestamps: SOL 2023-05-29 16:05 UTC, BNB 2023-11-01 16:05 UTC. Last accepted L2 updates preceded T0 by 51ms and 3ms, respectively. Both books contained 400 valid bid and 400 ask levels at the instant reviewed.

Original modeled BASE quantities: SOL ~104.792 SOL, BNB ~8.82249 BNB. Applying the **contract size published at listing** (SOL 1 SOL/contract in 2021; BNB 0.01 BNB/contract in 2022), the full hypothetical static LONG entry can traverse displayed ask levels within 4 levels on SOL or 3 levels on BNB. Theoretical ASK VWAP prices: SOL ~20.460103 USDT, BNB ~223.170448 USDT; costs to walk relative to respective OKX best ASK: SOL ~1.517bp, BNB ~0.468bp. Neither full quantity could be filled at the single best ASK on those two observations. Contract size/lot increments must still be verified **at the precise 2023 dates**; fraction-of-contract sizes have not been rounded to actual exchange lot sizes.

Source chronology: 965 SOL initial/periodic snapshots and 1,928,579 updates before T0; BNB 968 snapshots and 1,715,581 updates. Both archives contain no continuity sequence IDs, and the largest inter-event gap in BNB during the day was ~90s; successful chronological parsing does not prove no dropped updates. User-file SHA256 is **local custody only**, not publisher-signed checksum.

**VERDICT:** Actual original-date OKX L2 historical book data can be reconstructed provisionally and the originally missing multi-level depth exists in these **2 examples**. This does NOT verify actual broker fills, full 2023-25 trading performance, stop execution, funding, fees, 2026 OOS edge or profitable live trading. Science only, NO LIVE GO. The broader L1 SOL 33 and BNB 6 original source gates and all protected history remain unchanged.

Source specs: https://www.okx.com/en-eu/help/okx-to-enable-margin-trading-savings-and-list-perpetual-for-sol-lon and https://www.okx.com/de/help/okx-to-enable-margin-trading-savings-and-list-perpetual-for-bnb .

Next: verify historical ctVal/lot and exact original exit day, then evaluate corresponding bid-side L2 exit conservatively. Private raw files must not be redistributed.

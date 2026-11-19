# MEME-DIAMANTE-007 — Historical Solana swap flow recovery
Frozen 2026-11-19 UTC before trade-source outcomes. Read-only scientific research. Economic NO-GO.

## Locked cohort and unchanged strategy
Use exactly six mints/pools from MEME005 Actions run 44362407659, seed snapshot SHA256 39ee74fb7521ca699b7e3bbbb83b37fcd133ac05fe8ee2349c79c360043889e4. Historical outcome window 2026-10-01 to 2026-11-15, discovery/holdout split 2026-10-23. These six coins are survivor-selected as of 2026-11-18, so historic analyses inherit hindsight selection bias.
Retain deployed MEME006 price triggers unchanged: REVERSAL h6 <= -4%, h1 >= +1.5%; MOMENTUM h6 >= +5%, h1 >= +2%. Additional as-of gate: h1 buys >= sells AND h1 swaps >=20. Quality: pool >=7d, reported liquidity USD >=150k, volume24h >=50k, swaps24h >=200, DEX/Gecko cross-price <=3%, 0.05 SOL swap route immediate stress cost <=2.5%. Any historical gate lacking point-in-time source means FULL HISTORIC MEME006 IS INCONCLUSIVE, not PASS.

## Trade data requirements
Historic DEX swap record must have signer/trader, block timestamp, exact token bought/sold mint, amount and optional USD notional, signature, instruction indices and pool/venue. Distinguish economic swap from split aggregator fills, internal router legs, duplicates and wallets managed by one beneficial owner. A token transfer is not automatically a swap. Do not label base acquisition vs disposal without both actual legs. For each HH:37 UTC signal, trailing exactly 60m, at least 20 economic swaps, buys >= sells; otherwise UNKNOWN if incomplete. Source timestamp vs later update timestamp recorded.

## Prior independent price-only findings
MEME006-HIST001 PR #370: 6,363 hourly price candles over 45d, 18 reversal and 18 momentum raw-price triggers, both negative mean returns after 2.5 percentage point hypothetical costs; did NOT reconstruct buyer counts, historical source agreement, liquidity nor executable quotes. Must not relabel price-only observations as economic results.

## Historical-source investigation (no spend)
1. Dune dex_solana.trades official schema. Authenticated query execution requires user account/API key; no use of nonexistent permissions or bypass.
2. GeckoTerminal free GET /api/v2/networks/solana/pools/{pool}/trades. Latest trades only (up to 300 within previous day); not historical October. Probe actual fields/cutoff; all source failures explicit.
3. SolArchive.org CC BY 4.0 archived raw tx. Only index/schema metadata for 2026-10/11 until size and ability to decode exact pool DEX swaps verified. Do not download blockchain-wide months.
4. Bitquery archive add-on paid; no spend; public 2026-06 sample inapplicable.
Keep signed read-only source receipts (URL, timestamp, HTTP status, source digest) and deterministic offline SQL+CSV reducer and unit tests. No raw private user accounts, no purchases, no order submissions.

## Decision
No full-source evidence => DATA_SOURCE_BLOCKED / SCIENTIFIC_INCONCLUSIVE and ECONOMIC_NO_GO, not invented zeros or wins. Future GO requires complete historical as-of trades+reliably marketable quotes or 30+ independent forward days, >=200 actual qualified evaluated entries, positive cluster-bootstrap 95% lower bound and independent fill/cost risk checks. Never merge into MEME006 main pipeline or alter frozen thresholds.
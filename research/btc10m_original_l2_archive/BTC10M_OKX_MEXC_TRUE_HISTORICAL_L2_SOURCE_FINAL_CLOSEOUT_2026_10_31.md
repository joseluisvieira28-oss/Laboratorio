# CRYPTO LAB — BTC10M ORIGINAL OKX SPOT x MEXC FUTURES TRUE HISTORICAL L2 SOURCE FINAL CLOSEOUT, 2026-10-31

**SOURCE PAIR HISTORICAL AUTHORITY NOT VERIFIED, NO HISTORICAL REPLAY, NO 10M EDGE CLAIM, NO REAL ORDERS.**

## What is ACTUALLY required
To historically reconstruct the original frozen Nov 2026 signal (NOT the failed 2025 Binance 3-minute executed taker-buy share proxy):
1. OKX BTC-USDT **SPOT** L2 top 5 timestamped book snapshots;
2. MEXC BTC_USDT **FUTURES/PERP** L2 top 5 timestamped book snapshots on the SAME UTC dates and times;
3. exact three separate paired observations 4–8s apart within each frozen 10-minute signal time; original 0.25 opposite top5 imbalance in all 3 pairs, follow OKX sign, else ABSTAIN;
4. exact reference price and validated +600-second no-lookahead label, plus MEXC Event Futures accepted open price and settlement/contract-specific actual payout if attempting product-specific economics.

Candles, tick trades, MEXC SPOT books, OKX swap books, current L2 endpoint responses or order histories cannot replace the second historical input. MEXC contract-depth amounts are in *contract units*, not BTC by default; absolute book notional in USD needs instrument contract specifications. Within-venue bid/ask ratio may cancel a constant contract-size factor, but don't mistake raw q for BTC. Official current depth API https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-order-book-depth returns CURRENT book version and timestamp; it lacks historical UTC date selection. Last N depth commits https://www.mexc.io/api-docs/futures/market-endpoints/get-the-last-n-depth-snapshots similarly lacks date selection; cannot generate 2025 history from now.

## Verified official historical source and vendor feasibility
- Official OKX historical data https://www.okx.com/en-sg/historical-data explicitly advertises HIGH-RESOLUTION L2 starting March 2023.
- Tardis OKX Spot https://docs.tardis.dev/historical-data-details/okex and https://docs.tardis.dev/downloadable-csv-files advertise free FIRST-DAY-OF-MONTH full L2 snapshot CSV samples without account; historic listed OKX, NOT listed MEXC Futures in their exchange coverage index https://docs.tardis.dev/historical-data-details .
- CryptoStruct https://cryptostruct.com/docs/api and https://cryptostruct.com/pairs/btc-usdt offers true tick L2 per historical instrument/day EUR1 each, but marketing BTC/USDT 'Mexc' does NOT independently establish MEXC perpetual product coverage; searchable vendor market metadata must say perpetual, not spot.
- CryptoHFTData https://www.cryptohftdata.com/datasets/crypto-orderbook-data lists supported markets but no independently verified MEXC BTC_USDT FUTURES exact 2025 source. CoinAPI historic book https://www.coinapi.io/products/market-data-api/docs/rest-api/order-book/orderbooks/symbol_id/history/get requires API key and an exact symbol-specific coverage confirmation; no pay without explicit operator go.

## Original first no-cost source census (immutable)
Freeze commit a03f437f8dfaaffabf5a17526a022a3762ca3884; actual CI https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41234699496, source artifact ID **13054763940**, ZIP sha256 **084ef518c3ce42b5e124e498dd41f2a3a03614d46c5bef7dfe6bcaf856e1570e**. Exactly public CryptoStruct two strict GET searches q=BTCUSDT, venue=okx/class=spot, venue=mexc/class=perp, and one GET /api/samples, returned 200 valid JSON, zero exact instrument results in both. No coverage query. SOURCE_PAIR_IDENTITY_UNPROVEN. Original source NOT subsequently rewritten.
Independent offline immutable original API response audit https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41234783421, artifact 13054893747 ZIP sha256 9919566fc6b8ef82500f13ca55528b98c5668503d6a854e14a7eb98a090b1860. Independently SHA verified original 3 tiny JSON replies; corrected interpretation: official sample wrapper uses FILES, not SAMPLES; 13 free examples had OKX SOL-USD but NO exact OKX BTC-USDT or MEXC BTC_USDT futures free same-day pair. Vendor normalized venue OKEX and class PERPETUAL.

## Independently frozen FINAL broader metadata census V0.2
Separate pre-source freeze commit **ce3256335f2b7f37968c81b2fc7ad2735f7b2cd2**, after V0.1 offline schema inspection and BEFORE any new data:
- exactly GET https://cryptostruct.com/api/search?q=BTC&venue=okx&class=spot
- exactly GET https://cryptostruct.com/api/search?q=BTC&venue=mexc&class=perp
- optional exact /api/instrument/{id}/coverage for both if verified. NO dates/price outcome opened or further source query.
Actual successful GitHub CI https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41234900278, source artifact **13055132914**, ZIP sha256 **3d461ffa5e5bee6a953702f9dd971bcc76a0cc01e15889f0c105c59784e61da5**.
Result: vendor OKX SPOT BTC-USDT identity **VERIFIED instrument_id 240145**, exchange okex, type spot, exact 1 of 25 returned BTC symbols. Vendor MEXC class PERPETUAL q=BTC returned HTTP200 valid JSON but **ZERO INSTRUMENT MATCHES (results=[])**. V0.2 cannot check same-date coverage since MEXC Futures instrument identity not found. Original source result **SOURCE_PAIR_IDENTITY_UNPROVEN**, not NO-MEXC-DATA-IN-WORLD. Both results were obtained without spending, no exchange private APIs, no crypto account or wallet, no live trading.

## Binding decision
NO-GO EXACT HISTORIC BACKTEST YET. Historical OKX first leg documented and instrument identified; historical exact MEXC perpetual L2 second leg NOT independently obtainable from the providers probed under no-cost constraints. Claiming to have tested original OKX/MEXC November order-book model would be source fabrication. Do not substitute MEXC SPOT, Binance candles or OKX perpetual while claiming same science.

Economic point: real MEXC Event Futures payout q varies and must be captured per decision, and real entry/expiry index authority still not independently proved. Even a historic 10m 60% result on a proxy is NOT live trade GO without actual MEXC Event Futures price parity, market acceptance and manual delay cost.

NEXT rational options, without re-tuning frozen rule:
1. Find an independently verifiable archive of **MEXC BTC_USDT PERPETUAL full top5 L2** covering a fixed 2025 date, with time precision, unit schema, price/size, and overlapping UTC dates with OKX; first require one tiny authentic no-cost sample of both original books. Only then preregister historical outcomes study, download original files and compute real paired 10m labels.
2. If this does not exist free, a new distinctly labelled OKX Spot vs OKX Swap historical L2 mechanism could be tested using official OKX public history or Tardis first-of-month snapshots, BUT that is a different market mechanism requiring its own preregistered hypothesis and economic interpretation; do not pretend it proves original OKX vs MEXC.
3. Or collect true future public OKX/MEXC real-time books without funding an account, then observe real 10m outcomes prospectively. This does not solve historical demand.
No new source retries under V0.1/V0.2, no main merge, no account, no paid data, no signals based on missing history. Keep frozen original Nov hypothesis distinct from the killed 2025 Binance taker-flow proxy.
**FINAL VERDICT: REAL OKX SPOT L2 HISTORICAL SOURCE AVAILABLE; MEXC FUTURES HISTORICAL L2 MATCH NOT VERIFIED; ORIGINAL HISTORICAL ECONOMIC EDGE UNKNOWN.**

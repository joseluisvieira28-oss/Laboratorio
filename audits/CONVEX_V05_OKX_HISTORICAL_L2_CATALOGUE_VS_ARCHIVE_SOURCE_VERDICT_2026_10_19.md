# CRYPTO LAB — V05 OKX EXACT-ORIGINAL-ENTRY HISTORICAL L2 SOURCE VERDICT — 19 OCT 2026

## Actual empirical evidence (NOT synthetic)

**Original source freeze before V05 metadata:** `research/convex_okx_l2_v05/PRE_SOURCE_AND_RECONSTRUCTION_FREEZE_2026_10_19.md` committed before 2 frozen public results. Target dates from existing Binance original V5 source receipts (not cherry-picked after OKX access):

- SOL-USDT-SWAP 2023-05-29 16:05:00 UTC (original SOL1h LONG).
- BNB-USDT-SWAP 2023-11-01 16:05:00 UTC (original BNB4h LONG).

**V05 #1 [GitHub Actions 39202147739](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39202147739): SUCCESS engineering and 2/2 public catalogue result presence**. Both calls `GET https://www.okx.com/api/v5/public/market-data-history`, `module=4` (400-level), `instType=SWAP`, `dateAggrType=daily`, exact two original dates, returned HTTP200, API code 0, one `data` record each. Decoded nested response shape:

`data[0].details[0].groupDetails[0].{dateTs,filename,sizeMB,url}`

Both `url` values have HTTPS hostname **static.okx.com**; no authentication, credentials or price data in the sanitized receipts. SHA256 of catalogued response and sanitized path stored in CI artifact. **This is concrete supplier-origin file-link discovery, NOT actual archived book file contents or fully reconstructed order book.**

**V05B #2 [GitHub Actions 39202571193](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39202571193): SUCCESS engineering, SOURCE_BLOCKED economic/scientific.** A separately frozen bounded trial of exact two listed raw archive files returned **HTTP 403 for both**, zero verified archive bytes; current sanitized logging does NOT establish whether the error occurred on the repeated metadata call or on static archive transport. No retries, bypasses, host switching or false substitution; classify `ACCESS_BLOCKED`, not missing historical data, not NO_EDGE. Source/sweep results remain ZERO.

OKX official history page https://www.okx.com/historical-data claims L2 since March 2023. Historical data terms dated 2023-10-26 explicitly allow use for one's own strategy development and prohibit commercial redistribution. Updated API terms also restrict redistribution of public market data. No raw market files are committed or uploaded to GitHub Actions; no raw historical price quotes printed.

## Tested code and immutable scope

- `catalogue_gate.py` probes two exact historical dates, sanitizes schema and link hosts, refuses to call non-public/private endpoints or count catalogue files as real L2.
- `l2_reconstructor.py` is a **pure offline research engine** for T0 causal snapshots/deltas, 400-level restrictions, crossed book, stale and future quotes, missing snapshot, broken sequence proof, LONG ASK and LONG-exit BID hypothetical multi-level sweep. Requires externally verified historical per-SWAP contract `ctVal` and `lotSz` and correct base currency. It CANNOT create actual fills and does not compute net strategy profit.
- `raw_l2_two_archives.py` has strict two-case official archive URI, 190MB compressed cap, 2GB unpacked cap, 10M NDJSON row cap, ephemeral one-file storage and no raw redistribution. Both attempts returned HTTP403.
- `local_archive_importer.py` supports **personal offline files only**, no network, no passwords or keys, SHA256 from provided bytes (NOT vendor signature), chrono checks. Restricted two precise instrument/dates; full local Windows handoff at `research/convex_okx_l2_v05/LOCAL_WINDOWS_PUBLIC_ARCHIVE_HANDOFF_2026_10_19.md`.
- Hermetic CI [GitHub Actions 39202917794](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39202917794) SUCCESS Windows+Ubuntu: **24 synthetic L2/source cases and 4 synthetic offline-importer cases per OS**, NONE actual historical market proof.
- Neither code path opens Binance 2026 protected holdout, accesses an account, places orders, merges to main, touches Windows watchers or renders services.

## Economic implications and next verifiable action

1. Historical source catalogue exists with identifiable original date/symbol filenames and public archive links. The published two-link source block is an operational HTTP403, **not historical source absence**.
2. No actual OKX L2 book has yet been loaded or matched to Binance signal T0. Thus no historic multi-level ASK VWAP, no full-trade executable cost, no verified stop-exit BID price, no funding/taker fees/venue slippage, no signed venue-specific minimum contract quantity, no OOS forward.
3. Operator can download **only** these two exact original public archives from the official OKX Historical Market Data > Order Book (SWAP, 400-level, exact original UTC dates) using their own normal authorized browser if personal-use terms and local region permit. Do not request any login credentials from user; do not upload raw files to public GitHub. Use repo's offline importer and share the **sanitized JSON only**. Or user may report 403/visibility from portal; this is a genuine source barrier requiring data entitlement/license confirmation, not a trading account.
4. Historical `ctVal,ctValCcy,tickSz,lotSz,minSz` must be externally source-verified at the selected 2023 dates (current specs not automatically historical), BEFORE converting original Binance BASE-sized positions to OKX perpetual contract order quantities. Don't run an unsupported raw quote cost analysis.
5. Once genuine 2-date archive source and contract multipliers are proven, freeze extension to ALL historical matched entries and historical gap/stop replay with actual venue funding/fees. Sample of two cannot certify statistical edge.

**FINAL V05 VERDICTS:**
- OKX HISTORICAL 400-LEVEL CATALOGUE DISCOVERY **PASS 2/2 SOURCE LINKS**.
- OKX RAW ARCHIVE CONTENT ACCESS **BLOCKED HTTP403 2/2** (transport stage not isolated in current receipts).
- MONOTONIC/V5 strategy PnL still original *historical only*, no OKX executed book/slippage/stop model.
- Synthetic Windows + Ubuntu 28/28 test contracts each **PASS**; technical proof != economic alpha.
- Live strategy economic proof **NO**; native broker stop ACK **NO**; independent OOS **NO**; **TRADING AUTHORITY NONE / NO LIVE GO**.

Do not lower scientific approval thresholds to recategorize missing data as profitability.

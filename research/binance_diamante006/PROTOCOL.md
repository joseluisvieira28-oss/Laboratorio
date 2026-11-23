# BINANCE-DIAMANTE-006 — SEPARATE HISTORICAL AGGTRADE STUDY AND FREE L2 PROVENANCE GATE
**Immutable experiment registered 2026-11-23 BEFORE any BINANCE006 historical market-data downloads.**
**Read-only, no orders, no keys, no subscriptions, no payments, no main changes.**
Study ID: `BINANCE006-SPOT-AGGTRADE-FLOWONLY-90D-V01`.

## IMPORTANT: scientific separation from BINANCE-004/005
- The frozen BINANCE004/005 primary study is **bid-depth resilience/absorption**. The historical public Binance archive does NOT provide contemporaneous per-level Spot L2 orderbook reconstructions. **Do not** label flow-only results as an exact absorption backtest.
- Keep all BINANCE004/005 thresholds and their prospective observation unchanged; don't read their protected future returns to select parameters. Historical 006 is an independent **flow-only** candidate, NOT a rescue of 004 or the 2025 BTC 10m flow-only NO_EDGE.
- Preliminary previous BTC 10m Spot/perp flow #313 had NO_EDGE. This is a distinct 30-second one-venue Spot sample, still must be compared adversarially. Claims that 006 refutes that previous rejection are forbidden.

## Fixed public data / economic question
Binance's **official** `https://data.binance.vision` monthly Spot `aggTrades` and `1m klines` for BTCUSDT, ETHUSDT, SOLUSDT, exactly **2026-08-01T00:00:00Z to 2026-10-30T00:00:00Z EXCLUSIVE** (90 UTC days). Download exactly months 2026-08, 2026-09 and 2026-10 for each of 3 pairs, ignoring October 30–31 for outcomes and training. One ZIP and companion official `.CHECKSUM` for each (9 aggTrade + 9 kline), from a single whitelisted public data host, no private APIs. **2025+ Spot ZIP timestamps are MICROSECONDS, not milliseconds**; verify UTC rows accordingly.

No historical row may be interpreted as executable bid/ask. Aggregated trades are not independent order-level events or orderflow cancellation; side `isBuyerMaker=true` implies **sell initiated** at a matched print. No L2, maker identity, queue priority, liquidation, spread or real fills.

Economic question, **pre-specified LONG** only: Does sell-initiated aggressive flow alone predict a positive **60-second long return net of conservative proxy costs**, notional 1,000 USDT? Define 30-second UTC grid aligned to Unix epoch. At interval close, if total spot aggTrade notional >= **5,000 USDT** and seller-initiated fraction >= **65%**, trigger hypothetical long on the **first following aggTrade print** within 3 seconds, exit on the **first print** at or after 60 seconds from entry, no later than 3 seconds from target. **120-second cooldown per asset**. Baseline: every fourth valid 30-second bucket unconditional LONG, same holding/fill proxy and per-type cooldown; do not add overlapping baseline and signal trades as independent. Zero trade is 0 cost/0 PnL reference. No long upon aggressive buying, no tuning, additional horizons or stops.

Static print-based counterfactual, **no fills**: gross entry and exit trade prices; base fee **10 bps taker per leg**, adverse slippage **2 bps per leg**; stress fee **10 bps + 5 bps adverse slippage per leg**. Net = `(exit_trade_price/entry_trade_price) × (1-cost_leg)/(1+cost_leg)-1`. **This underestimates real unknown bid/ask crossing and market impact; even a positive print proxy cannot prove executable profitability**. Illustrative 1000 USDT per position, without capital recycling, leverage or compounding. No actual Swiss account tier/eligibility assumed.

## Nonnegotiable chronological split — one preregistered family
- **TRAIN**: 2026-08-01 through 2026-08-30 inclusive (30 UTC days).
- **VALIDATION**: 2026-08-31 through 2026-09-29 inclusive (30 UTC days).
- **TEST untouched until code freeze**: 2026-09-30 through 2026-10-29 inclusive (30 UTC days).
- Cross-split entries/exits are CENSORED rather than borrowing future records from a later split. Partial monthly October ZIP after October 29 is ignored.
- No optimizing thresholds on train or validation in V01. All 3 symbols and both control groups must be shown, no winner-picking. Print-level side/timestamps, UTC coverage, trade IDs, ZIP integrity and 1m kline source coverage checked. If source missing, malformed, ZIP too large or incomplete, `SOURCE_BLOCKED`; no post hoc substitutes.

## Frozen source safety / budget gates
- Before downloading, make anonymous HTTP HEAD requests for all 18 ZIPs, retrieve all 18 tiny official CHECKSUMs, and reject unexpected non-HTTPS/non-Binance hosts and files. **Maximum 900 MB total reported compressed ZIP size** across all 18 files, **single ZIP <=250 MB**, max 25 min runner time; no retries, no paid endpoint or other providers. If size > cap, mark `SOURCE_SIZE_BLOCKED`, do not download all; run must not be described as completed research.
- Stream SHA256 while downloading bounded original ZIP bytes, then compare to official SHA256 CHECKSUM; record URL, actual bytes, checksum, row counts, timestamp bounds, first/last IDs, per-file raw SHA256 and zipped data in manifest; downloaded raw ZIPs may be too big to retain in Actions artifacts; URLs and verified official hashes are replay provenance. Preserve full event-level CSV ledger and small source receipts as Actions artifacts for 60 days. No silent sampled subsets, no partial-day successes.
- Fail if ZIP contains multiple/unexpected members, row malformed, sort chronology regresses, duplicate aggTrade IDs, nanosecond/millisecond rather than 2026 microseconds, gaps in 1m kline per UTC day or contradictory official checksum. Abort without rerun or substitute if platform blocks source.
- HEAD-only L2 **source gate**: probe official public demo documentation and at most 2 genuinely open third-party Spot L2 endpoints via HEAD/small controlled first bytes (Tardis free monthly first day, independent open-licensed HF dataset). Never fetch paid full-book archive, signup/account or request >16 KiB unverified sample. Provider sample ≠ 90-day verified coverage; label `L2_SOURCE_PROSPECTIVE_NEEDS_VALIDATION` until snapshots+diff continuity+license and aligned trades are verified.
- GitHub Actions standard Ubuntu public runner only, repo remains public, no paid runners, no cloud storage subscription, no external payments.

## Statistics and decision protocol
- Source coverage: 90 complete UTC days **per symbol**, 1m kline coverage each day, validated original hash.
- All per-event outcomes and censorship must be archived with as-of decision time, entry/exit print times, price, gross bps, base and stress net bps, split, symbol, and reference fee/slip. Decisions without next print within 3 sec or exit within 3 sec count CENSORED; not removed from validity denominator. No future quote used in decision.
- Report event count/matured/censored, positive net, mean/stdev, per-asset and all assets jointly, per split, baseline comparator. **No GO** unless TEST-only >=200 matured flow events across >=20 days, test stress net mean>0 and fixed-seed (20261123) cluster-bootstrap 95% lower positive (10,000 resamples of whole days), signal mean above baseline and no single UTC day >20% of positive gains. No trade execution GO even if these conditions pass.
- One 90-day retrospective test cannot establish post-selection independence; any putative edge would need a genuinely **new prospective frozen 2026/2027** replication.
- **NO-GO ECONOMIC** if complete valid test with adequate coverage but stressed returns fail. **INCONCLUSIVE** when source, sampling, or statistical gates are insufficient. Historical L2 absorption stays **UNTESTED** unless a free legitimate source's full snapshots/diffs and integrity are independently reproduced.

References: https://github.com/binance/binance-public-data/blob/master/README.md ; https://docs.tardis.dev/downloadable-csv-files ; https://docs.tardis.dev/historical-data-details/binance .

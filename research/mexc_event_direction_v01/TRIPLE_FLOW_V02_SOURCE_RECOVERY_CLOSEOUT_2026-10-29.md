# TRIPLE FLOW V0.2 — BOUNDARY, TRANSPORT AND HISTORICAL RAW SOURCE CLOSEOUT
Date: 2026-10-29. All runs SOURCE-ONLY. No trading, exchange account, MEXC payout/index outcome join, money, private endpoints, or September 2026 holdout access.

## Verdict
**SOURCE_RECOVERY_PARTIAL / RAW_ARCHIVE_PARITY_PASS / LIVE_TRANSPORT_PASS / LIQUIDATION_CAPTURE_CONTINUITY_NOT_CERTIFIED / JOINT_ECONOMICS_NOT_TESTED / NO_LIVE_GO**.
The original frozen V0.1 PR #278 source gate remains **SOURCE_INCOMPLETE**, unmodified. The separate terminal LICP-001 PR #107 remains **NO_EDGE (-16.374554 bps mean base)**, unmodified. Do not interpret V0.2 passes as a V0.1 rescue or as predictive evidence.

## A. Tardis day-boundary semantic reconciliation (new V0.2)
Original Tardis dataset day partition is by the local collector timestamp; 12 already documented book records (six BTC, six ETH) were received within 2026-04-01 UTC while their event timestamps were slightly before the start of that day.
- **V0.2 run [#40895362328](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40895362328)**, head 1a3900699197bdb47aedf1f79a7de0eb5f3b93c4, job 123522870722, artifact 12907031317, digest sha256:04628f3df9e5499b040acda29d43530e07075b91485394ea28bc37890b55a0a5.
- BTC six boundary rows max collector-minus-event lag = **291550 us**; ETH six max lag = **396251 us**. Both inside V0.2's newly predefined 5sec bound.
- The exact V0.1 defect rows, source hashes and failures were kept untouched. This check only read the prior JSON receipt and defect metadata; it did NOT re-download or re-validate the 7,945,015 raw source records.
- V0.2 label: **METADATA_BOUNDARY_RECONCILED_V02**; not V0.1 PASS, not full historical quality PASS.

## B. Live public Bybit transport continuity smoke (95.002s)
Same run #40895362328:
- Exactly six anonymous public topics: BTC/ETH publicTrade, orderbook.50 and allLiquidation. One socket, zero reconnects, zero parse errors and zero book sequence regressions.
- **7 application pings sent, 7 pongs received; subscription acknowledged.**
- BTC: 4,562 book frames, 3,855 trade frames, **1** liquidation child event.
- ETH: 4,643 book frames, 2,095 trade frames, **0** liquidation events observed.
- Both trade and orderbook topics represented in **19/19** five-second buckets. Source-only **PUBLIC_TRANSPORT_WINDOW_PASS**.
- No public liquidation event in a given interval does not establish zero true liquidations, and 95sec healthy live Bybit transport cannot retroactively prove the 2026-04-01 Tardis capture had no gaps.

## C. Raw historical Tardis API sample, corrected parsing
Tardis official HTTP API serves first-day-of-month raw feeds free without login and reports true collector disconnect as *empty lines inside the response*, not a genuinely empty HTTP body.
- Original exploratory [run #40895733587](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40895733587) contained a **parsing bug** which mistakenly counted a genuinely empty response as a disconnect line. That interpretation is RETRACTED, while the raw bytes/hashes remain evidence.
- Corrected [run #40895982459](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40895982459), head eee9fcf0afff66f38120cbfe741f57325f5462a0, artifact 12906697779, digest sha256:fa27fb18fee943faa11c04265b65ee771029ccf0c603646d9fe214fe8586c95d.
- Frozen minute offsets 0,1,360,720,1200,1439: **6/6 GET 200**; one native liquidation message (offset 720); five genuinely empty bodies and **zero actual disconnect markers in these six sample minutes**. Regression assertion ensures empty response => zero markers. This was an access/source probe only, not a full-day census.

## D. Full-day Tardis native liquidation source (all 1,440 UTC minute offsets)
**Authoritative run [#40896404712](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40896404712)**, frozen before first full-day GET; head c058eb06df9947edcd555f50710f6911fcd2934d, job 123526588006, artifact 12907307779, digest sha256:736a010b7afe39887fde2269ccddb7b89f6de9b75ce4c18aafe4d5fc3d5e32ea.
- **1440/1440 public raw minutes readable; 0 HTTP/schema errors.**
- **1,100 native raw messages**, with **1,318 BTC + 1,013 ETH = 2,331** nested liquidation events. This is **EXACT COUNT PARITY** with immutable parent V0.1 normalized CSV totals. This is an independent format/route reconciliation within Tardis, NOT proof of complete original Bybit exchange event feed.
- **1,173 genuinely empty raw minute bodies**. Empty raw body = no messages available from that filtered archive minute; not necessarily healthy zero true liquidations. Never impute zero.
- **6 explicit blank-line collector-disconnect markers**, at minute offsets 480 (08:00 UTC), 481 (08:01 UTC), 626 (10:26 UTC), 910 (15:10 UTC), 934 (15:34 UTC), 1222 (20:22 UTC) on 2026-04-01.
- Marker timestamp is the *minute containing a disconnect marker*, not necessarily the entire outage duration. A bounded exclusion/recovery rule must be frozen separately before any outcome access.
- 267/1440 minutes had nonempty raw payloads (the remainder 1,173 had zero-byte decoded bodies). Six of the empty-message minutes also contained explicit disconnect markers.
- All 1,440 normalized source receipts include minute index, compressed raw SHA256, event counts, genuine empty-line markers and error fields.
- **RAW_DAY_READABLE + RAW_TO_CSV_COUNT_PARITY_PASS**; historical liquidation collector continuity is demonstrably imperfect and whole-day event census NOT certified.

## Scientific consequence
This recovery has produced genuine technical evidence and eliminated an apparent time-boundary inconsistency without source corruption. It **has not** produced a joint signal, return, EV, calibrated probability or edge.
A future distinct forward/source-family freeze may condition solely on **positive observed liquidation events**, exclude all known disconnect and connection recovery windows, demand independently continuous contemporaneous trade+book+liquidation capture with bounded receive-time lag, and compare joint flow versus isolated components on fixed matched decisions. It must not treat empty minutes as certified zero. Before any real Event Futures claim the model additionally needs exact contemporaneous direction-specific payout and shadow-index/real executed-openPrice semantics. The protected Sep2026 holdout is CLOSED; original NO_EDGE studies cannot be rescued by threshold/horizon/cost changes.

No outcomes opened. Main unchanged. No merges, orders, wallets, logins, API keys, private account reads, spending or live trading.

## Provider sources
- https://docs.tardis.dev/downloadable-csv-files
- https://docs.tardis.dev/api/http-api-reference
- https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
- https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
- https://bybit-exchange.github.io/docs/v5/websocket/public/trade

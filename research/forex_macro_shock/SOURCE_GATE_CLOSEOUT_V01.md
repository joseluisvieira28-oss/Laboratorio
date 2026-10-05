# FOREX-MACRO-SHOCK-001 — public/free source gate V0.1

Date: 2026-10-05. Verdict: **SOURCE_BLOCKED** for historical Development/OOS activation. No economic outcomes opened. This is neither NO_EDGE nor a permanent rejection of Forex, and the family is not killed merely because consensus is incomplete.

## Repository reconnaissance and earlier authorities

Read the INDEX NEXT-HANDOFF at 7025bd1cccb7fd002a8f2b16f0f3b3ef6a849858 before creating this branch. Full clone refreshed; 769 remote ref tips searched for FOREX, word-boundary FX, EUR/GBP/JPY/CHF-USDT aliases, macro shock, ECB, BoE, BoJ, SNB, CPI, NFP, consensus and surprise. Matching-history search found 437 commits; exact new family ID appears only in the INDEX handoff. No earlier Forex scientific authority was recovered. Search ledger/hashes are in recon/receipt.json; full inventories are in the accompanying evidence bundle. Source searches did not open new market outcomes; existing closeouts were read for duplication control.

Mandatory News Shock authorities:
- V0.2 robust-controls freeze: descriptive BTC/ETH CPI/NFP study, not a transferable directional edge.
- V0.3 Macro Consensus Source Gate at 908e409732437c549d3cb1d05dd580e5d38bd5db; formal closeout branch head fb1dff5d40ea8b5efbd0a9489e59bf40cb81f670: **D — NO DEFENSIBLE SOURCE IDENTIFIED**. Its 2021 census accepted 0/108 consensus fields and 0/24 complete events; CONSENSUS_PROVENANCE_INCOMPLETE is a source status, not NO_EDGE. Its exact CPI/NFP reopening restriction is preserved; this mission does not reopen it.
- Distinct V0.3A CPI-surprise Discovery closeout: NO_EDGE_STOP; BTC failed the exact frozen p gate, despite ETH passing. Switching BTC to EUR would not justify rescuing that experiment.
- Macro Shock Microstructure V0.1: INSUFFICIENT_SAMPLE, 28 resolved cases versus 30; no continuation claim or favourable NFP-subgroup reuse.
- MACRO-EXPECTATION-VIOLATION-001 at 4d56da2f8991354990598b369a8c3189b09f9708: SOURCE_BLOCKED_NO_AUTHORIZED_INTRAMINUTE_TRADFI_PATH for NQ + 2Y futures, not Forex.
- macro-transmission-v0.1 c3cbdf6a8fd4240cd97224123c3da417d84f3af0 and macro-transmission-001-v01 ba063e7a38d6eb0918ec4ea930767806a5d907e0: daily FRED macro proxies/BTC; not ECB FX intraday dislocation.
- MACRO-POSTRELEASE-FWD-001 at 1b62a83f56223a28b94936b995820748fd7572b8: BLS calendar/actual + BTC/ETH public-index source gate, no consensus; a different instrument/product family.

No STOCK/ETF overshoot baskets, costs-adjusted results, rules or thresholds are transferred.

## MEXC source gate

Fresh public metadata confirms all four contracts. All have quoteCoin=USDT, state=0 and apiAllowed=true; metadata flags do not authorize trading.

| Contract | Base | Contract size | Public metadata indexOrigin |
|---|---|---:|---|
| EUR_USDT | EUR | 1 | BINANCE, MEXC_FUTURE, MEXC |
| GBP_USDT | GBP | 1 | MEXC_FUTURE, KRAKEN |
| JPY_USDT | JPY | 100 | LIGHTER, MEXC_FUTURE, KRAKEN |
| CHF_USDT | CHF | 1 | MEXC_FUTURE, KRAKEN |

EUR metadata openingTime is 1744019880000; the other three openingTime values are 1745571240000, 1745571360000, 1745571480000. These are metadata fields, not historical-coverage guarantees. Official listing notice corroborates GBP/JPY/CHF: [MEXC listing](https://www.mexc.com/announcements/article/initial-futures-listing-gbp-jpy-chf-cad-and-aud-usdt-m-futures-listing-apr-25-2025-17827791523587).

GETs used only public market paths on api.mexc.com: detail, ticker?symbol=, kline/{symbol}, depth/{symbol}, deals/{symbol}, index_price/{symbol}, fair_price/{symbol}. The legacy contract.mexc.com public K-line route was also checked without authentication. [Public API documentation](https://www.mexc.com/api-docs/futures/market-endpoints) states market endpoints require no authentication.

All four corrected ticker requests passed; public books, recent trades (100 rows each), index and fair-price payloads were accessible. Current snapshots validate source routes only, not macro-event execution quality. No historical full books or event-time bid/ask archive was proven. Recent-trades endpoint is capped at 100; it is not a historical trade corpus.

Historical source probes inspected timestamps/schema only on burned, non-target source dates. All four contracts had 60/60 requested minute timestamps on 2026-10-02 (61 returned including the end boundary). All four returned zero rows on 2025-04-29 and 2026-07-07. Additional EUR checks returned zero on 2026-07-08, 2026-08-04, 2026-09-01. EUR had 61 timestamps on 2026-09-08, 09 and 16. April 2025 remained empty with end-only query, Min5 and legacy public domain. Responses were HTTP 200 / success=true with empty time arrays: not a price-outcome failure and not a 2000-row pagination issue. [K-line docs](https://www.mexc.com/api-docs/futures/market-endpoints/get-candlestick-data) specify seconds and segmented requests; these requests were already narrow. No documented global retention duration or exact first-ever accessible timestamp is inferred from these sparse probes.

This evidence cannot establish the proposed historical Development corpus. Do not shrink the periods to September's convenient surviving history or treat missing candles as zero returns. No target event-window K-lines were fetched.

## External FX gate

Dukascopy's datafeed subdomain returned 503 for the initial 8 requests; the same provider's www.dukascopy.com datafeed route succeeded. This is an outcome-blind access repair, not a performance-driven source replacement.

EURUSD hourly tick files: 3,051 records on 2025-04-29 and 2,081 on 2026-10-02. The April daily file had 106,873 records. Recent GBPUSD/USDJPY/USDCHF probes had 2,763/7,817/3,369 records. Source-only validators found monotonic timestamps and positive uncrossed quotes. EUR hourly maximum intertick gaps were 28.863/35.826 seconds; daily maximum gap 60.232 seconds. These are probe statistics, not guarantees for every event.

[Dukascopy methodology](https://www.dukascopy.com/wiki/en/development/data-export/) describes LZMA .bi5, 20-byte big-endian records, bid/ask and UTC offsets. Hour files require offsets from the named UTC hour; daily files require offsets from midnight. Price scale is 100000 for EUR/GBP/USDCHF and 1000 for USDJPY. Resolution is irregular ticks with millisecond timestamps, not a guaranteed millisecond refresh. The broker feed is an independent FX reference, not consolidated global FX or an executable MEXC price. Event coverage, gaps, publication latency and availability-at-decision-time require separate checks before any signal authority.

HistData public free ASCII tick ZIP for EURUSD April 2025 downloaded successfully. Only 2025-04-29 timestamp capability was inspected (106,410 records); the month ZIP is preserved as an opaque source artifact, not an opened event-price sample. [HistData FAQ](https://www.histdata.com/f-a-q/) specifies fixed EST UTC-5 without DST, bid-based M1 and ask only in Generic ASCII tick data; it provides gap information and no reliability warranty. Corpus origin/quote methodology and immutable vintages are less explicit than Dukascopy. HistData is secondary validation only in this gate, not a silently selected substitute. No claim of matching tick counts between providers.

Quote identity matters: MEXC EUR/GBP/JPY/CHF-USDT is not a USD spot pair. JPY/CHF require reciprocal bid/ask mapping: target bid=1/reference ask and target ask=1/reference bid. USDT/USD also requires an independent bridge. A public Coinbase USDT-USD 60-second historical request on the burned April date returned 61 rows with exact timestamps. This is capability evidence only: missing buckets, bid/ask execution and full corpus coverage remain unproven. Never assume USDT=USD or treat MEXC index as the independent reference.

## Macro and consensus provenance

Official authorities reviewed and raw documentation preserved:
- EUR: [ECB decisions](https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html), official release clock 14:15 European local time; use Europe/Berlin with date-specific DST, not a fixed CET offset. Original website label is retained. April/June 2025 source examples therefore map 14:15 local to 12:15 UTC. Scheduled time is not independently measured publication-arrival time. April 17 release has date-only published_time; publication-instant evidence is not fabricated.
- GBP: [BoE policy](https://www.bankofengland.co.uk/monetary-policy), announcement at 12 noon Europe/London, with BST/GMT conversion.
- JPY: [BoJ release calendar](https://www.boj.or.jp/en/about/calendar/index.htm), policy statement clock may be undecided. Do not assign an arbitrary fixed T0; release-instant evidence is required. Asia/Tokyo has UTC+9.
- CHF: [SNB process](https://www.snb.ch/en/publications/communication/speeches/2025/ref_20251121_msl), press release at 09:30 Europe/Zurich, separate from 10:00 remarks, with DST conversion.
- US CPI/NFP/FOMC are not included in this candidate; BLS/Fed remain first-release authorities if a separately frozen extension is ever made.

No complete event corpus was accepted. Two ECB source examples identify published decisions without opening FX outcomes: 17 April 2025 deposit rate lowered 25 bps to 2.25%, effective 23 April; 5 June lowered 25 bps to 2.00%, effective 11 June. Prior values are arithmetically implied by the release's stated change (2.50%, 2.25%), explicitly derived rather than claimed as separately archived prior-state evidence. Current official releases retrieved in 2026 do not by themselves prove absence of subsequent edits. No rate surprise or directional label was computed.

Required future event schema: event ID, official URL/hash, scheduled local clock and IANA zone, scheduled UTC, independently proven actual publication timestamp (nullable), previous policy/value with its own pre-T0 evidence, first published decision/value, effective date separate from publication, revisions known at T0 only, version status, missing reason. No current revised series substitution.

Consensus status: **CONSENSUS_PROVENANCE_INCOMPLETE** for a usable field-complete Forex sample. Timestamped Reuters poll leads can be investigated field by field, but search snippets/current mirrors are not accepted pre-T0 vintage proof. [ECB SMA publication methodology](https://www.ecb.europa.eu/pub/pdf/ecbu/eb202108.en.pdf) describes aggregate results published after the Governing Council meeting; a premeeting survey collection date does not prove public availability before the decision. SPF quarterly forecasts are not automatically a meeting-specific rate consensus. No absence-of-all-possible-public-sources claim is made, and old News Shock reopening requirements are unchanged.

## Hypothesis review before market outcomes

| Mechanism | Disposition |
|---|---|
| A MACRO-SURPRISE-DIRECTION | Not activated: no field-complete, auditable pre-T0 consensus corpus. No BTC-to-EUR resurrection of the closed surprise hypothesis. |
| B POLICY-DECISION-DISLOCATION | Preferred conditional mechanism: official announcements may create transient quote-adjusted divergence between MEXC and independent FX, without a surprise label. EUR/ECB chosen for documentary clock and direct EURUSD reference, not returns. Historical activation blocked by MEXC coverage. |
| C CROSS-VENUE-REACTION-LAG | Distinct possible timing mechanism; historical MEXC coverage missing, and a retrospective FX archive does not prove live availability at decision time. Not activated. |
| D POST-SHOCK-MICROSTRUCTURE | Not activated historically: current public books/recent trades cannot reconstruct past event spread/depth/fills. A future study needs a separate prospective source/collector authority. |

B is a mechanism choice for the next source-gate continuation, not a tradable signal or a completed preregistration. No threshold, horizon, minimum N, statistical grid, executable model or PASS criterion was selected from prices. No scientific freeze is created while mandatory inputs are missing.

## Scope, results, costs and final gate

Proposed outcome-blind source assessment: Development 2025-04-07 through 2025-12-31; OOS 2026-01-01 through 2026-10-04. These proposals were not activated or frozen for economic evaluation. All target market outcomes remain closed; no holdout period/sample was used to design parameters.

Events evaluated economically: **0**. Complete accepted event records: **0**. Source-only ECB examples: **2**. Gross, net, win rate, p-value and event cost estimates: **not computed**. Source availability is not an edge result.

Current standard API cost evidence: [MEXC fee notice](https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742), effective 1 June 2026, maker 0.06% and taker 0.08% per side; hypothetical taker/taker 16 bps round trip before spread/slippage. No fee paid, no zero-fee assumption, no historical fee schedule retroactively fabricated; a future freeze must state whether costs model current deployability or historical realized schedules.

Primary blocker: public MEXC historical coverage needed for the proposed Development/OOS is not established. Additional unpassed requirements: full event first-release/publication provenance, event-aligned FX/USDT bridge coverage, historical executable-book evidence if required, real-time external data availability if a prospective decision rule is chosen. Consensus blocks A specifically, not B/C/D by itself.

Next legitimate gate: prove a public/free auditable historical MEXC source spanning the intended periods, or separately design and validate a future-only source path. Then commit a full pre-outcome freeze covering all required definitions/statistical gates before any event-price analysis. Do not substitute providers, change windows, lower gates, or claim missing evidence is NO_EDGE. No scheduler or outcome runner is armed.

## Technical corrections and evidence limits

Fixed the initial ticker probe URL (/ticker?symbol= rather than /ticker/{symbol}); used the same Dukascopy provider's working www route; repaired ECB TLS verification with a trusted CA bundle, without disabling certificate checks. Raw storage now uses content hashes to prevent label-based overwrites.

During the TLS documentation retry four preliminary web-document snapshots were overwritten; their original hashes are retained and those records explicitly withdrawn, not represented as preserved bytes. All market-source raw records remain preserved. Corrected documentation captures govern source statements; no event outcomes or scientific parameters were affected. PROVENANCE_REPAIR_RECEIPT_V01.json records this limitation.

Raw source bytes, timestamps, headers and SHA-256 evidence are preserved in the accompanying local evidence bundle; 86 raw request references verified at packaging. Git stores source tooling, compact receipts and the bundle fingerprint rather than redistributing the full raw market/doc archive. The full recon inventories are in the same bundle. Retrieval scripts make public source requests only; source availability can change, so replay is not guaranteed to yield identical current snapshots.

No main merge, login, private APIs, account reads, positions, balances, orders, wallets, spending or live trading. Verdict remains **SOURCE_BLOCKED**; scientific mechanism untested.


# SOURCE RELIABILITY V2.1 - terminal verdict

**SOURCE_BLOCKED / ECONOMIC_INSUFFICIENT / NO_LIVE_GO.** No forward multi-day recommendation.

One new real public bounded capture completed. Independent ZIP audit reconstructed every receipt, source validation, causal coverage grid and signal and matched the capture report. This verification is evidence integrity, not a source-quality PASS. The frozen 95% joint-coverage gate FAILED: 92.861111%.

Prospective protocol and collector published at 30f44e38affe502f24d820acafaeb880cd12406e before new data, after local freezes 13793ac/e82c383. Parent #335 exact b7bf960cd8c7b45956fc7548198a44d7c9b7d28b unchanged. New draft #336, independent branch stacked on #335; #333, prior protocols, original pilot and protected holdouts untouched. Only this new research directory and its offline CI workflow changed. No main merge.

## Actual window and budget

UTC: 2026-11-04T21:30:29.850000+00:00 to 2026-11-04T23:30:30.225000+00:00. Europe/Paris: 2026-11-04T22:30:29.850000+01:00 to 2026-11-05T00:30:30.225000+01:00. Monotonic recorded span 7200.250s; capture/close/hash completion 7200.656s, within 7250s process allowance. Collection stopped on the frozen 7200s deadline; subsecond close/receipt/hash overhead disclosed. No extension, follow-on capture or recurring schedule.

Raw 102,770,595 bytes (cap 384 MiB); gzip 13,033,838 bytes (cap 128 MiB); ZIP 13,067,043 bytes. Evidence storage remains below 512 MiB including ZIP/raw copies. Local public websockets only. Repository public status verified; GitHub standard Ubuntu/Windows runners only, no larger runners, no Actions artifact/cache uploads, no paid infrastructure. [GitHub billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions) confirms public standard runners remain free. CI budget: only initial and final two-job runs, timeout 5 minutes/job, maximum 20 unweighted runner minutes.

## Coverage and failure attribution

| Measure | Actual | Frozen gate |
|---|---:|---:|
| Causal grid seconds | 7200 | >=7200 |
| Joint-good seconds | 6686 | >=95% |
| Joint-good fraction | 92.861111% | **FAILED 95%** |
| Good full minutes (>=57/60 good seconds) | 101 | >=100 |
| Bad seconds, including quarantine | 514 | never filled |
| Initial Bybit connection failures | 1 | <=8 total |
| MEXC disconnects | 0 | disclosed |
| Stale-book resets | 22 | 30s quarantine each |
| Parse/clock/receipt-integrity violations | 0 | zero integrity violations |

All 22 stale resets on the one-second grid were attributable to Bybit book freshness >1000ms, not MEXC disconnects. Bybit had 71 consecutive-book receive gaps >1s, maximum 2.609s; MEXC had 24 such gaps, maximum 1.250s. Not every receive gap crosses a one-second grid boundary; 22 reset triggers therefore differ from 95 raw gaps. Repeated resets can overlap quarantine. The audit enumerates all 15 bad intervals, all reset triggers and the failed connection receipt. No gap was interpolated or zero-filled. 6686 good seconds equal 111.433 good-second-equivalent minutes; this differs from 101 full minutes meeting the 57/60 rule.

Bybit initial connection reset at +0.531s (WinError 10054, before successful handshake); retry and re-subscription succeeded at +2.046s. MEXC connected once at +0.796s. Bybit 478 pings/478 pongs; MEXC 476 pings/475 pongs (last outstanding ping at bounded stop is not a pong-timeout). Maximum inter-ping interval: Bybit 15.687s, MEXC 15.750s. No retry exhaustion. MEXC recovery from a new actual disconnect was not exercised in this window; no claim that every failure mode is solved.

## MEXC 1005 and current protocol

Original pilot raw SHA256 reverified unchanged: eb86dd41c9bdb87c84c66c8206dcb102139b5da3e38ea7ef58765add5e93f7e3. Original parser incorrectly expected data.timestamp; original error report and corrected envelope-ts audit remain separate in #335. Current actual subscription ACK is rs.sub.depth.full with data=success; full depth arrives as push.depth.full with envelope ts. No incremental-depth reconstruction or historical request.

[WebSocket RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455#section-7.1.5) defines 1005 as absence of a supplied close status; it is reserved and not a server diagnostic code transmitted on wire. The old collector sent application ping only after a 10s receive timeout: continuously active market traffic prevented that branch. [MEXC documentation](https://mexcdevelop.github.io/apidocs/contract_v1_en/) requires application ping independently of traffic and disconnects after about a minute without it. The original close arrived 65.847s after first MEXC WebSocket receipt. Heartbeat starvation is therefore a supported mechanism/implementation defect, not definitive server-side root-cause attribution. Independent 15s application heartbeat avoided recurrence in this two-hour observation.

Implementation includes bounded retry/backoff, re-subscription on each segment, global window invalidation, mandatory warm-up, full-book validation, source timestamp bounds, receipt sequence and clock checks, per-segment versions and session-wide event deduplication. Receive-order detector and one-second coverage grid use no future rows. Windows clocks have 15.625ms resolution despite nanosecond integer representation. No nanosecond-accuracy claim.

## Economically relevant comparison

| Measure | Original #335 pilot | V2.1 new public window |
|---|---:|---:|
| Runtime | 180.234s | 7200.250s |
| Valid Bybit book snapshots | 3895 | 163058 |
| Bybit executed trade children | 3394 | 106577 |
| Valid MEXC full books | 230 | 24132 |
| Observed unique liquidation children | 0 | 112 |
| Independent threshold burst episodes | 0 | 1 |
| Qualified decisions/observations | 0 | 1 observation |
| Economic PnL assessment | none | none |

Observed rates per gross two-hour window: 56 liquidation children/hour; 0.5 independent qualifying-threshold episode/hour; 0.5 qualified observation/hour. These are observed BTCUSDT feed reports, not a complete exchange liquidation census or a stable event-rate estimate. Exact (T,s,S,v,p) deduplication may undercount indistinguishable children. Bybit liquidation price is a bankruptcy proxy, not a certified execution price.

The single Sell-position-side episode occurred at 2026-11-04T22:35:03.699000+00:00 (+3873.781s): 19 unique children, 105110.8554 USDT bankruptcy-notional proxy, qualifying sell aggressor flow and joint-good source state. It is an observational short-side signal under frozen thresholds; not an order, entry or successful trade. The audit found 1061 overlapping raw burst-frame windows belonging to the same cooldown-separated episode; these MUST NOT be counted as 1061 independent opportunities.

No simulated fills, fees, returns, win rate, Sharpe or PnL computed. BASE/STRESS assumptions and parent 60-completion/14-date economic gate remain unchanged and unassessed. Source observation does not satisfy that gate. No profitability claim and no NO_EDGE conclusion. V2.1 differs from parent paper execution: it observes source-valid thresholds and consumes cooldown for blocked bursts; counts are not inherited paper fills.

Forward recommendation fails both source quality (92.861111% <95%) and independent episode count (1<2). A qualified signal does not override either gate. No multi-day collection authorized or scheduled by this result.

## Reproduction and custody

232700 raw receipts, SHA256 verified independently from ZIP before reconstruction. Compressed raw and exact original report/manifest retained in the ZIP. Auditor is separate standard-library code with no collector import or network access; fixtures are separate synthetic tests. Source/protocol byte hashes match the pre-data GitHub freeze. Original pilot and parent protocol remain byte-identical.

- Raw SHA256: bf3c33ea0657f4b43fe0a2b5ebd57517022a16a6a9734846f18f06f0e1eba2a1
- Gzip SHA256: b3d9ffa9b423c8de5fc70a8af554989ac4eb60afa41acb8c3afd501abda258c4
- ZIP SHA256: 27f85b9c3db362820370c68313893739276fad5bea093f894e4ff060b4789dd2
- Protocol SHA256: 6be726411e366622bf12fa6b8c496f7dc9dedb0f5bf2d2dfee55cfaa188736c5
- Collector SHA256: fb1be4af559401d77ffd2654a749b51020970f68d4a20bd4517338a9f72a22f9

See README.md for offline commands, INDEPENDENT_AUDIT.json for interval/segment details and GATE_RECEIPT.json for gate arithmetic. Initial Windows/Ubuntu CI run 41916644410 passed 14 adversarial source tests per OS, actual checkout 26e1deff48d48b8e84c65809eab0a689ead92bab (merge of frozen 30f44e3 into parent b7bf960). Final bounded CI adds independent ZIP reconstruction/tamper tests and audits the actual public ZIP on each OS; its terminal run is linked from PR #336. Technical tests do not count as economic episodes.

No orders, exchange keys/accounts/private APIs, live arming, recurring schedule, protected-study changes or main merge. Authority for the one new capture is consumed; no rerun or longer window under this protocol.

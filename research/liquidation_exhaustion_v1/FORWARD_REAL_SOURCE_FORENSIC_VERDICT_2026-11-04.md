# Liquidation Exhaustion V1 — forward source forensic / next verdict
Date: 2026-11-04 UTC. Research only, NO trading, no economic returns opened.

## Authoritative REAL run and archive
- GitHub Actions source-only run **#41861306212**: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41861306212
- Source SHA/commit: `800f7b1882235c8eb7e83cf7464e561c70b988d1`; PR #332. First attempt run #41858738136 failed its synthetic test and did not collect; it must not be pooled.
- Run #2 180.007 seconds, 12/12 pongs, zero socket disconnects, zero source errors. Collection and artifact upload succeeded. The attempted GitHub PR comment failed **Resource not accessible by integration**, despite the job step being marked success by `continue-on-error`. This is reporting/permissions, not market data failure. An independent GitHub API `actions/runs` query recovered the push run; `fetch_commit_workflow_runs` only exposed PR-triggered runs.
- Genuine GitHub artifact **#13340661055**, `liquidation-exhaustion-v1-public-source-raw`, containing `raw_public_frames.ndjson` and `source_receipt.json`.
- Original ZIP SHA256 **522ebfb68bef0f27cb7cdfbf400fc5cfeb3e603ba3576d6eff88889daadb6b51**; matches GitHub artifact digest.
- Raw frame file SHA256 **28f5d1734be719482bc427f77ec65957cfcd187aff06b872618b00579d2c5898**, matching receipt. This hash is of uncompressed raw-public-frames NDJSON.
- 28,889 captured received raw frames; non-market heartbeat/subscription messages are counted separately from topic data.

## Independent replay findings, computed from raw bytes (not just receipt)
| Topic | Native messages |
|---|---:|
| BTC orderbook.50 | 8,867 |
| ETH orderbook.50 | 8,936 |
| BTC publicTrade | 7,184 |
| ETH publicTrade | 3,877 |
| BTC allLiquidation | 9 |
| ETH allLiquidation | 3 |

- **12 witnessed positive liquidation child events** (9 BTC and 3 ETH). All 12 occurred with an earlier-received, non-crossed BBO and an earlier-received trade for the same symbol.
- Both orderbooks start with one complete native snapshot and replay without crossed best bid/ask, update-ID regressions, or sequence regressions. **BTC: 8,866/8,866 deltas with `u` increment +1; ETH: 8,935/8,935 +1**. 0 received timestamp regressions.
- For each of 12 liquidation events, nearest **previously received** book was between **0 and 21ms** old; nearest previously received trade was at most **193ms** old. These are as-of-*receive* checks, not future-execution or prediction tests.
- Observed liquidation child exchange-timestamp-to-local-receive lag = **124–562ms**. Max book source-lag from exchange envelope `ts` = **536ms BTC, 480ms ETH** (startup snapshots), and trade lag max **316ms BTC, 295ms ETH**. No negative observed child lag.
- Public liquidation `p` is not an executable entry quote. Only reconstructed BBO could serve as a source-side quote, and source-side BBO is *not* automatically execution-venue MEXC BBO.
- No return, trade PnL, mean outcome, performance claim, exit fill, future candle, financing or edge calculation was performed.

## Adversarial limitations — must not overclaim
1. A complete observed sequence of orderbook update IDs and zero disconnects in **this 180-second session** does not establish the exchange published every underlying forced liquidation; liquidation stream has no analogous gap-free market-wide event counter.
2. Only one bounded 3-minute positive-event sample, **12 child events not 12 independent cascades**. Some events may overlap into one episode under any frozen de-duplication rule.
3. BTC/ETH Bybit BBO is not MEXC executable BBO. Need the user's actual accessible venue, signed trade route, fees, spreads and realistic manual delay.
4. `SOURCE_PARTIAL_POSITIVE_EVENT_OBSERVED` is the original collector receipt status; independent replayer supports **SOURCE_WINDOW_TECHNICAL_PASS_WITH_CENSUS_LIMITATION**, not full `SOURCE_CENSUS_CERTIFIED`.
5. Old 2026-04-01 Tardis archive PR #279 with six disconnections remains blocked for whole-day source continuity; do not retroactively relabel it PASS.
6. Original LICP-001 continuation PR #107 remains NO_EDGE (-16.374554 bps under its frozen base cost assumption); no reversing its known outcomes to rescue the experiment.

## Binding verdict on 2026-11-04
**FORWARD_SOURCE_WINDOW_TECHNICAL_PASS / LIQUIDATION_POSITIVE_OBSERVED / FULL_CENSUS_UNPROVEN / ECONOMICS_NOT_TESTED / NO_LIVE_GO**.

This clears the specific operational blocker "cannot obtain any positive liquidation events with co-timed as-of trade/book" **for this one source-window**, but does NOT clear the full economic/source gate. Next only: freeze an independent executable entry rule, latency (5/15/30s), fees, de-duplication, primary holding horizon and sample-size/power gate *before* collecting future outcome observations. Then prospectively capture independent events over multiple dates, with execution-venue BBO and continuity. Do not optimize on these 12 already observed events; treat them as **source qualification only**. No more duplicate automatic source runs, paid API, accounts, orders, Live GO, protected old holdout or main merge.

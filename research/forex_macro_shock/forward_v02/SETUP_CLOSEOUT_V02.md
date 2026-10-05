# FOREX EUR/ECB V0.2 setup closeout — 2026-10-05

**Current verdict: OPERATIONALLY_BLOCKED.** Historical V0.1 remains SOURCE_BLOCKED; hypothesis untested. No economic outcome was opened, no live order/account/private API, no main merge, no spending or deployment.

| Required field | Verified result |
|---|---|
| Branch | forex-ecb-eurusdt-v0.2-forward-setup-2026-10-05 |
| Base HEAD | 94813ec386d0a94579eaab38ce2b0fa5fd4d7bdd |
| Method freeze commit | 48b1ad63c13e1fcaa568b8996d9886878bec3798 |
| Capture code commit | eddeea4b3b20011233fe6177e6f3834dc77c714c |
| Candidate | FOREX-ECB-EURUSDT-DISLOCATION-FWD-001 |
| MEXC source | api.mexc.com public routes return HTTP 200 HTML Site Unavailable, not JSON; schema fails closed. No feed health claimed. |
| Binance source | api.binance.com metadata probe returned HTTP 451. Official market-data-only data-api.binance.vision returned EURUSDT EUR/USDT TRADING metadata, 100-level bid/ask books and 100 recent trades. Same venue/product, selected before outcomes; no authentication/proxy/location manipulation. |
| ECB | Official calendar/index fetched and archived. Generic index capture implemented; semantic target-release watcher remains unimplemented/unqualified. |
| Sampling | Bounded concurrent REST source sampler, >=5s requested between batches; realized cycles slower because RTT. It is not the required 1s event feed. |
| Book RTT median/max | MEXC 8459.119/9277.898 ms; Binance 5563.136/7792.609 ms. Small technical sample only; not feed-latency guarantees. |
| ECB index RTT median/max | 6900.285/8846.063 ms; exceeds watcher target. |
| Persistence | SQLite WAL + synchronous FULL; raw bytes content-addressed in transaction; 33 persisted request receipts, PASS chain verification. |
| Restart | 20 receipts after initial two cycles, 33 after fresh-process restart on same database; continuous chain verified. |
| Deduplication | Raw content hashes and persisted book update identities; synthetic repeat/restart and conflict tests passed. Live sequence continuity is not implemented by this REST sampler. |
| Scheduler/runtime | Two bounded runs completed; no continuously running process, schedule, paid VPS or Render. Actions not represented as tick collector. |
| Fee model | 8bps each side on actual fill notionals; nominal 16bps round trip, plus 2bps fixed slippage and executable book spread/depth. No fees incurred. |
| Threshold | Fixed median basis, nearest-rank 99.5% absolute deviation; max(noise,16+median MEXC spread+2). No numerical calibration accepted. |
| Freeze path | research/forex_macro_shock/forward_v02/PRE_OUTCOME_METHOD_FREEZE_V02.json; complete prospective method, activation locked. |
| Tests | 15/15 pass, including actual subprocess crash before transaction commit, restart, persistent dedup, corruption, concurrency lease and protected-event request lock. Synthetic prices only. |
| Evidence chain head | 5109a7590d0040d3abb9ea4a2980636f686160446439090176b9a8616a9de2d0 |
| Next protected event | 2026-10-29, scheduled 14:15 Europe/Berlin = 13:15 UTC; T0 must be actual local first-seen substantive official release. |
| Outcomes opened / events evaluated | 0 / 0 |
| Qualified calibration grids / days | 0 / 0; short REST smoke tests do not qualify as economic burn-in. |
| Gross / net / notional results | Undefined; none computed from real observations. |
| Next gate | Source/runtime qualification, semantic watcher, five-day burn-in, then immutable calibration/activation receipt before 26 Oct UTC. |

## Reconciliation with earlier discussion

Read the parent charter, source closeout/tooling, and INDEX reconciliation/NEXT-HANDOFF. Earlier macro authorities/restrictions are inherited explicitly from the parent closeout: News Shock V0.2 descriptive; V0.3 consensus SOURCE_BLOCKED/no defensible source; V0.3A NO_EDGE_STOP; microstructure insufficient sample; MEV/macro transmission/postrelease distinct instruments. No old study reopened; no STOCK/ETF/index outcomes transferred. The full historical branch reconnaissance was performed by V0.1, not repeated or claimed newly performed here. Selected recursive tree contains no AGENTS.md.

The conceptual horizon/quantile/cost suggestions are now an explicit future-only method commit. Direction fades contemporaneous basis, not inferred macro surprise. Only 25 USDT/60s is primary; 10/50/100 are descriptive. First eight source-valid scheduled events of the ten fixed ECB dates form one event-level sign-flip analysis, with eligible no-signal events counted as zero. No interim PASS, no tick-count inflation, no hindsight event selection. Positive research result would not authorize live trading.

Spot bookTicker documentation has update identity but no E/T clock; REST depth likewise lacks exchange timestamp. Polling server time does not create missing quote timestamps. Required timestamped diff-depth plus documented U/u sequence/bootstrap is not implemented/qualified, and local arrival skew cannot be called exchange reaction lag. MEXC index/fair are diagnostics only and not independent venues.

## Technical changes and remaining blockers

Implemented raw transactional persistence, durable receipt chain, restart verification, single-instance lease, duplicate/conflict protection, positive uncrossed ordered book validation, no credential/private endpoint path, redirect rejection, TLS verification and hard setup stop on 23 Oct UTC. Frozen pure signal/quantity/VWAP/net/statistical functions are synthetic-testable, but are not connected to a live economic runner.

After the capture-code commit, extended the collector lease from 60 to 180 seconds and bounded intervals at 5..30 seconds, so a long source request cycle plus sleep cannot expire the intended single-instance lease. The two capture runs used the preceding 60-second implementation; final code/tests use 180 seconds. This repair changes no science or captured observation.

Blockers: current MEXC access in this environment; multi-second request latency; absent qualified timestamped stream runtime; absent semantic release detector; no persistent continuous operator process; no accepted five-day calibration. No bypass, source replacement or artificially lower timing gate was used. A live runtime must be qualified, not inferred from this package being downloadable. If it cannot qualify, the event remains locked.

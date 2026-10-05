# FOREX EUR/ECB V0.2.1 — implementation and public runtime audit

Date: 2026-10-05. **Current verdict: OPERATIONALLY_BLOCKED.**
Historical V0.1 remains **SOURCE_BLOCKED**, scientific mechanism untested.
Public access/transport blockers were partly resolved; this does not arm the
forward, open economic outcomes or establish edge.

## Required operator report

| Field | Verified result |
|---|---|
| Branch | `forex-ecb-eurusdt-v0.2-forward-setup-2026-10-05` |
| Prior published HEAD | `6d9da37747c7da8828310cf47028c57d64057979` |
| Final tested implementation/capture HEAD | `99b1b12f1e4422f7fd028c82b45f2bee718ca903`; final documentation/package commit reported separately by the operator response |
| Candidate | `FOREX-ECB-EURUSDT-DISLOCATION-FWD-001` |
| Authority | V0.2 complete method freeze, commit `48b1ad63c13e1fcaa568b8996d9886878bec3798`; activation locked |
| Freeze path | `research/forex_macro_shock/forward_v02/PRE_OUTCOME_METHOD_FREEZE_V02.json` |
| Freeze SHA-256 | `6ea83bed921ce8f65c2e4bfd3af0af35be39de733074c2b0350b0f6a1ab0c2d4`, unchanged across all three CI captures |
| Real instruments/references | MEXC `EUR_USDT` perpetual / Binance `EURUSDT` Spot. MEXC contractSize/minVol/volUnit=1; metadata EUR/USDT identity/state verified. No NAS100/SP500, stocks/ETF or synthetic index reuse. |
| MEXC source status | Local REST returns Site Unavailable HTML and WS handshake HTTP 200 instead of upgrade. Standard public GitHub Linux runner successfully established timestamped MEXC WS and reconstructed the book. Current local restriction is not universal source absence. |
| Binance source status | Official public market-data-only REST/WS accessible. Timestamped `depthUpdate` with E/U/u verified; bootstrap/continuity implemented. Spot bookTicker/REST book alone are never treated as timestamped quotes. |
| ECB watcher | Semantic release URL/date/title/policy and placeholder checks implemented; raw hash and first-seen persistence tested. Actual 29 Oct release unavailable yet. Setup minute polling is not the frozen 1s event watcher; event mode remains locked. |
| Sampling mechanism | Concurrent WS source streams, fresh REST bootstrap after gap/reconnect, per-second UTC grids, metadata and server clocks. Unmerged MEXC versions require +1 continuity and `data.cts`; root ts is diagnostic. No historical reconstruction/backfill of missed grids. |
| Latency | Final CI Binance applied-delta age median 79ms, max 99ms, n=129. Initial final-run clock RTT: Binance 159.37ms / MEXC 163.16ms, valid. Later MEXC probe RTT 479.26ms and offset 163.5ms implies uncertainty bound 403.13ms; correctly rejected by the 250ms frozen clock gate. Schema timing flag alone is not qualification. |
| Persistence | Transactional raw byte archive and durable hash chain. Final CI 4,414 receipts, complete downloaded ZIP SHA verified and chain reverified locally. Separate CI archives remain separate, not silently pooled into a calibration sample. |
| Restart recovery | Local fresh-process continuation grew 234 to 317 receipts without breaking chain. Crash rollback, restart hash validation, persistent first-seen release and single-instance lease tested. Feed state is rebootstraped rather than retrospectively replayed as live evidence. |
| Deduplication | Raw content dedup/persisted receipt identities; WS duplicate/conflict/ordering tests; live restart starts from a fresh sequence-proven bootstrap. No event signal dedup is claimed for an unarmed economic runner. |
| Runtime/scheduler | Three bounded GitHub source runs completed successfully. No process remains active between them. Portable foreground operator supervisor and Windows launcher supplied. It starts the next full weekday, warms at 09:58 UTC and records 10:00–16:00 UTC; no intentional hourly restart gaps. No paid VPS/Render or scheduled GitHub collector claimed. |
| Fee model | Frozen 8bps per side on actual fill notionals, nominal 16bps round trip; 2bps fixed slippage plus real book-side spread/depth. No fees paid; no account reads or cost optimization. |
| Threshold | Frozen median basis and nearest-rank 99.5% absolute noise; max(noise,16+median MEXC spread+2). No real calibration values accepted, no strategy PnL computed from burn-in. |
| Tests | 32/32 local and final GitHub tests PASS; meaningful sequence/gap, missing/reversed timestamp, bootstrap, crash/lease, first-seen restart, semantic publication, redirect/private URL, calibration lock and full-window supervisor tests. Windows host launcher not executed on a Windows machine here. |
| Qualified full calibration days | 0 |
| Final CI paired grids | 90 total, 16 valid (=17.78% of this 90s smoke), far below the required full-day 99% coverage. This is not a definitive estimate of every future day or event. |
| Gross/net/notional economics | Undefined; 0 economic events/returns opened. No results for 10/25/50/100 USDT. |
| Protected event | ECB 2026-10-29, scheduled 14:15 Europe/Berlin = 13:15 UTC; T0 must be actual local first-seen substantive publication, not scheduled clock. |
| Outcomes opened | **0** |
| Next gate | Qualified source/clock/continuity coverage and >=5 full prospective days / >=21,600 valid grids; then frozen calibration and committed activation receipt before 26 Oct UTC, plus qualified 1s event publication/shadow runtime. |

## Independent technical captures

| Run | Commit | Tests | Paired grids | Valid grids | Result |
|---|---|---:|---:|---:|---|
| 37300913583 | `0c8a6ed3125f778aa3a63ea9985f0d9737914d71` | 29 PASS | 90 | 0 | Both public feeds accessible; cold Binance clock RTT failed frozen gate |
| 37301839008 | `3436f7ec49bdbd8e7a9fd250c93cd9e3ad2c3463` | 31 PASS | 90 | 13 | Pooled HTTP clocks passed; stale/misaligned quotes still invalidate most grids |
| 37302785198 | `99b1b12f1e4422f7fd028c82b45f2bee718ca903` | 32 PASS | 90 | 16 | Latest runtime/package implementation works; coverage and variable clock uncertainty remain blockers |

These are source/technical captures only. CI SUCCESS means the bounded job/tests
completed, not SOURCE_PASS or economic PASS. No threshold/horizon/fee/event list
or statistical gate was selected using these counts. All raw captures are burned
setup evidence, not ECB event outcomes.

## Source quality diagnosis

The final run had 57 MEXC-stale and 19 Binance-stale grid observations; 24 grids
had both books fresh, three of those exceeded 500ms cross-venue time difference.
Clock qualification and startup contributed further invalidation, leaving 16
valid paired grids. These categories overlap; do not sum them as disjoint causes.
An unchanged book or a connected socket is not permission to invent a fresh
exchange timestamp. The code preserves the frozen <=1s age and clock gates.

Connection pooling removed an avoidable per-request HTTP/TLS cost. Environment
proxy/TLS settings are retained; no VPN, location override, login or private path.
The optional SOCKS dependency supports an already configured environment proxy.
Local pooling also demonstrated actual ~188ms Binance clock probes without
changing the endpoint or deleting network time from the measurement.

## Implemented and corrected

Added timestamped Binance and MEXC adapters, buffering/bootstrap/continuity,
raw wire preservation, source failure receipts, reconnect backoff, clock
uncertainty/metadata/stale/alignment guards and per-second source grids. Added
semantic ECB discovery and durable first-seen logic. Added a public push/dispatch
smoke workflow on the named branch with read-only permissions and raw artifacts.
Added a locked calibration checker that cannot promote short/invalid samples,
select profitable windows or calculate PnL. Added operator ZIP and full-window
foreground supervisor; avoids an intentional 10-second hourly gap and avoids
silently selecting a partial launch day. Long-run report generation no longer
loads every wire receipt/raw grid into one giant list.

Still not complete/qualified: continuous operator disk/process observation,
full daily coverage, event-window 1s publication/runtime, event shadow state/
fills/funding/aggregation and immutable activation receipt. The pure frozen fill
model is tested but is not represented as an armed economic execution engine.
No remaining implementation blocker is called scientific failure.

## Evidence anchors

Final raw CI archive SHA-256:
`1710409ba69f79417ce81d207218ce19712a3fcb539cc6d43cf8bbe51204ee3c`.
Final source chain head:
`b294280574813c78c14106e7eb1c0849aa4bd36419d9693716366dbaecf05ee8`.
Artifact ID `11342181365`. Byte-exact ZIP, source DB and SHA chain were downloaded
and verified. Earlier two byte-exact CI ZIPs plus local raw SQLite backup are
preserved in `FOREX_ECB_V021_RAW_EVIDENCE_2026-10-05.zip`; bundle receipt links the
durable item. GitHub's 90-day artifact expiry is not relied on as permanent raw
retention. Operator ZIP hash/file manifest is in its separate package receipt.

Authority and historical closeout preserved. No main merge, orders, private APIs,
account reads, wallet, spending, Render or economic outcome evaluation.

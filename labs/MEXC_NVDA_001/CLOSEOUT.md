# MEXC NVDA 001 — BLOCKED

No executable edge validated. No thresholds retuned. No merge, trading, private exchange endpoints, account reads or exchange mutation.

Architecture and pre-outcome freeze committed locally before data acquisition (6749dae) and published through GitHub connector (0c418a4bb326c47edefa2015f42ca6a9b0e6a8b5). The immutable protocol JSON is identical. Commit metadata differ; the connector's original architecture title had a UTF-8 decoding artifact, corrected in final publication without changing any architecture fact or strategy rule. Original freezes remain in Git history. Base main f263c6c6f3a57f26666a7aee28e782f2cbd08418. Dated addendum adds source evidence without adding event tests.

## Legitimate sample

1320 segmented public requests (Last, Index, Fair across 440 UTC daily windows from 2025-07-23 through the acquisition cutoff). No failed requests or conflicting duplicates. Returned history has 44,349 common minutes, continuous within its returned span, starting 2026-09-04 and ending at the last complete minute selected on 2026-10-05. Older success-with-empty responses are retained; coverage is NOT 100% since contract creation. The earliest returned timestamp is not proof of an exchange-wide historical retention policy. Discovery16 observed UTC days (Sep4–19), OOS8 (Sep20–27), Holdout8 (Sep28–Oct5, last day partial). Partial first/last days are included per the availability-based freeze; this is only about a month, not a full-year study.

848 historical funding settlements retrieved with observed cycle changes (24h/1h/8h); 92 within the price sample, maximum adjacent interval8h. Zero funding is not assumed from old promotional documentation. None of the frozen five-minute qualifying holdings crossed a returned settlement. Full timestamp coverage and source arrival latency remain separate gates.

NVDAON spot history: 43,102 minutes intersect the future sample; no failed requests. Public spot census also lists NVDAXUSDT. No unregistered replacement of Ondo with xStocks performed. Current future census has one interchangeable NVDA contract, NVIDIA_USDT; NVD and NVDL are leveraged ETFs, not multi-rail equivalents.

## Hypothesis verdicts

| Hypothesis | Verdict | Evidence / exact gap |
|---|---|---|
| H1 Nasdaq -> token -> future | BLOCKED | No aligned timestamped Nasdaq share corpus obtained; dated constituent/instrument mapping and token total-return conversion missing. Current indexOrigin does not assert Ondo dependency. |
| H2 Last–Fair 1m magnitude screen | NO_EDGE | Max14.3705bps Discovery, 10.3833 OOS, 10.6220 Holdout; zero minutes >=16bps. Narrow convergence magnitude screen only; this does not exclude intraminute dislocations or unrelated funding strategies. Closed without retuning. |
| H2 Last–Index fixed rule / execution | BLOCKED | Magnitude survives a fee-only screen; OOS/Holdout have too few independent signals/days and historical executable depth/spread/latency missing. |
| H3 token–future residual | BLOCKED | Token bars obtainable, but corporate-action/total-return conversion and dated index architecture unresolved; no authenticated vendor access or invented conversion. Historical executable costs absent. |
| H4 cash/event regimes | BLOCKED | Wall-clock open/close, pre/after and overnight diagnostics computed in New York timezone. No official session/holiday calendar frozen; earnings outcomes excluded. No event selection after viewing data. |
| H5 MEXC interchangeable multi-rail | BLOCKED | No eligible second future found in current census. Historical listing ledger missing. Forward collection cannot create a nonexistent rail. |
| Global | BLOCKED | No SURVIVES; partial narrow NO_EDGE does not kill unresolved source hypotheses. |

## Frozen price-path diagnostics

Completed-minute residual threshold20bps, fade direction, next-minute Last open to open five minutes later; consecutive positive-volume bars and nonoverlapping holdings required. These are price-path diagnostics, not fills. Fee-only results subtract16bps. The separate4bps spread/slippage stress is an assumed stress, not a measured transaction cost.

| Split | Max Last–Index bps | Signals / active days | Mean gross bps | Mean after16bps fee | Mean after20bps stress |
|---|---:|---:|---:|---:|---:|
| Discovery |44.2133|241 /4|0.3311|-15.6689|-19.6689|
| OOS |30.6362|8 /1|4.5236|-11.4764|-15.4764|
| Holdout |21.1198|1 /1|13.7634|-2.2366|-6.2366|

Direction-reversal, one-day signal shift and extra-minute delay controls executed independently inside every split; their fee-only means remain negative. One Holdout observation is not statistical validation. Confidence intervals are suppressed below30 active signal days rather than presenting a degenerate bootstrap interval. None of the splits meets the frozen statistical gate. Fair-price maker diagnostic floor12bps is exceeded only in Discovery; it is not a fill or maker edge and does not alter the taker verdict.

## Exact next data needed

1. Time-versioned NVDA index constituents, actual source instruments/weights, fallback/staleness rules and the Ondo-to-current transition date; authoritative historical contract/trading-status/corporate-action ledger. Current labels and general index FAQ do not resolve these.
2. Timestamped NASDAQ NVDA trades/BBO or provenance-verified bars, including publication/receive time, and token conversion/corporate-action records. Raw NVDAON vs share price equality cannot be assumed.
3. Historical MEXC BBO/full depth/trades matched to Index/Fair receive times for executable validation. Documented recent-trades/last-N-depth routes do not provide arbitrary old-time history. Public REST collector records full depth snapshots (L2 observations), L1 derivable from those, recent trades, Index/Fair/funding/ticker plus NVDAON depth/trades. It is partial polling, not lossless L2/tick reconstruction. Version/sequence gaps and trade-key collisions must invalidate claims that require complete order flow.

`forward_collector.py` is implemented and opened with bounded smoke collections. Initial smoke exposed an incorrect ticker route (404); corrected to query-symbol route. Corrected future-only smoke: zero errors; extended future+token smoke: zero errors over7 cycles/~31seconds. The archived extended receipt predates a wording-only correction to its scope field; its raw URLs prove token capture. No persistent background job was installed or left running. A continuous30-day public collection and the frozen15/7/8-day split remain necessary; current smoke is not an outcome sample. A reliable publicly accessible Nasdaq feed must be wired separately before H1 is testable. No threshold optimization is authorized by this closeout.

## Reproducibility and verification

Restore exact archived responses using `restore_evidence.py`; hashes are in evidence/package_manifest.json and evidence_manifest.json. Then run analyze.py to regenerate results.json. acquire.py is resumable; new collection requires a new preregistration, not silently extending this frozen sample. Run test_analysis.py for synthetic next-minute execution timing, split isolation and rejection of false confidence from one signal day. Two meaningful tests passed. All live outcomes are in results.json; token_source_receipt.json separates obtainable data from unresolved architecture gates.

Frozen JSON and scripts are preserved, along with logs, manifests, raw compressed evidence parts and collector observations on the isolated branch. No claim is made that blocked sources have been exhaustively proven nonexistent.

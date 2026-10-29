# EVENT-10M MU V0.3 — SOURCE FORENSICS CLOSEOUT (29 Oct 2026)

**Verdict:** HISTORICAL OPENING SOURCE WINDOW REPRODUCIBLE, but Yahoo source entire-day historical drift root cause remains **UNDETERMINED**. No outcome read occurred on this V0.3 branch, no live as-of custody or economic conclusion.

## Independent read-only runs

- [Run #40907599978](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40907599978), job 123566513413, head 323a9b0d73ab8f0248368f9c054accf16cd8dc65: SOURCE_WINDOW_STABLE_WITHIN_RUN.
- [Run #40907759684](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40907759684), job 123567088924, head 43bd6aaab2035195d30e6e450945c806c3293141: SOURCE_WINDOW_STABLE_WITHIN_RUN. Second run used byte-identical Python source; only GitHub Actions step label changed to trigger it.

Each run fetched *exactly* same historical window Oct26–Oct27, Yahoo query1 twice plus query2 once and MEXC MUSTOCK Min1 index twice/day. All three Yahoo requests produced the exact same **60 1-minute close bars per opening hour** on each day; two MEXC requests produced the exact same **61 1-minute index open bars per opening hour**. Opening-window SHA256 fingerprints were identical **across independent GitHub jobs**, not only within a job. No missing bars.

| Day | Yahoo MU STOCK CLOSE: 60 bars SHA256 | MEXC MUSTOCK INDEX OPEN: 61 bars SHA256 |
|---|---|---|
| 2026-10-26 | `d47ed00b747bc37f8e6b557d151496015b8f7b0776ca8e3476bf9a8bf04288d2` | `6d263827363061ccb8f30a08b32a4472874b5a021ad16b1278f01fd4006a43db` |
| 2026-10-27 | `95060301367034d6b33b9f5633d4a5779938cf5574c5eaa305640b74bf294528` | `3fc8f721b9028be5452d7583f99fdb0360ea42aeaad7c4f586c73ec3cdc205d6` |

Historical full 780 Yahoo close vector in both of these runs hashed `fb5f745b4dde9fd611199de115302401f8c0bcb411ae3bed6e58dbe708062733`, different from earlier V0.2.1 `aea2418b3308cec57eb1480fcf847ab9e4b82f2f9091b72a8eb14770dfcb6c5d`. The older raw underlying vectors were not preserved, only hashes, so the actual changed minute(s) CANNOT be isolated after the fact. Yahoo unprocessed JSON bytes continued to differ between calls in V0.3 while the canonical opening prices matched. Do not falsely claim the full-series historical drift was "just metadata".

**Scientific status:** source-only opening window feasibility established for small exploratory replay. Does NOT prove a source feed was available with a bounded receive timestamp at the original historical decision time, or that the MEXC standard Futures index open price equals Event Futures server-assigned open/expiry, or that historically effective payouts match the Oct29 public product rates.

No NVIDIA, SPCX, MLI alias, private API, orders, capital, September holdout, trading, main merge.

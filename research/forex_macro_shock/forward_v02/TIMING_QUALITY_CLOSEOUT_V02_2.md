# FOREX V0.2.2 — timing repair, activation locked

Candidate `FOREX-ECB-EURUSDT-DISLOCATION-FWD-001`; parent family
`FOREX-MACRO-SHOCK-001`. Historical V0.1 remains SOURCE_BLOCKED.
MEXC EUR_USDT perpetual versus Binance EURUSDT spot. Research-only, public-only.

The delayed asyncio wake-up could previously consume a book received after the
nominal UTC grid. This violated the frozen information cutoff even when wake-up
lateness was below 250ms. DepthBook now retains recent immutable summaries and
selects the last applied state received at or before the grid. Duplicate messages
never refresh the observation; a reconnect/reset clears the history. Freshness
is evaluated at the decision grid, not at the delayed wake-up. Missing evidence
is rejected; there is no interpolation or reconstruction of missed grids.

Each new grid contains clock-probe facts, metadata proof hashes and a reproducible
list of rejection reasons. Clock uncertainty is recalculated from recorded
send/receive/source times. Future-received prerequisite probes cannot qualify a
earlier grid. Calibration recomputes quality and basis/spread from those facts;
a boolean source_valid flag alone no longer qualifies a grid. Legacy grids lack
this self-contained proof and are retained as diagnostic evidence, never silently
promoted into calibration. This checker is not an event activation receipt.

Technical implementation tested at commit
`51b9d1f94f006be7698c6d62dd6fc09cfada3e01`.
All 36 synthetic/restart/timing tests pass locally. Added tests cover a quote
received just after a grid, future-only bootstrap, duplicate freshness, a false
source-valid claim and fabricated burn-in measurements. No economic outcomes,
real strategy signals or PnL were opened.

Read-only prior-source audit (all three raw chains PASS; DB bytes unchanged):

| CI capture | Grids | Previously claimed valid | Post-grid quote selected | MEXC max applied receipt interval | Binance max interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original WS | 90 | 0 | 0 | 7614ms | 5602ms |
| Pooled HTTP | 90 | 13 | 0 | 5884ms | 3500ms |
| Final V0.2.1 | 90 | 16 | 0 | 6115ms | 3300ms |

The timing defect was possible but did not occur in these 270 recorded grids.
These are setup/source diagnostics, not historical economic backtests. Message
silence does not prove a fresh exchange observation. Bursts of applied updates
and intervals above 1000ms help explain stale grids; transport RTT alone does not
resolve them. This is not a definitive full-day estimate. Freeze age/coverage
criteria remain unchanged; neither polling, heartbeat nor a repeated update ID
may invent a fresh source clock.

`audit_sources.py --state PATH` verifies raw hashes/chain and reports timing only,
using a read-only SQLite connection. It never writes to the source database,
selects a strategy threshold or computes returns. Full derived prior audit is
`evidence/PRIOR_SOURCE_AUDIT_V02_2.json`.

Freeze SHA256 remains
`6ea83bed921ce8f65c2e4bfd3af0af35be39de733074c2b0350b0f6a1ab0c2d4`.
Required burn-in remains at least five distinct full weekday 10:00–16:00 UTC
windows, 21,600 valid paired grids, >=99% daily valid coverage and qualified
continuity. Deadline remains 23 Oct exclusive; calibration/activation receipt
must be committed before 26 Oct. First protected event remains 29 Oct. There is
no qualified event runtime, no 1s event publication capture, no automatic
activation, and no background process left active. OPERATIONALLY_BLOCKED is a
technical verdict, not NO_EDGE or economic failure.

Use the updated source-only Windows package with Python 3.11+ and
`start-burnin.cmd`. Keep PC awake and window open; it waits for the next complete
weekday window. Preserve prior SQLite state. Legacy rows remain diagnostic and
unqualified; do not delete them to rescue calibration. Windows launcher has not
been executed on Windows here. No service, order, private endpoint, spending,
Render deployment or main merge is authorized or performed.

## Prospective corrected CI receipt

GitHub run [37305960903](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37305960903),
job 111749585425: SUCCESS, 36 tests pass, bounded 90s public source run.
4,624 receipts; 90 grids; 21 independently valid (23.33%). Both books reached
ready status during the bounded run; runtime_active=false after completion.
Audit independently reproduces exactly the 21 valid flags, with zero post-grid
quote selections. Both capture and audit have outcomes_opened=0.

Overlapping rejection counts: MEXC exchange age 61, MEXC receipt age 50,
cross-venue timestamp mismatch 63, Binance exchange/receipt age 10 each, startup
no-book 2 Binance / 1 MEXC. These are overlapping reasons, not additive totals.
MEXC max applied receipt interval 7495ms; Binance 2500ms. Applied-message source
age medians 141ms MEXC / 72ms Binance; low arrival latency alone does not pass
freshness on every grid. No threshold/cost/horizon was selected from these data.

Raw receipt chain:
`042cdaa78a1b8a00689ba836337a07bc31811a3c9fbda8b380517dafd860b223`.
Byte-exact raw artifact 11342919717, 743283 bytes, SHA256
`8bc6f037a5ef654f73ad3603923979c5f60d5a33f177cd8c52d6d313bc873cc5`.
Downloaded archive bytes and embedded SQLite receipt/raw hash chain verified.
Raw ZIP preserved as `FOREX_ECB_V022_RAW_EVIDENCE_2026-10-05.zip`.
Derived capture receipt, independent source audit and blocked calibration receipt
are in evidence/CORRECTED_*_V02_2.json. Calibration still rejects insufficient
count/days, daily coverage, capture continuity and open burn-in window. No
calibration values were finalized and no activation occurred.

Next gate: prove continuous fresh source coverage under the unchanged freeze.
The current depth feed cadence has not demonstrated this. Merely leaving the
collector running for five days cannot guarantee qualification. If the declared
source requirement cannot be met, retain OPERATIONALLY_BLOCKED; no economic
claim or first-event activation follows from a green CI job.

# BINANCE-DIAMANTE-005 — FROZEN MULTI-DAY REPLICATION / FREQUENCY GATE
**Protocol registered 2026-11-23, BEFORE first BINANCE-005 prospective run.**
Study ID: `BINANCE-005-SAME-FROZEN-004-ABSORPTION-30-DAY-REPLICATION`

## Critical constraint: do NOT change the signal
This is a prospective **frequency, source stability, and economic-shadow replication of EXACT BINANCE-004-V01**. Scientific identity from [PR #375](https://github.com/joseluisvieira28-oss/Laboratorio/pull/375), pre-data protocol commit `42d8725ae32eab146acd6958dc3804079bdd018e`. Frozen threshold family: 30s windows, aggregated sell share >=65% and quote volume >=5,000 USDT, >=80% visible 10bps bid depth persistence, mid drop no worse than 3bps; 60s LONG Spot hypothetic after next book update, <=3s entry/exit tolerance; 120s per-kind symbol cooldown, no decisions after 360s of each 480s session. BTCUSDT, ETHUSDT, SOLUSDT Spot only. Baseline every fourth valid interval. Never retrain or rescue a null signal.

The below Git blob SHAs are **IMMUTABLE CODE GATES**, checked before each future session, independent of the 005 branch HEAD:
- `research/binance_diamante004/PROTOCOL.md`: `b1b8d2aa2b9dd4853e04671de0d96336ae895d1b`
- `research/binance_diamante004/capture_forward.py`: `ef8a987e026656cd3a60d402761c21078dee3ca7`
- `research/binance_diamante004/study.py`: `58cf6af9c0ba26da2ac9efa700c103b93c7580b5`
- `research/binance_diamante004/verify_offline.py`: `33ca9731cbbb2d4f22db8d5309d4616bfe3ca616`
- `research/binance_diamante003/book_core.py`: `9b2a92455d36dc251ec99a2754c07a7f91a9af91`

No 005 changes to 004/003 rules or source tools. Fail-closed on changed blob SHA, account access, source gap or invalid clocks.

## Prospective schedule and cost
- GitHub repository `joseluisvieira28-oss/Laboratorio` verified public at setup; use exclusively **standard `ubuntu-latest` GitHub-hosted runners**, currently free for public repositories per GitHub official billing docs. Stop if public access/runner charges change. No payment/subscription authorization.
- Exactly one **one-off 480-second** anonymous public Binance market-data capture per new UTC day: initial feasibility on 2026-11-23 via isolated DRAFT PR; then planned **30 new calendar days**, 2026-11-24 through 2026-12-23 inclusive, UTC calendar, operator-controlled check-ins. Future daily trigger uses a unique dated marker file committed to this DRAFT branch; pull-request CI runs from the isolated branch, **no workflow merge to main and no GitHub `schedule` on main**.
- Daily trigger must check the marker filename **equals the current UTC date** and assert no same-day marker exists before creating. One daily marker only; if a day's collection is blocked, retain failure as missing, **never run a same-day rescue or substitute a different time**.
- All runs one read-only public WS `wss://data-stream.binance.vision`, one public REST snapshot per symbol; no retries, no cron in the repo, no password/keys, futures, paid API, real paper exchange orders, Telegram, Render or deployment.
- Journal up to 40k frames / 50MB per session, **ONE short 480s market window**, single-run timeout 14 minutes; raw receipts SHA256 archived per unique GitHub Actions run ID for 60 days. No relabeling statuses, event cherry-picking or raw-data editing. If GitHub Actions artifact expiration creates data gaps before final audit, classify affected day `MISSING_ARCHIVE`, never synthesize.

## Aggregation and independence
- Study clock is each session's **capture receipt UTC day from journal**, not GitHub job creation time, title, or marker alone. Each session must lie entirely in one UTC date; if it crosses midnight UTC, mark that session invalid for the daily independent sample.
- Exactly the **first initiated trial for that UTC day**, whether PASS or FAIL, is the daily record; any accidental rerun on that day is flagged as DUPLICATE and is **excluded** from primary economics. Correlated baseline/control overlap is disclosed; never add the cohorts as independent wins.
- Strict windows and 004 same-code replay from raw original events with frozen cost logic. No merging 004 pilot events into prospective 005 population; 004 acts solely as prior feasibility.
- Define primary per-event 1,000 USDT stressed net bps as 004 `STRESS_5BPS_net_bps` (10bps taker and 5bps adverse slip **per leg**), net to reference static book ask/bid; no actual fills. Distinct UTC days are bootstrap clusters. 100 USDT and 1,000 USDT BASE (2bps adverse slip/leg) remain sensitivity, never a cherry-picked alternative economic GO.
- A full **GO SCIENTIFIC** would require *both* >=200 matured independent PRIMARY events from >=20 independent accepted UTC days, mean stressed bps >0, one-sided day-cluster bootstrap lower 95% >0 with 10,000 **fixed-seed (20261123)** replicates, no single UTC day contributing >20% of total net gains, robustness vs flow-only and unconditional long baseline and further independent prospective replication. *All are necessary, not individually sufficient for live authorization.*
- These source and quote-based observations **cannot** certify tradeable execution; even a scientific GO is NO_GO_LIVE without Swiss account access verification and real execution constraints.

## Failure, stops and verdict
- Source failures, missing days, artefact corruption, null timestamps, unexpected code drift and schedule gaps are visible as BLOCKED/MISSING, not replaced.
- At 30 prospective daily check-ins, stop the automatic collection and decide: `INCONCLUSIVE_INSUFFICIENT_PRIMARY` if event/day minimum missed; `REJECTED_OR_INCONCLUSIVE_ECONOMIC` for adequately sampled negative outcomes; `GO_SCIENTIFIC_LIMITED_NO_LIVE_GO` only if **all** frozen gates pass independently.
- This pilot is not authorization to change the economic mechanism, launch bot, create real orders, trade, pay or merge to main. Preserve original closed CPI/NFP/MEME/BTC10m labs and protected holdouts.

GitHub official billing: https://docs.github.com/en/actions/concepts/billing-and-usage . GitHub workflows `schedule` and `workflow_dispatch` require default-branch setup; therefore the daily PR-marker approach avoids modifying `main`: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow .

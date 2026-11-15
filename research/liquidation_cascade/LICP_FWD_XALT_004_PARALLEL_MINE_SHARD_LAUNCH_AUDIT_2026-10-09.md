# PARALLEL MINE — LICP-FWD-XALT-004 PROSPECTIVE SOL 60M SHADOW CONTINUATION
Date: 2026-10-09, run queued at 20:23 UTC
Status: FUTURE SOURCE OBSERVATION IN PROGRESS, NO NEW OUTCOME VERDICT YET
Authority: RESEARCH/SHADOW ONLY, trading authority NONE, no private accounts, orders, wallet, Render or main merge

## Reason to prioritize in parallel to RW-HL-EXITFLOW-001
The Robot Wealth Hyperliquid OI/funding work is at a fresh 14-day SOURCE gate (2026-10-10 through Oct23 UTC); it is not a profit test. To attack an economically distinct pre-existing candidate, prioritize the separate **BTC confirmed liquidation ignition -> SOL_USDT short 60m transfer**. Do not adjust or pool with the Hyperliquid OI family.

Historical `LICP-HIST-XALT-003` original protected 2025 Q4 holdout, canonical run `36234052123`:
35/35 valid; mean gross +25.071392bps and mean **transfer-ceiling** net +9.071392bps after fixed 16bps transport fee proxy. This is **NOT MEXC fill-adjusted PnL** and cannot be promoted until current source transfer validates.

Prospective canonical XALT-004 preceding run `37733563875`:
- four already-completed October 5 real-public MEXC BBO virtual trades, mean net -11.295823bps after the frozen 16bps hurdle, **1 UTC day**;
- two additional October 8 real source episode entries ended with `exit=null` before the observer stopped; since the 60-minute due exits passed while OFFLINE, these are irrecoverable prospective missing exits, not valid completed trade outcomes.
- no other XALT forward job running before launch.
- prior duplicate `37732360638` NON_AUTHORITATIVE and excluded.

## Frozen preflight — PASS BEFORE this observation started
[2026-10-09 XALT frozen artifact preflight run 37986534222](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37986534222) verified:
- exact authoritative **artifact 11548718087** and SHA256 `16debf506b5f2f090ab0eefd19529fcf82547cb36e9ff4d6973c2956582ae93d`;
- original source trigger config status FROZEN;
- original durable-state episode IDs unique;
- original 60,000ms entry delay, >=3,600,000ms exit horizon, 16.0bps fee gap unchanged;
- **4 completed + 2 expired now missing exit** with one completed historical UTC day;
- 10/10 synthetic fail-closed tests PASS.
Immutable read-only preflight receipt artifact [11642544976](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37986534222/artifacts/11642544976).

## Exactly one NEW future-only observation
The XALT trigger token changed ONCE to `LICP-FWD-XALT-004-2026-10-09-NEXT-01`, commit `b159ac21a4d94cdae82fa4ff7d897c09ea1d265b`.
The UNCHANGED original source observer .github/workflows/licp-fwd-xalt-004-shadow-block-v01.yml was launched:
[run 37986608683](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37986608683).
The block runs for 20,700s (~5h45), using public Bybit BTC forced liquidations, Binance BTC forceOrder confirmation and MEXC SOL_USDT BBO. Observes only NEW event-time prices after run start; original state mark_restart_gaps must mark lost exits as missing. No live orders, no paid authenticated exchange endpoints.

### Hard scientific gates unchanged
- BTC_CONFIRMED SELL only, 120s cooldown;
- first fresh noncrossed MEXC SOL bid >=60s after ignition, ask >=60min after entry;
- frozen taker cost 16bps/roundtrip;
- >=20 independent episodes matured, >=3 UTC dates, <=10% missing entry/exit;
- positive mean NET, median gross and >=2 profitable UTC-day gross means.
Do not alter event classification, side, thresholds, horizon, fee, or source. Distinguish historical coarse holdout from live MEXC transfer.

**Current scientific decision, as-of run started:** `FORWARD_INSUFFICIENT`. Initial 4 completed events mean -11.295823bps; two expired missing exits must be counted honestly. New run has NOT completed and future results MUST NOT be invented.

## Next audit
When and only when run `37986608683` is completed, inspect GitHub Actions job result and artifact `licp-fwd-xalt-004-state-37986608683` for restored SHA/state, source health, dedup counts, newly matured episodes, honest miss count, UTC dates and frozen FORWARD verdict. Do not dispatch concurrent shadow run, change main or authorize trading.

# LICP-FWD-XALT-004 — NEXT FUTURE SHARD TRANSPORT AUTHORITY (2026-10-09)
State: FROZEN OPERATIONAL AUTHORITY BEFORE NEXT SOURCE WINDOW
Target: the existing scientific study, NOT a new LAB_ID.
Trading authority NONE. No exchange accounts, wallets, orders, Render or main merge.

## Why this is the chosen parallel mine
The independent historical `LICP-HIST-XALT-003` 2025-11..12 frozen holdout recorded **35/35 valid BTC ignition -> SOL SHORT cases**, gross +25.071392bps average, transfer-ceiling net **+9.071392bps** after a frozen 16bps hurdle; legitimate historical survivor, but NOT real executable PnL or proof that Bybit/Binance/MEXC signals will transfer.

Current `LICP-FWD-XALT-004` uses distinct, explicitly frozen REAL-TIME public-source-transfer sensors:
- Bybit BTCUSDT `allLiquidation` trigger
- Binance BTCUSDT `forceOrder` confirmation
- BTC_CONFIRMED SELL only, 120s cooldown
- MEXC SOL_USDT public executable BBO best-bid virtual SHORT entry exactly at first valid quote >=60s after trigger, best-ask exit >=60m after entry
- frozen taker fee hurdle **16bps round trip** (no maker/parameter rescue)
- final >=20 independent episodes, >=3 UTC dates, <=10% missing matured entry/exit, mean NET>0, median gross>0, positive mean gross on >=2 dates; no terminal classification before all gates.

## Baseline integrity and treatment of lost observations
Last authoritative XALT shadow run **37733563875** on 2026-10-08 [https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37733563875] completed successfully. Its latest durable immutable artifact:
- artifact ID `11548718087`, name `licp-fwd-xalt-004-state-37733563875`
- GH artifact digest `sha256:16debf506b5f2f090ab0eefd19529fcf82547cb36e9ff4d6973c2956582ae93d`
- four completed matured entries (October 5) with prospective mean net -11.2958bps after same 16bps frozen hurdle; date count 1.
- two additional episodes **obtained Oct 8 but exit=null** when the observer stopped. Their due 60m exits elapsed while source recorder was OFFLINE. They must become `exit_missed_restart=true` and count as missing matured, NEVER fill with current or historical MEXC prices. Subsequent verdict may be adversely affected by >10% missing; this is an honest operational consequence and cannot be masked.
- Earlier queued duplicate run `37732360638` is NON_AUTHORITATIVE_REDUNDANT_TRANSPORT and contributes ZERO science. Do not use its artifact as current state.

Before launching any new market observation, perform exact immutable previous-authoritative-artifact preflight: frozen config status, original constants and restored state, counts 4 COMPLETE + 2 PENDING, no duplicate episode IDs or previous source mutation, true current time beyond pending due, correct latest official artifact digest. Publish a read-only receipt with SHA evidence. An integrity fail blocks new source window.

## Exactly one newly authorized prospective observation block
After preflight PASS, update ONLY existing `research/liquidation_cascade/LICP_FWD_XALT_004_FORWARD_RUN_TOKEN_V0_1.json` to mark `LICP-FWD-XALT-004-2026-10-09-NEXT-01`. This triggers original unchanged `.github/workflows/licp-fwd-xalt-004-shadow-block-v01.yml` once on research branch `liquidation-cascade-propagation-v0.1` for **20,700 seconds**, with public Bybit/Binance/MEXC only.
- No 2nd simultaneous run; a prior queued/in-progress XALT job invalidates a duplicate launch.
- No predictions or outcome alterations, no live execution.
- Restore most recent valid authoritative XALT state; at startup the original `mark_restart_gaps()` MUST mark the two expired historical exits as missing, not fabricate their outcomes.
- Keep future-boundary timestamps, precommitted event/missing rules, 16bps economics, original same dedup/cooldown.
- Report latest immutable artifact, source connections, valid episodes, complete/missing counts and freeze verdict when job finishes. If remote job remains queued/running, ONLY report launch, not fabricated future result.

State after G0 and before next source: **FORWARD_INSUFFICIENT (4 COMPLETE / 2 EXPIRED PENDING, one UTC date)**. No MICRO-LIVE-GO; no historical +9.07bps guarantee of current net profit.

No merge to main, no authenticated exchange endpoints, private reads, capital, paid source or scientific retuning.

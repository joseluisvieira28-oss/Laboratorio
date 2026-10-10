# Windows Radar V0.14.4 — Healthy-last-cycle forensic closeout and evidence snapshot handoff
Date 2026-10-10. Owner PC V0.5 receipt `CRYPTO_LAB_LOCAL_RADAR_LOG_FORENSIC_V0.5` at 2026-10-10T18:50:06Z.

## Verified local forensic facts
- `radar_stdout.log` exists, **389.61 MiB**, last modified **2026-10-08T20:13:53Z**.
- Last **25/25** lines parsed as valid JSON; **0** non-JSON in sampled tail. The last eight visible states at **20:10:22Z through 20:13:52Z**, roughly 30s spacing, all report `health=OK`, `error_fields_count=0`, `direct_error_present=false`, `orders_created=false`.
- Corrects false-positive prior full-string regex finding **300/300 'Error' and 'FAIL_CLOSED'**: those keywords occur in rich state JSON; they were NOT distinct fatal errors.
- `forward_local_status.json` latest write **2026-10-08T20:13:53Z**, `health=OK`. `cirv_local_status.json` latest write **2026-10-08T20:13:29Z**, `status=FORECAST_READY`, `runtime_phase=TODAY_FORECAST_ALREADY_PERSISTED`. These prove local state had progressed by the final log window, NOT that the source/payout had economic profitability, nor that missing subsequent periods may be reconstructed.
- `radar_status.json` last modified **2026-09-25T09:02:15Z** with `health=OK`, `build_id=v0.14.4-win-cirv-eight-motor`; `dh03_local_status.json` last modified **2026-09-25T09:05:00Z` with `status=COLLECTING`; `forward_local_supervisor_status.json` and `render_sentinel_supervisor_status.json` last modified Sep25 with `status=RUNNING`. These are stale startup/status snapshots and do NOT establish a current functional collector.
- Windows V0.3 showed `CryptoEdgeRadarV0144` Task Scheduler Ready enabled, last result **267011 / 0x41303** and no recorded execution; uses **at-logon** trigger. No local `CryptoEdgeRadarNode.exe` process or listener on 8787 detected. Therefore **automatic local supervision is not demonstrated**, and final stop reason remains **UNKNOWN**. A healthy final cycle does not prove Windows killed the app or a socket exception caused termination.
- This is **legacy local SQLite evidence**, distinct from canonical Render/Supabase Postgres. Do not claim a unique canonical scientific writer or complete 24/7 collection.

## Launch-risk blocker
Original `crypto_edge_radar/windows/START_RADAR_RECOVERY_V0141.ps1` **deletes original stdout/stderr at launch** and, if 8787 is already taken by the approved Radar executable, may terminate the legacy process. Operator MUST NOT invoke it until evidence preserved and all process/single-writer gates reviewed.

## New V0.6 local snapshot tool — NO START
`crypto_edge_radar/operator_windows/CryptoLab_Radar_Recovery_Snapshot_V06.ps1`
- Resolves existing V0144 watcher task, approved root and `CryptoEdgeRadarNode.exe` filename, records installed executable SHA256 **without running it**.
- Finds four known logs plus local public-shadow JSON/JSONL/SQLite evidence and companion WAL/SHM within existing Radar data directory; reports size/count without exposing paths/log content. Refuses if Radar node process or 8787 listener exists when snapshot is requested.
- With explicit `-CreateSnapshot`, copies approved files to new **local** `%LOCALAPPDATA%\CryptoLab\RadarV0144RecoverySnapshots\<UTC-run>` directory. Checks copied sizes; retains **all original files unchanged**. Never upload this snapshot, which can contain private user information embedded in logs.
- Automatically refuses if expected exe absent, estimated backup >5 GiB or destination free space would fall below 2 GiB. It does not hash all original evidence files, nor independently prove SQLite transactional consistency: size checks alone are **not scientific integrity certification**.
- Generates **sanitized JSON receipt only** at `%TEMP%\CryptoLab_Radar_Recovery_Prep_V06.json`. No live exchange access, no account reads, no API credentials requested, no remote DB changes or new processes.
- Windows GitHub Actions hosted runner synthetic test [run #38077611399](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38077611399) **SUCCESS: V06_SNAPSHOT_SAFE_PASS**, with original log SHA intact. This test is **not the operator PC**.

## Operator handoff
1. Download Raw `CryptoLab_Radar_Recovery_Snapshot_V06.ps1`, save to Downloads, inspect and execute:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_Radar_Recovery_Snapshot_V06.ps1" -CreateSnapshot
notepad "$env:TEMP\CryptoLab_Radar_Recovery_Prep_V06.json"
```
2. Share ONLY the scrubbed JSON receipt, **never any backup files or log contents**, nor MEXC secrets, bot tokens, DSNs, or DPAPI blobs.
3. Only after snapshot confirmed: prepare a distinct reversible **manual public-shadow local node start** whose stdout/stderr target new timestamped names and whose guard forbids any existing Radar listener/node, with separate audit of local SQLite-only vs canonical Postgres writer, and a checked installed package identity. Do not auto-execute MEXC or re-enable disabled AutoLive tasks.
4. Staging is not a cutover; no guarantee of 24/7 power/internet or zero missed windows without an actual soak test.

## Governance
No main merge, no brokerage access/positions/positions exit modification, no market orders, no remote service deploy, no post-outcome retuning, no science gate bypass and no paid resource.

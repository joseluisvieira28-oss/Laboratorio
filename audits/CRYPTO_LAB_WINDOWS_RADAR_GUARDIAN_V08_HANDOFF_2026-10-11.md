# Crypto Lab — Windows Radar Guardian V0.8 staged handoff
**Date:** 2026-10-11. **Target:** existing user's local SQLite-only V0.14.4 eight-motor Radar. **Status:** repository candidate / offline Windows QA; **not installed on the operator PC**.

## Confirmed prior real-PC evidence
- V0.6 **44-file local snapshot** complete, approx. 0.409 GiB, old logs/data preserved.
- V0.7 **explicit local public-shadow start** completed on 2026-10-11T07:26:33Z. Local PID **3212**, registry **3.7**, eight focus motors loaded, localhost **8787**, expected build `v0.14.4-win-cirv-eight-motor`.
- Two read-only Windows checks ~45s apart: process alive, HTTP healthy, registry 3.7 8/8, `forward_local_status.json` mtime advanced **2026-10-11T07:31:19Z to 07:32:19Z**. Evidence shows actual successive forward state updates, not continuous 24/7 or per-motor scientific health.
- Old Task Scheduler `CryptoEdgeRadarV0144` remains **Enabled/Ready** and previously never recorded a run (code `267011`). The old launcher can forcibly terminate a stale/canonical mismatch and **deletes its historic stdout/stderr logs** before restarting.
- No known reason for Oct08 process disappearance; backup + first stable periods are not a proof of uninterrupted science or positive net trading edge.

## New files in this branch
- `crypto_edge_radar/operator_windows/CryptoLab_Radar_Guardian_V08.ps1`: **default one-shot audit**. `-Watch` alone is monitor-only; `-Watch -EnableAutoRecover` is an explicitly gated local SQLite public-shadow recovery.
- `crypto_edge_radar/operator_windows/CryptoLab_Radar_Guardian_V08_Install.ps1`: **default audit only**. `-Install` explicitly migrates just the existing *Radar* supervision from unsafe V0144 to new V08 task `CryptoEdgeRadarSafeWatchV08`.
- Offline Windows PS5.1 CI tests verify parseability, audit-only default, loopback absence handling, monitor-only bounded loop, prior log SHA unchanged and refusal of implicit auto-recovery. Installer syntax and static no-StopProcess/StopScheduledTask checks. This is **not** an end-to-end validation on the operator's own Windows; no task migration tested on the user's host.

## Guardian V0.8 strict runtime rules
1. **Adopt existing process** if exact executable path matches approved V0.14.4 exe, `127.0.0.1:8787` listener PID matches that process, HTTP build/registry = V0.14.4/3.7/8-of-8, forward status file updated within 180 seconds. Do **not** restart or kill it.
2. **Alive but stale/no HTTP/unknown port owner**: FAIL_CLOSED with alert in local Guardian log/receipt; **NEVER forcibly kill or start another process**.
3. **Both node absent AND port absent** on at least 2 successive polls spaced >=55s: only then consider recovery. Legacy task must exist but **be Disabled**; new V08 scheduled task must be **Running**; local V0.6 backup copied files must still be present; executable must match **operator's** SHA256 baseline `EFA25C10C9901A62173250BF147F8206D2A63722F815895AAE18FC73DA7FA5BD` (**not independently signed**); >=1GiB free RAM and >=3GiB free disk; reject known inherited secrets/DB URL environment vars. Perform bounded package selftest and recheck absence before starting old local public-shadow exe with **fresh timestamped logs**, never existing logs.
4. Persist recovery attempt to local state **before** launch. Up to 3 attempts/UTC day and no attempt more often than every 30 minutes. On a launch without HTTP identity, leave process untouched for human inspection. **Never synthesize missed retrospective entries / fills / market outcomes.**
5. Guardian writes a bounded own JSONL with uniquely named archival logs, never deletes prior archived logs or the old Radar logs. No Render/Supabase/Postgres write transport or brokerage mutations are added.
6. Protect new V08 watchdog itself with `Local\CryptoEdgeRadarSafeWatchV08` Windows Mutex and Task Scheduler `MultipleInstances=IgnoreNew`.

## Installer boundaries
- `-Install` is a separate, **explicit user-PC action** not yet performed. It will:
  - Require existing local Radar healthy, exact pinned executable SHA, fresh forward status, old V0144 task Ready and enabled, and V08 task absent.
  - Save full old ScheduledTask XML in local old Radar logs folder, install the new file without overwriting an unfamiliar version.
  - Register V08 logon task, start V08 while legacy still enabled (**automatic recovery remains disabled by guard during this adoption phase**).
  - Verify new V08 task RUNNING and identical old Radar process PID still healthy; **only then disable** the unsafe legacy V0144 task.
  - Verify V08 task running, old V0144 task disabled, and same Radar process PID. On partial failure, **fail closed**, leave full receipt for manual review, and **never automatically re-enable** the destructive legacy watchdog.
- Scheduled task trigger is at **user logon**, not pre-login Windows service. It will not guarantee monitoring after an unattended reboot that reaches login screen without signing in. Continuous observation requires PC power, login session, internet, healthy data providers, and an actual multi-day soak.
- No MEXC tasks are disabled/reconfigured, no live trade authority changed, no main merge.

## Operator commands (not yet used on their PC)
Download both script files' GitHub Raw versions into Downloads, **do not** run old `START_RADAR_RECOVERY_V0141.ps1`.

First operator step — safe V08 inspection:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_Radar_Guardian_V08_Install.ps1"
notepad "$env:TEMP\CryptoLab_Radar_Guardian_V08_Install.json"
```
Proceed with `-Install` **only after user/operator reviews PASS receipt, confirms the running Radar is still current, and expressly accepts replacing the unsafe legacy task**:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_Radar_Guardian_V08_Install.ps1" -Install
notepad "$env:TEMP\CryptoLab_Radar_Guardian_V08_Install.json"
```
Expected adoption: `GUARDIAN_V08_INSTALLED_ADOPTED_NODE_OLD_TASK_DISABLED` and same old PID alive. If any error or new task does not run, **do not retry/reboot**; reconcile state read-only.

## Governance
No MEXC authenticated access, orders, leverage/position changes, wallets, paid services, Render redeploy, database cutover, proof of one canonical writer, main merge, or scientific tuning. Monitor-only at first; auto-recovery remains guarded by explicit install and health validation.

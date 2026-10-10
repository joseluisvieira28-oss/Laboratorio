# Crypto Lab Windows V0.14.4 - Recovery after verified local evidence snapshot
Date 2026-10-10; default posture **PRECHECK ONLY**. No remote DB cutover. No MEXC execution.

## Operator PC V0.6 confirmed snapshot
The operator personally executed the V0.6 script at **2026-10-10T18:55:55Z** and sent its sanitized receipt:
- `snapshot_complete=true`, **44/44** local Radar evidence files copied; estimate **0.409 GiB**.
- All old logs and local data still in place; no processes started and no Task Scheduler changes.
- Installed `CryptoEdgeRadarNode.exe` SHA256 pin: `EFA25C10C9901A62173250BF147F8206D2A63722F815895AAE18FC73DA7FA5BD`.
- Node process **0**, TCP port 8787 listeners **0** at receipt time, free disk **13.3 GiB**.
- Operator hash is a **local baseline only**: NOT independently compared to an official exe release signature; the historical released artifact SHA256 was for an entire ZIP, NOT for this executable.
- File-count/size consistency is **not** transactional-consistency proof for copied SQLite/WAL, nor proof of market-data economic edge.
- Operator reports PC stays on; uptime/ISP stability, single canonical evidence writer remain unproven.

## V0.7 controlled local-only recovery script
`crypto_edge_radar/operator_windows/CryptoLab_Radar_Manual_LocalShadow_Recovery_V07.ps1`

### Safety boundaries
- **Default**: read-only preflight with sanitized TEMP receipt. No program started.
- `-StartLocalShadow` must be passed **explicitly** by local operator. It does not execute legacy `START_RADAR_RECOVERY_V0141.ps1`, which erases historic stdout/stderr and may force-stop a prior node.
- Refuses to start if V0144 task is not Ready, existing `CryptoEdgeRadarNode.exe` process exists, port 8787 has listener, SHA mismatch, memory free <1 GiB, disk free <3 GiB, or V0.6 local snapshot cannot be verified using original V06 receipt + the 44 copied files.
- Refuses if process environment contains known MEXC/Binance credential variables, Telegram token or canonical `RADAR_DATABASE_URL`/DATABASE_URL (checks existence **only**, never outputs values).
- Runs **packaging selftest** using the existing exe with `RADAR_PACKAGING_SELFTEST=1` and requires `status=PASS`, expected build `v0.14.4-win-cirv-eight-motor`, registry 3.7, 8 candidates and CIRV import binding. This selftest verifies package identity and importability but does not prove the installed binary exactly matches an officially signed release.
- Starts only the existing `CryptoEdgeRadarNode.exe` with fresh timestamped V0.7 stdout/stderr logs. Never deletes original logs, never kills any process or touches Task Scheduler. Sets only local public market provider + local SQLite evidence paths. Source `windows_node_entry.py` local DH03, CIRV, BNB/TFG/OPTIONS/ETF/EMA6H and Render Sentinel use **public data** and local stores; `local_forward.py` explicitly sets `database_url=None`. This is **not the canonical Render/Supabase Postgres writer**, which remains untouched.
- Fails closed on missing/mismatched package, collision or startup readiness; explicitly **does not auto-retry or forcibly terminate node on failed HTTP identity**. Manual diagnosis required if it reports a node still running without port readiness.
- May perform public-data downloads and local SQLite writes in `-StartLocalShadow`; this is an intentional local public-shadow start, NOT read-only. No MEXC account read or order path authorized, no remote writes, no trading, leverage or exit mutations.
- A passed bootstrap `LOCAL_SQLITE_PUBLIC_SHADOW_UP_NOT_CANONICAL_CUTOVER` means localhost GET returned expected build + registry 8/8, not that 24/7 collection has been proven or the historical missing two days can be recovered legitimately.
- PC always-on Task Scheduler reliability and historic missing windows require **separate post-start review**; DO NOT enable or manually start the existing V0144 watchdog yet. DO NOT restart Windows solely to trigger it.

### Operator commands after carefully inspecting downloaded source
Download Raw V07 script from canonical branch, keep filename in Downloads.
Run **PRECHECK ONLY** first:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_Radar_Manual_LocalShadow_Recovery_V07.ps1"
notepad "$env:TEMP\CryptoLab_Radar_Manual_Recovery_V07.json"
```
If and only if receipt says `PRECHECK_PASS_NO_NODE_STARTED` and the operator elects to restore the local SQLite-only public-shadow node, run:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_Radar_Manual_LocalShadow_Recovery_V07.ps1" -StartLocalShadow
notepad "$env:TEMP\CryptoLab_Radar_Manual_Recovery_V07.json"
```
If a gate fails, **do not retry**, send only sanitized JSON. Do not upload snapshots, log files, DB files, tokens, DPAPI blobs or executable to chat. Do not restart or adjust MEXC operator tasks.

### Scientific and operating gate
1. Confirm fresh localhost identity and 8/8 focus without conflating watchlist/motor counts with positive scientific edge.
2. Compare actual timestamp progression of local forward/CIRV/DH03 and logs while accounting for fail-closed missing windows, no retrospective fills.
3. Preserve Render/Supabase writer unchanged, continue Telegram alerts, resolve local supervision with a new no-truncate watchdog under separate reviewed authority. Existing V0144 scheduled watchdog may unexpectedly trigger next Windows login; reconcile/replace **only after** a controlled operating window, never by blind reinstall/reboot.
4. Prove multiple days of collector continuity. No micro-live permission from this incident recovery.

## CI
GitHub Actions Windows runner (not operator PC) validates default safe audit with pinned fixture SHA256, *and* expected negative test of a fake executable, which must fail package selftest before launching any collector. Hosted-runners do not validate the real `CryptoEdgeRadarNode.exe` or the user's power/ISP reality. See branch workflow `.github/workflows/crypto-lab-windows-manual-recovery-v07.yml`.

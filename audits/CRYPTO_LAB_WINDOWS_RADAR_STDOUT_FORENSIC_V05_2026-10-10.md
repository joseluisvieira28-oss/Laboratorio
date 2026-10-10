# Windows Radar stdout forensic: false-positive string counts, true root cause unresolved
Date: 2026-10-10. Operator's actual Windows has legacy radar node V0.14.4 absent from 127.0.0.1:8787. Scheduler `CryptoEdgeRadarV0144` enabled and READY, LastTaskResult=267011 (`0x41303`, not yet run). Trigger = logon; no evidence watchdog task ever started. Watchdog and recovery launcher exist; exact approved `CryptoEdgeRadarNode/CryptoEdgeRadarNode.exe` exists. The recovery launcher **deletes old stdout/stderr before launching**, and it may terminate an approved old Radar process: NEVER launch it just to diagnose.

## Evidence from user's latest PC (do not inflate)
- `radar_stdout.log`: ~389.61 MiB, last modified **2026-10-08 22:13:53 PC local time**.
- `radar_stderr.log`: ~1.89 KiB, last modified Oct06.
- The last 300 lines of stdout each match raw regex `Exception|Error|FATAL` **and** `COLLECTOR_FAIL|FAIL_CLOSED`; this is an **unstructured string count and not evidence of 300 distinct errors or crashes**, since full structured state records can contain those field names or repeated fail-closed source statuses.
- There are zero matched Application crash events within +/-30 minutes of last stdout write (lack of events is not proof no crash).
- `data/radar_status.json` was last modified Sep25 despite stdout being newer; not proof of live scientific writer.

## Code reality
The V0.14.4 Windows entrypoint may run independent shadow threads: DH03, local forward supervisor, CIRV, Render sentinel. Local `forward_web.py` outputs a JSON status **every forward cycle** via `print(json.dumps(state))`; text searches cannot distinguish a repeated blocked source from a process exception. Local dashboard HTTP errors `ConnectionAbortedError` can result from disconnected browser and are not terminal process proof. **Do not mistake a debug log, launcher, legacy local SQLite store, or current Render Supabase writer for one unique certified source.**

## New bounded read-only script and CI
`crypto_edge_radar/operator_windows/CryptoLab_Radar_Stdout_Forensic_V05.ps1`
- Resolves only the pre-approved Windows Scheduler task locally by pathname; never outputs task Arguments/Paths.
- Reads only **last 25 stdout lines** of ~390MiB log, parses per-line JSON, reports top-level enum-like status/health labels, JSON error-field **count** (without keys/messages), and flags any top-level direct error (without message). Does NOT expose raw lines.
- Reads only local metadata/allowed basic status names from six specific local status files; no large data loads, markets, keys, writes or any network API calls.
- Writes sanitized `%TEMP%\CryptoLab_Radar_Stdout_Forensic_V05.json`; does not change task/sleep/collector/render/MEXC/Postgres.
- Windows PowerShell 5.1 synthetic integration QA: [run 38076037699](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38076037699) **SUCCESS**; checks true empty error dict is 0 not a false positive, no raw error content disclosed.
- The test is on **GitHub-hosted Windows**, not the operator PC.
- To use: download Raw script; launch from Downloads with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_Radar_Stdout_Forensic_V05.ps1"`; then `notepad "$env:TEMP\CryptoLab_Radar_Stdout_Forensic_V05.json"`. No admin needed. Do not paste secrets or unsanitized raw logs.

## Next decision gate
Interpret actual PC V0.5 receipt and status chronology, compare with Oct8 stop and watcher history; separately preserve backup/integrity SHA256 of stdout/stderr **before** touching recovery launcher. Do not run duplicate local shadow collector, restart, change Task Scheduler or MEXC leverage/execution based on stale text. Local V0.14.4 is distinct from current Render Postgres-backed public shadow; true single-writer gate remains unverified. No science modification, no main merge, no live trading.
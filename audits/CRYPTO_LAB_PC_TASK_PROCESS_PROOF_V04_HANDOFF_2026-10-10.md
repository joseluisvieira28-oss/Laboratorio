# Crypto Lab — Windows scheduled task/process proof V0.4
Date: 2026-10-10. Owner-submitted V0.3 exact local observation at 14:41:10Z.

## V0.3 evidence vs unwarranted assumptions
- `CryptoEdgeRadarTruthCockpitV0145` = **Running** Task Scheduler state; last run 2026-10-08 20:55:49Z; last Task Scheduler code **267009 / 0x41301** ("running" status), which does NOT identify a functioning collector or its authorizations.
- `CryptoEdgeRadarV0144` = **Ready** and enabled, but no prior/next recorded run. A second name does NOT imply a second running writer, nor prove it is safe to start.
- `CryptoLab-Triple-Fishing-Operator-V03` = **Ready** and enabled, last run Oct08, last code **3221225786 / 0xC000013A** (usually interrupted console/control event); cannot infer current MEXC position or order state. **Leave task untouched.**
- `CryptoLab-OPTIONS-V21-Telegram-Watcher` = Ready/Enabled; last code 3221225786 (interrupted); may duplicate GitHub Telegram warnings, but no evidence that it currently executes. **Leave task untouched.**
- `CryptoLab-OPTIONS-V21-Futures-AutoLive` and `CryptoLab-BNB-Operator-AutoLive-V01` both disabled: **do not reactivate**.
- Local process name counts: **0** `CryptoEdgeRadarNode`, **0** `python`, **0** `pythonw`, **9** `powershell`. Local port **8787 has 0 listeners**. This is **evidence that the known local web port is not serving**, not proof that no headless worker runs or that the running Task Scheduler process is healthy.
- PC RAM 15.91 GB, free 2.20 GB; disk free 14.00 GB; AC sleep and hibernate disabled. Operator confirms availability for always-on use; internet uptime, power loss safety, dynamic RAM load, duplicate writer and DB access remain **UNVERIFIED**.

## V0.4 — one last local evidence gate
File `crypto_edge_radar/operator_windows/CryptoLab_PC_Task_Process_Proof_V04.ps1`
- Reads only the six known task labels, Task Scheduler state, count of actions, **coarse executable host class only**, trigger kinds and last run UTC / last result code.
- DOES NOT serialize executable path, **does not read any Task Arguments**, does not inspect process command lines, environment, secret files, DPAPI blobs or broker accounts.
- Reads process metadata only for `CryptoEdgeRadarNode`, Python, PowerShell and pwsh: PID, startup UTC and working-set MB, and listener ownership on localhost port 8787. Times can suggest correlations but CANNOT prove task-to-PID association.
- Outputs `%TEMP%\CryptoLab_PC_Task_Process_Proof_V04.json`; no telemetry, scheduled changes, trading, Postgres, Render or other effects.
- **Tested** on independent Windows GitHub Actions runner: [run #38060848104](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38060848104) `V04_READ_ONLY_PASS`. A previous prototype run failed PowerShell 5.1 UTF-8 no-BOM due non-ASCII dash; current committed file is strict ASCII and passed. Hosted runner's task counts/processes are NOT operator-PC observations.

## Mandatory user handoff
1. Download **Raw** `CryptoLab_PC_Task_Process_Proof_V04.ps1` from the canonical branch.
2. Execute (non-admin Windows PowerShell 5.1):
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_PC_Task_Process_Proof_V04.ps1"
notepad "$env:TEMP\CryptoLab_PC_Task_Process_Proof_V04.json"
```
3. Review local JSON; redact any personally identifiable process data the owner does not want shared. **Never** share MEXC private keys, positions/account credentials, Telegram BotFather token, Supabase credentials/DSNs, DPAPI payloads or full scheduled-task command lines.
4. Do not start or disable anything pending task-role review.

## Cutover gate
**NO_AUTO_CUTOVER**. If the existing `TruthCockpitV0145` is a local console observer, favor replacing **only** shadow collection through explicit single-writer source freeze and record reconciliation, while preserving all broker/exit tasks. If it is a writer, reconcile source role and DB before changing any runner. The free Render service is currently a separate Postgres writer and must be deliberately quiesced and verified BEFORE any Windows writer can take authority. That requires an extra reviewed permission and a reversible procedure. End-to-end uninterrupted 24/7 evidence must be observed, not assumed.

This document does not authorize a brokerage order, self-healing live execution, paid hosting or scientific gate changes.

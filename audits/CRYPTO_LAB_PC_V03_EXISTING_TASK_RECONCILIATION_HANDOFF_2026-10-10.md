# Crypto Lab PC Continuity — V0.3 actual operator reconciliation
Operator-supplied V0.2 receipt at `2026-10-10T14:32:16Z`:

- Windows 11 Home; ~429.36h boot uptime **is not continuity proof**.
- Total RAM **15.91 GB**, currently free **2.20 GB** (resource headroom caution).
- System disk free **14.00 GB** (resource headroom caution).
- AC sleep = **0 min**, AC hibernation = **0 min** in active power plan (good; actual internet/power continuity unverified).
- Six exact CryptoLab Task Scheduler records:
  - `CryptoLab-OPTIONS-V21-Futures-AutoLive`: Disabled — **must not re-enable**.
  - `CryptoLab-OPTIONS-V21-Telegram-Watcher`: Ready/Enabled — potential duplicate Telegram notifier; confirm role before change.
  - `CryptoLab-Triple-Fishing-Operator-V03`: Ready/Enabled — potential account operator; **leave untouched**.
  - `CryptoEdgeRadarTruthCockpitV0145`: Running/Enabled — unknown whether UI or evidence writer.
  - `CryptoEdgeRadarV0144`: Ready/Enabled — possible alternative duplicate Radar runtime.
  - `CryptoLab-BNB-Operator-AutoLive-V01`: Disabled — **must not re-enable**.
- Processes seen: 0 Python, 0 pythonw, 8 PowerShell; neither proves collector absent nor confirms MEXC execution.

### Risk classification
**POWER_PLAN_SUPPORTS_ALWAYS_ON, BUT SINGLE_WRITER_UNVERIFIED, MARKET_SOURCE_CONTINUITY_UNVERIFIED, ACCOUNT_ORDER_RISK_NOT_INSPECTED.** User confirms willingness to keep PC on 24/7, but no technical 24-hour dataset exists yet.

### V0.3 tool
`crypto_edge_radar/operator_windows/CryptoLab_PC_Worker_Reconciliation_V03.ps1`

Read-only enumerates ONLY those six exact task names, state, enabled, last/next run metadata, Task Scheduler multiple-instance policy, and TCP LISTEN ownership of local port 8787 by PID/process **name only**. Does not enumerate task Action commands or arguments, environment variables, secrets or any account data; does not issue HTTP requests, touch Postgres, exchange APIs, or mutate tasks/settings. Generates only local receipt `%TEMP%\CryptoLab_PC_Worker_Reconciliation_V03.json`.

CI (Windows GitHub Actions **runner**, not operator's PC): [run 38060217158](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38060217158) passed `V03_READ_ONLY_PASS`. On CI machine task count 0 and port listener count 0 (expected).

### Operator action
Download **Raw** `CryptoLab_PC_Worker_Reconciliation_V03.ps1` from repository; run PowerShell 5.1 as logged-in operator with no admin rights:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\CryptoLab_PC_Worker_Reconciliation_V03.ps1"
notepad "$env:TEMP\CryptoLab_PC_Worker_Reconciliation_V03.json"
```
Before sending, review local JSON for any personally identifying task names and redact if needed; **NEVER** share BotFather token, MEXC keys, DPAPI blobs, database URL, account numbers, private trade positions or local command lines.

### Next gate
Compare actual statuses, startup consistency, Task Scheduler multiple-instance policy and listener; ask for a subsequent **separate** evidence-writer cutover authorization only after investigating `TruthCockpitV0145` and `RadarV0144`. Do not create a second writer or switch off the Render canonical writer until durable DB access path, missed-window adjudication and rollback are ready. Free resources without deleting evidence.

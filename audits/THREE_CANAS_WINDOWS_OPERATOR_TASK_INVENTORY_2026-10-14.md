# Local Windows task inventory — operator supplied — 2026-10-14

Read-only Windows output supplied by the operator, NOT remotely or independently inspected by GitHub.

| Scheduled task | PowerShell State |
|---|---|
| CryptoLab-BNB-Operator-AutoLive-V01 | Disabled |
| CryptoLab-OPTIONS-V21-Futures-AutoLive | Disabled |
| CryptoLab-OPTIONS-V21-Telegram-Watcher | Ready |
| CryptoLab-Triple-Fishing-Operator-V03 | Disabled |

Meaning: the three old trading executor tasks are not enabled to launch through their schedules. `Ready` for watcher does not mean it is actively executing and says nothing about account orders. Disabled scheduled tasks do not rule out manually launched executables, other unlisted task names, live broker positions, standing broker stop orders, or asynchronous operator processes. This status was not checked against MEXC via authenticated read-only endpoints.

Safe next checks: inspect names/PIDs of relevant running local processes; independently reconcile all current MEXC Futures positions, open orders and existing TP/SL read-only; inspect installed artefact/strategy parity; build a distinct new 10x 3-signal execution engine. Do NOT enable legacy BNB, OPTIONS, V03 or mutate order/account state. No LIVE_GO; no orders; no secrets; no merge to main.

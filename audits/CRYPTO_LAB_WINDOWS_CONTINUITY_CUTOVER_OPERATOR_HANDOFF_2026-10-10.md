# Crypto Lab — Windows PC continuity cutover V0.1 — operator handoff
Date 2026-10-10. Default posture: **READ-ONLY PREFLIGHT / NO WRITER CUTOVER**.

## Mission
Render Free shadow `crypto-edge-radar-v05-canary` spins down and GH cron has delivered multi-hour gaps. On 2026-10-10, Supabase had at least 26 immutable gap receipts. To obtain real continuous data collection without paying for a new host, evaluate whether the operator's Windows PC can remain always on (mains power, network, wake/reboot recovery), with exactly **one** canonical scientific evidence writer.

## Mandatory first step on Windows
**NO ADMIN required, NO credentials requested.** Download and inspect the official GitHub source of:
`crypto_edge_radar/operator_windows/CryptoLab_PC_Continuity_Readonly_Preflight_V01.ps1`
Run with PowerShell from a local folder:
```powershell
powershell.exe -NoProfile -File ".\CryptoLab_PC_Continuity_Readonly_Preflight_V01.ps1"
```
It creates a local `%TEMP%\CryptoLab_PC_Readonly_Preflight_V01.json` and reports only non-identifying OS capability, Python 3 detection, disk/RAM, DNS, power configuration readability, relevant scheduled-task *counts* and explicit unverified single-writer/sleep states. It does NOT enumerate task commands, credentials, account holdings or usernames. Upload only that JSON result; NEVER Telegram bot token, MEXC keys, Supabase DSN, Windows DPAPI data, PowerShell transcript or public IP.

## Independent CI proof
GitHub Actions Windows hosted runner [run 38057840024](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38057840024): Windows PowerShell 5.1 script executed and parsed successfully, `PC_PREFLIGHT_READONLY_PASS`; DNS 4/4 on that **hosted runner**. This does not prove the operator's PC is ready.

## After operator returns PC JSON
1. Decide whether PC **will be kept on 24/7** and is online under a reliable electrical/network source; estimate net electricity cost. If no, a paid always-on platform is likely required: present actual prospective costs before purchasing anything.
2. Establish the exact local running MEXC operator tasks and risk/single-writer state through separate read-only diagnostics. No override of any open positions, exits, stop/TP/SL.
3. Package one frozen, pinned GitHub binary/source runner with integrity SHA256; **separate** public Radar writer from private MEXC trading executor; use DB access via locally encrypted DPAPI secret with minimum privileges (never accept DSN in chat).
4. Reconcile immutable events, forward cutoff/last persisted timestamps, source clocks, 2026 holdout seal, and missed windows; prove a parallel **read-only** PC observer first.
5. Make the cutover atomic: verify no duplicate writers; quiesce previous Render writer deliberately and confirm quiesced state; only then arm PC public-data **shadow writer**. Maintain a rollback that never enables simultaneous writers.
6. Configure Windows Task Scheduler for auto-start and reboot recovery only after a separate reviewed authority. Use bounded supervision, alerts and restart receipts. Check multi-day real uptime; no claim of 24/7 until evidenced.
7. Prove Telegram read-only alerts continue separately; GitHub scheduled wake can be supplementary, never treated as completeness proof.

## Latest evidence / known blockers
- Render last verified public-shadow deployment `d645891a588c594b69f41938263cc4066652aa9b`, 346/346 CI PASS, fast HTTP bind. It remains subject to Free idle sleep.
- Telegram real status alarm run [38057623784](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38057623784) on default branch `main`: reported CED1D fail-closed, continuity review and degraded health; **`TELEGRAM_DELIVERY_SENT`**, dedup cache saved. Final workflow conclusion **failure is intentional**, to surface non-OK Radar. This run was **push triggered**, not a scheduled firing; schedules remain unverified separately.
- CED1D exact Oct08 AVAXUSDT bookDepth zip + checksum both HTTP 404 between Oct07 200 and Oct09 200; publisher-side isolated source hole, **NO workaround can replace frozen data**.
- OPTIONS 19/50 forward outcomes gross-negative descriptive; TFG 12/12 -1R; no positive fee-inclusive edge certified.

**All activities in this document are research-only until distinct authority; do not place orders or mutate live exchange state.**

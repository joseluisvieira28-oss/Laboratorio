# Triple Fishing V0.3 — diagnostic repair / operator handoff (2026-10-08)

Status: **DRAFT / NO DEPLOYMENT APPROVED / EXCHANGE STATE UNKNOWN**

Code branch: `fix/triple-v03-failclosed-launcher-watch-2026-10-08`; draft PR #164, based on the original operator branch, **not main**.

## Why the old HOTFIX2 cannot be treated as final

Installed HOTFIX2 metadata source SHA: `47ec9997dbd9d68afe2316c9693fcbc4f15f0579`. The installed main EXE and overlay builder match its own original manifest, but are not byte-identical to the validated later package at build source `e581823ae82c6c14ab9ae9d984430ba6e248a9ea`. The installed patched readiness EXE has the later expected SHA. This **does not prove** which stage caused task exit code 1.

Previous runtime last heartbeat was 2026-10-05 19:20:49Z, no process found, ARMED marker absent, Windows scheduled task last run 2026-10-02 14:13:44 with result 1 and AtLogOn-only trigger. The discrepancy between task LastRunTime and heartbeat timestamp remains unexplained. Task Scheduler Operational history is disabled.

## What is changed

- Launcher now writes fixed-schema stage receipts only to `%LOCALAPPDATA%\CryptoLab\TripleFishingV03\diagnostics\TRIPLE_V03_LAUNCH_LAST.json`. Requirements=10, overlay=20, DPAPI=30, environment=40, launcher exception after main starts=50; native main return retains its own exit code, recorded in a diagnostic receipt. No exception messages, credentials or API responses are saved.
- Python supervisor records fatal exception **phase** and sanitized class (not message) in `live_state\TRIPLE_V03_FATAL_LAST.json` and exits 71. It changes no trading rules.
- `Watch_MEXC_Triple_Fishing_V03_ReadOnly.ps1` reports missing, stale, malformed or future heartbeat, task/process presence, and filenames/markers. It **never** starts/restarts/stops/arms/disarms the supervisor or reads credentials, and explicitly marks account verification false.
- Offline synthetic tests run on the CI Windows runner; none require private APIs.

## Operator-safe collection after a successful, verified CI build

**Never run the launcher, installer, overlay or readiness/arm tool just to diagnose.** Do not run `Switch_From_BNB_To_Triple_V03.ps1`. Do not delete receipt/state files, global-slot markers or kill switches. If any exchange position may exist, do not terminate its owner.

1. On GitHub PR #164, open the **Windows build workflow**, require a completed `success` build on the exact desired head SHA, and obtain its single-build artifact. The earlier artifact 11101231947 expired on 2026-10-07. An artifact being present or hashes matching a manifest is necessary but not sufficient to prove market readiness.
2. Unzip to a **new** directory, leaving HOTFIX2 and every existing runtime path untouched. Inspect `BUILD_INFO.json` and `SHA256SUMS.txt`. Independently compare every file's `Get-FileHash -Algorithm SHA256` with its manifest entry. A missing or mismatched file is a fail-closed stop.
3. The included read-only watcher can be invoked from a plain PowerShell session (without Administrator) to inspect the **existing** runtime, even before installing: `& ".\Watch_MEXC_Triple_Fishing_V03_ReadOnly.ps1"`. It does **not** verify MEXC positions or trading authority.
4. Separately obtain **independent account read-only** proof of no open positions, open normal orders, and exchange-hosted TP/SL, plus local active/reconciliation/slot state; never expose API keys, private receipts or secret values.
5. Only after full local and account reconciliation, assess **a separately approved, controlled** install/switch. An unarmed supervisor can still manage a previously owned live position. Do not automatically add a restart trigger or rearm based only on the watchdog.
6. If operator later authorizes a strictly controlled diagnostic launch with a proven empty account, report the fixed-schema `TRIPLE_V03_LAUNCH_LAST.json` and `TRIPLE_V03_FATAL_LAST.json` **after reviewing for private information**, then trace the specific stage. Absence of these new receipts on old HOTFIX2 is expected.

## Scientific and authority boundaries

No strategy thresholds, fees, horizon, signal science, risk sizing, exchange routes or frozen outcomes changed. No merge to main, account calls, orders, live arming, secret extraction or MEXC mutation was performed in this branch. No one may conclude a profitable trading opportunity from a missing supervisor heartbeat. A CI-green EXE is **not** live-authorized.

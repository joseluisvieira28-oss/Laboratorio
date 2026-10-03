# V0.4 ACTIVE authority and controlled Windows handover

Authority issued; installation, arming and exchange/runtime status remain unperformed. The local PASS is owner-reported; its original bytes were not available here. Do not reconstruct or rewrite the receipt. The commands below verify the original locally.

Frozen: 3 slots, one active per symbol, 30 USDT total notional, 14 USDT total initial isolated margin, loss kills 5 USDT daily / 5 USDT rolling 7d. OPTIONS BTC futures LONG/SHORT 1x <=10 USDT; BNB LONG 5x <=10 USDT; DH03 LONG 5x <=10 USDT per position, global capacity 3. Futures only, no auto margin, no blind resend, no late chase. Preserve historical receipts and fee correction overlay.

Use the existing extracted prelive bundle. Download the ACTIVE JSON from this branch into that bundle folder, alongside the existing scripts and EXE. Do not replace the executable or policy. Open Windows PowerShell as the same Windows user that owns DPAPI secrets (elevate if Scheduled Tasks require it).

Run this entire block from the bundle folder. It checks receipt and authority before stopping V0.3. Arming alone creates a local marker; starting V0.4 enables real exchange mutations under the frozen rules. No such action was run by the author of this handover.

```powershell
Set-Location -LiteralPath "$env:USERPROFILE\Downloads\mexc-triple-fishing-multislot-v04-windows-prelive"
$ErrorActionPreference = 'Stop'
$runtime = Join-Path $env:LOCALAPPDATA 'CryptoLab\TripleFishingV04'
$ready = Join-Path $runtime 'live_state\triple_ready_v04.json'
$authorityName = 'OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_ACTIVE.json'
$source = Join-Path (Get-Location).Path $authorityName
$expectedReady = '024024b3482f5d93ecb0e53fe2925374f870b873e031a11b926cc0e2b9baf604'
$expectedAuthority = '2e7769e42e3158be9134e0a405732e7050230673fcb78aa47efdf28854259038'
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower() -ne $expectedAuthority) { throw 'Authority bytes differ. STOP.' }
if ((Get-FileHash -LiteralPath $ready -Algorithm SHA256).Hash.ToLower() -ne $expectedReady) { throw 'Readiness hash differs. STOP; obtain separately reissued authority.' }
$r = Get-Content -Raw -LiteralPath $ready | ConvertFrom-Json
if ($r.pass -ne $true -or $r.status -ne 'PASS_PRELIVE_ACCOUNT_FEASIBILITY' -or @($r.blockers).Count -ne 0) { throw 'Readiness is not clean PASS.' }
if ($r.capacity_target -ne 3 -or $r.position_mode -ne 1) { throw 'Capacity/mode mismatch.' }
if ($r.exchange_state.pass -ne $true -or $r.exchange_state.open_position_count -ne 0 -or $r.exchange_state.open_order_count -ne 0 -or $r.exchange_state.open_tpsl_count -ne 0) { throw 'Account was not empty at readiness.' }
$age = ([DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse($r.checked_at_utc)).TotalSeconds
if ($age -lt 0 -or $age -gt 900) { throw 'Receipt expired. STOP: new Ready Check and new hash-bound authority required.' }
$v03armed = Join-Path $env:LOCALAPPDATA 'CryptoLab\TripleFishingV03\OPERATOR_FUTURES_V03_ARMED.json'
if (Test-Path -LiteralPath $v03armed) { throw 'V0.3 has been rearmed since readiness. STOP.' }
# Confirm MEXC still shows zero positions, orders and TP-SL before proceeding.
# If anything appeared after the receipt, STOP and leave V0.3 managing its exits.
Copy-Item -LiteralPath $source -Destination (Join-Path $runtime $authorityName)
& .\Arm_After_Approved_Handover_MEXC_Triple_Fishing_V04.ps1
if (-not $?) { throw 'Arm failed. STOP.' }
$oldTask = Get-ScheduledTask -TaskName 'CryptoLab-Triple-Fishing-Operator-V03' -ErrorAction Stop
Disable-ScheduledTask -InputObject $oldTask | Out-Null
Stop-ScheduledTask -InputObject $oldTask
Start-Sleep -Seconds 2
$oldTask = Get-ScheduledTask -TaskName 'CryptoLab-Triple-Fishing-Operator-V03'
if ($oldTask.State -ne 'Disabled') { throw 'V0.3 is not disabled. STOP.' }
& .\Install_And_Start_MEXC_Triple_Fishing_V04.ps1
if (-not $?) { throw 'V0.4 install/start failed. STOP; inspect local status.' }
Start-Sleep -Seconds 10
Get-ScheduledTask -TaskName 'CryptoLab-Triple-Fishing-Operator-V03','CryptoLab-Triple-Fishing-Operator-V04' | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName 'CryptoLab-Triple-Fishing-Operator-V04' | Select-Object LastRunTime,LastTaskResult
& .\Status_MEXC_Triple_Fishing_V04.ps1
```

Expected: V0.3 Disabled; V0.4 Running; ACTIVE AUTHORITY True; ARMED True; KILL SWITCH False. Supervisor `version=TRIPLE_FISHING_OPERATOR_V0.4`, `max_simultaneous_positions=3`, three lane IDs, advancing `checked_at_utc`, reservations <=3, no authorization/hash/reconciliation/risk failures. Capacity 3 does not require three immediate positions. DH03 may bootstrap before producing eligible prospective signals. A running task or marker alone does not prove successful engine operation.

Repeat status after 30 seconds to confirm timestamps advance. A long-running task can show LastTaskResult 267009 (0x41301, running); inspect state and engine receipts, not an assumed exit code 0. Verify leverage/notional from actual position receipts if future eligible entries occur.

If the receipt is older than 15 minutes before arming, stop this procedure. Run only `Ready_Check_MEXC_Triple_Fishing_V04.ps1`, send its new complete output and SHA256, and obtain a newly bound authority. Never change receipt timestamps, manually create an armed marker or alter this authority's hash binding. Do not rerun Ready Check after arming/start: it overwrites the hash-bound receipt.

If V0.4 reports a fault after starting, run `Emergency_Stop_MEXC_Triple_Fishing_V04.ps1` to block new entries while preserving owned exit management; collect Status output. Do not restart V0.3 alongside V0.4, delete ledgers/receipts, or blind-resend. Do not stop/disarm a runtime that owns positions.

Issuance does not certify completed live handover or supersede V0.3 before the clean local transition. Main remains untouched. Prior prelive build evidence is recorded in the existing closeout; this closeout adds the exact owner-requested authority and operator instructions only.

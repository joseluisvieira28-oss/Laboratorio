param(
    [string]$RadarRoot = "$env:USERPROFILE\Desktop\CryptoEdgeRadar_V01433_FINAL"
)
$ErrorActionPreference="Continue"
$Data=Join-Path $RadarRoot "data"
$Receipts=Join-Path $RadarRoot "live_receipts"
$Arm=Join-Path $Data "TIER2_AUTOLIVE_ARMED_V03.json"
$Status=Join-Path $Data "tier2_autolive_v03_status.json"

Write-Host ""
Write-Host "================ TIER2 AUTO-LIVE V0.3 STATUS ================"
Write-Host "Checked local: $(Get-Date -Format o)"
$proc=Get-Process -Name "OptionsV21AutoLiveSupervisor" -ErrorAction SilentlyContinue
Write-Host ("Supervisor process       : " + $(if($proc){"RUNNING PID "+(($proc.Id)-join ",")}else{"NOT RUNNING"}))

if (Test-Path $Arm) {
    $a=Get-Content $Arm -Raw | ConvertFrom-Json
    Write-Host "Arming status            : $($a.status)"
    Write-Host "Candidate                : $($a.candidate_id)"
    Write-Host "Allowed lane             : $($a.allowed_lane)"
    Write-Host "Max notional             : $($a.maximum_notional_usdt_equivalent) USDT"
    Write-Host "Expires UTC              : $($a.expires_at_utc)"
} else {
    Write-Host "Arming status            : MISSING / DISARMED"
}
if (Test-Path $Status) {
    $s=Get-Content $Status -Raw | ConvertFrom-Json
    Write-Host "Supervisor state         : $($s.status)"
    Write-Host "Last check UTC           : $($s.checked_at_utc)"
    if ($s.signal_day) { Write-Host "Signal day               : $($s.signal_day)" }
    if ($s.entry_target_utc) { Write-Host "Next entry target UTC    : $($s.entry_target_utc)" }
    if ($null -ne $s.seconds_to_entry) { Write-Host "Seconds to entry         : $($s.seconds_to_entry)" }
    if ($s.reason) { Write-Host "Reason                   : $($s.reason)" }
    if ($s.blocker) { Write-Host "Blocker                  : $($s.blocker)" }
    if ($s.error) { Write-Host "Error                    : $($s.error)" }
} else {
    Write-Host "Supervisor state         : NO STATUS RECEIPT"
}

$active=@()
if (Test-Path $Receipts) {
    $active=Get-ChildItem $Receipts -Recurse -Filter ACTIVE_TRADE_STATE.json -ErrorAction SilentlyContinue | Where-Object {
        -not (Test-Path (Join-Path $_.Directory.FullName "POST_TRADE_RECONCILIATION.json"))
    }
}
Write-Host "Open micro-live receipts : $($active.Count)"
foreach($f in $active) {
    try {
        $x=Get-Content $f.FullName -Raw | ConvertFrom-Json
        Write-Host "  $($x.strategy_id) | $($x.direction) | notional=$($x.planned_notional_usdt) | exit=$($x.exit_target_utc)"
    } catch {}
}

$latestDecision=Get-ChildItem $Data -Filter "options_v21_autolive_decision_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestDecision) {
    $d=Get-Content $latestDecision.FullName -Raw | ConvertFrom-Json
    Write-Host "Latest decision          : $($d.status)"
    Write-Host "Latest decision file     : $($latestDecision.Name)"
}

Write-Host "=============================================================="

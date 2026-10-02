param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$stateDir = Join-Path $runtime "live_state"
$ready = Join-Path $stateDir "triple_ready_v04.json"
$authority = Join-Path $runtime "OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_ACTIVE.json"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V04_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V04_KILL_SWITCH"

if (Test-Path -LiteralPath $kill) { throw "V0.4 kill switch is present." }
if (-not (Test-Path -LiteralPath $ready)) { throw "Missing V0.4 readiness receipt." }
if (-not (Test-Path -LiteralPath $authority)) { throw "Missing separately issued ACTIVE V0.4 authority." }
if (Test-Path -LiteralPath $armed) { throw "V0.4 is already armed." }

$r = Get-Content -Raw -LiteralPath $ready | ConvertFrom-Json
if ($r.readiness_id -ne "MEXC-TRIPLE-FISHING-MULTISLOT-READY-V0.4") { throw "Unexpected readiness id." }
if (-not $r.pass) { throw "Readiness is not PASS." }
$checked = [DateTimeOffset]::Parse($r.checked_at_utc)
$age = ([DateTimeOffset]::UtcNow - $checked).TotalSeconds
if ($age -lt 0 -or $age -gt 900) { throw "Readiness is older than 15 minutes. Run Ready Check again." }

$readyHash = (Get-FileHash -LiteralPath $ready -Algorithm SHA256).Hash.ToLower()
$a = Get-Content -Raw -LiteralPath $authority | ConvertFrom-Json
if ($a.authority_id -ne "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE") { throw "Unexpected ACTIVE authority id." }
if ($a.status -ne "ACTIVE") { throw "V0.4 authority is not ACTIVE." }
if ([int]$a.risk.max_simultaneous_positions -ne 3) { throw "Authority does not freeze exactly 3 slots." }
if ([string]$a.readiness_receipt_sha256 -ne $readyHash) { throw "ACTIVE authority is not bound to this exact readiness receipt." }
$authorityHash = (Get-FileHash -LiteralPath $authority -Algorithm SHA256).Hash.ToLower()

$payload = [ordered]@{
    authority = "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE"
    max_simultaneous_positions = 3
    armed_at_utc = [DateTimeOffset]::UtcNow.ToString("o")
    readiness_receipt_sha256 = $readyHash
    active_authority_sha256 = $authorityHash
}
$tmp = $armed + ".tmp"
$payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $tmp -Encoding UTF8
Move-Item -Force -LiteralPath $tmp -Destination $armed
Write-Host "V0.4 ARMED MARKER CREATED"
Write-Host ("READINESS_SHA256=" + $readyHash)
Write-Host ("AUTHORITY_SHA256=" + $authorityHash)

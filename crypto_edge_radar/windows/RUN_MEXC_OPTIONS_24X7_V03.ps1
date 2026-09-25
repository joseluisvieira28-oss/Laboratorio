param([switch]$Live)
$ErrorActionPreference="Stop"
$cycle=Join-Path $PSScriptRoot "Run_MEXC_OPTIONS_Auto_Cycle_V03.ps1"
$recover=Join-Path $PSScriptRoot "Recover_MEXC_OPTIONS_Exits_V03.ps1"

if ($Live) { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $recover -Live } else { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $recover }

Write-Host ("OPTIONS V2.1 V0.3 watchdog started. Mode=" + $(if($Live){"LIVE_GATED"}else{"DRY_RUN"}))
while ($true) {
  $now=[DateTime]::UtcNow
  $midnight=$now.Date
  $elapsed=($now-$midnight).TotalSeconds
  if ($elapsed -le 25) { $target=$midnight.AddMilliseconds(500) }
  else { $target=$midnight.AddDays(1).AddMilliseconds(500) }

  while ($true) {
    $remaining=($target-[DateTime]::UtcNow).TotalMilliseconds
    if ($remaining -le 0) { break }
    if ($remaining -gt 60000) {
      $sleep=[Math]::Max(1,[Math]::Min(60,[Math]::Floor($remaining/1000)-1))
      Start-Sleep -Seconds $sleep
    }
    elseif ($remaining -gt 1000) { Start-Sleep -Milliseconds 500 }
    else { Start-Sleep -Milliseconds ([Math]::Max(20,[Math]::Floor($remaining))) }
  }

  $attempt=0
  while (([DateTime]::UtcNow-$target.Date).TotalSeconds -lt 28 -and $attempt -lt 2) {
    $attempt++
    Write-Host ("UTC cycle attempt " + $attempt + " at " + [DateTime]::UtcNow.ToString("o"))
    if ($Live) { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cycle -Live } else { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cycle }
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 2
  }
  Start-Sleep -Seconds 35
}

# Unified READ-ONLY health and installed-SHA receipt for EXACTLY TEN CONVEX lanes.
# No scripts executed, no Telegram API, no MEXC calls, no secrets or task actions printed.
$ErrorActionPreference='Stop'
$items=@(
    @{Ver='V07';Task='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly';Dir='ThreeConvexV07';Exe='V07_Telegram_MEXC_Watcher.exe';Status='V07_WATCHER_STATUS.json';Lanes=3;ExpectedHash='99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84'},
    @{Ver='V11';Task='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly';Dir='ThreeConvexV11';Exe='V11_Experimental_Signals.exe';Status='V11_STATUS.json';Lanes=3;ExpectedHash='8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc'},
    @{Ver='V12';Task='CryptoLab-CONVEX-V12-FinalFour-ReadOnly';Dir='ThreeConvexV12';Exe='V12_FinalFour_Signals.exe';Status='V12_STATUS.json';Lanes=4;ExpectedHash=$null}
)
$now=[datetime]::UtcNow
$rows=@()
foreach($i in $items) {
    $task=Get-ScheduledTask -TaskName $i.Task -ErrorAction SilentlyContinue
    $root=Join-Path $env:LOCALAPPDATA ('CryptoLab\'+$i.Dir)
    $binary=Join-Path $root $i.Exe
    $data=Join-Path (Join-Path $root 'data') $i.Status
    $s=$null
    $err=$null
    if (Test-Path -LiteralPath $data -PathType Leaf) {
        try {$s=Get-Content -LiteralPath $data -Raw | ConvertFrom-Json} catch {$err='STATUS_NOT_JSON'}
    } else {$err='STATUS_MISSING'}
    $age=$null
    if (Test-Path -LiteralPath $data -PathType Leaf) {
        $age=[math]::Round(($now-(Get-Item -LiteralPath $data).LastWriteTimeUtc).TotalMinutes,2)
    }
    $sha=$null
    if (Test-Path -LiteralPath $binary -PathType Leaf) {
        $sha=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $healthyStatus=switch($i.Ver) {
        'V07' { $s -and $s.status -eq 'V07_TELEGRAM_PUBLIC_SIGNALS_AND_AUTH_MEXC_READONLY' -and $s.v5_public_source_ok -eq $true }
        'V11' { $s -and $s.status -eq 'V11_EXPERIMENTAL_READONLY' -and $s.sources_ok -eq $true }
        'V12' { $s -and $s.status -eq 'V12_EXPERIMENTAL_READONLY' -and $s.sources_ok -eq $true -and $s.total_inventory -eq 10 }
    }
    $running=$task -and [string]$task.State -eq 'Running'
    $fresh=$age -ne $null -and $age -ge -0.5 -and $age -le 5
    $rows += [pscustomobject]@{
        version=$i.Ver;lane_count=$i.Lanes;task_state=if($task){[string]$task.State}else{'MISSING'};
        process_count=@(Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($i.Exe)) -ErrorAction SilentlyContinue).Count;
        report_age_minutes=$age;report_status=if($s){$s.status}else{$err};
        source_healthy=[bool]$healthyStatus;source_status=if($s){$s.source_status}else{$null};
        sha256=$sha;matches_audit_v2=if($i.ExpectedHash){$sha -eq $i.ExpectedHash}else{$null};
        monitor_healthy_now=[bool]($running -and $fresh -and $healthyStatus)
    }
}
$old=Get-ScheduledTask -TaskName 'CryptoLab-OPTIONS-V21-Telegram-Watcher' -ErrorAction SilentlyContinue
$result=[pscustomobject]@{
    inventory='CONVEX_EXACT_TEN_READONLY_RECEIPT';
    checked_utc=$now.ToString('o');
    expected_lanes=10;
    installed_lanes=($rows|Measure-Object -Property lane_count -Sum).Sum;
    all_three_monitors_healthy=[bool](@($rows|Where-Object{-not $_.monitor_healthy_now}).Count -eq 0);
    legacy_options_telegram_task=if($old){[string]$old.State}else{'NOT_FOUND'};
    monitors=$rows;
    note='No external API requests; Telegram end-to-end signal ACK still unproven.'
}
$result|ConvertTo-Json -Depth 8
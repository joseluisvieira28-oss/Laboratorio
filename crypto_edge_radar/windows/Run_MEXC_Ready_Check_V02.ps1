$ErrorActionPreference = "Stop"

$radarRoot = Split-Path -Parent $PSScriptRoot
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"

function Unprotect-LocalSecret([string]$Path) {
    $cipher = Get-Content -Raw -Path $Path
    $secure = ConvertTo-SecureString $cipher
    $credential = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $credential.GetNetworkCredential().Password
}

if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath)) {
    throw "MEXC DPAPI credentials not found. Run Set_MEXC_Preflight_Secrets.ps1 once first."
}

$apiKey=$null
$apiSecret=$null
$expectedEquity=$null
try {
    $apiKey=Unprotect-LocalSecret $keyPath
    $apiSecret=Unprotect-LocalSecret $secretPath
    $expectedEquity=Read-Host "MEXC Futures equity USDT shown in the app"
    if ([string]::IsNullOrWhiteSpace($expectedEquity)) {
        throw "Expected equity is required for account identity binding."
    }

    $env:MEXC_API_KEY=$apiKey
    $env:MEXC_API_SECRET=$apiSecret
    $env:MEXC_EXPECTED_FUTURES_EQUITY_USDT=$expectedEquity

    Push-Location $radarRoot
    try {
        $preflightExe=Join-Path $radarRoot "dist\MEXCAuthenticatedPreflight.exe"
        if (Test-Path $preflightExe) {
            & $preflightExe
            $preflightExit=$LASTEXITCODE
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            & python ".\scripts\mexc_authenticated_preflight.py"
            $preflightExit=$LASTEXITCODE
        } else {
            throw "MEXCAuthenticatedPreflight.exe and Python are both unavailable."
        }

        $receipt=Join-Path $radarRoot "mexc_authenticated_preflight_receipt.json"
        if (-not (Test-Path $receipt)) { throw "Preflight receipt was not created." }
        $pf=Get-Content $receipt -Raw | ConvertFrom-Json

        Write-Host ""
        Write-Host "================ CRYPTO LAB MEXC READY CHECK V0.2 ================"
        if ($pf.pass -eq $true -and $pf.status -eq "PASS") {
            Write-Host "MEXC AUTHENTICATED PREFLIGHT : PASS"
        } else {
            Write-Host "MEXC AUTHENTICATED PREFLIGHT : FAIL_CLOSED"
            Write-Host ("Exchange blockers          : " + (($pf.blockers | ForEach-Object { $_ }) -join ", "))
        }

        $candidate=$pf.candidate_feasibility.'ETF-CME-INSTFLOW-001'
        if ($null -ne $candidate -and $candidate.pass -eq $true) {
            Write-Host "ETF-CME CAPITAL FEASIBILITY : PASS"
        } else {
            Write-Host "ETF-CME CAPITAL FEASIBILITY : BLOCKED"
            if ($null -ne $candidate) {
                Write-Host ("Candidate blockers         : " + (($candidate.blockers | ForEach-Object { $_ }) -join ", "))
            }
        }

        $riskOut=Join-Path $radarRoot "mexc_account_risk_state.json"
        $riskRoot=Join-Path $radarRoot "live_receipts"
        $riskExe=Join-Path $radarRoot "dist\MEXCRiskState.exe"
        $risk=$null

        if (Test-Path $riskExe) {
            $riskArgs=@(
                "--preflight", $receipt,
                "--receipt-root", $riskRoot,
                "--out", $riskOut
            )
            $proc=Start-Process -FilePath $riskExe -ArgumentList $riskArgs -NoNewWindow -Wait -PassThru
            $riskExit=$proc.ExitCode
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            & python ".\scripts\mexc_risk_state.py" --preflight $receipt --receipt-root $riskRoot --out $riskOut
            $riskExit=$LASTEXITCODE
        } else {
            throw "MEXCRiskState.exe and Python are both unavailable."
        }

        if ($riskExit -ne 0) {
            throw "MEXC risk-state generator failed closed with exit code $riskExit."
        }
        if (-not (Test-Path $riskOut)) {
            throw "Risk-state receipt was not created."
        }

        $risk=Get-Content $riskOut -Raw | ConvertFrom-Json
        Write-Host ("ACCOUNT RISK FIREWALL       : " + $risk.status)
        Write-Host ("Daily realized loss         : " + ([math]::Round(100*[double]$risk.daily_realized_loss_fraction_equity,4)) + "%")
        Write-Host ("Weekly realized loss        : " + ([math]::Round(100*[double]$risk.weekly_realized_loss_fraction_equity,4)) + "%")
        Write-Host ("Concurrent planned risk     : " + ([math]::Round(100*[double]$risk.concurrent_planned_risk_fraction_equity,4)) + "%")

        Write-Host "-------------------------------------------------------------------"
        if ($pf.pass -eq $true -and $null -ne $candidate -and $candidate.pass -eq $true -and $risk.status -eq "PASS") {
            Write-Host "STATE: INFRA READY. CANDIDATE STILL REQUIRES CANONICAL SIGNAL + IMMUTABLE ACTIVE AUTHORITY."
        } elseif ($pf.pass -eq $true) {
            Write-Host "STATE: MEXC READY / CANDIDATE BLOCKED. NO ORDER."
        } else {
            Write-Host "STATE: EXCHANGE PREFLIGHT BLOCKED. NO ORDER."
        }
        Write-Host "This check never creates an order or changes exchange state."
        Write-Host "==================================================================="
        Write-Host ""
        Write-Host "Sanitized preflight receipt: $receipt"
        Write-Host "Risk state receipt: $riskOut"

        if ($pf.pass -ne $true) { exit 2 }
        exit 0
    }
    finally {
        Pop-Location
    }
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_EXPECTED_FUTURES_EQUITY_USDT -ErrorAction SilentlyContinue
    $expectedEquity=$null
    $apiKey=$null
    $apiSecret=$null
}

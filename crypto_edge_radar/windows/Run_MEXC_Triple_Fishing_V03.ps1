param([string]$BundleRoot = $PSScriptRoot)

# Diagnostic-only hardening: no changes to the signal, risk, slot, or arming gates.
# Never record secrets, raw exceptions, command arguments, HTTP replies, or stdout/stderr.
$ErrorActionPreference = "Stop"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$receiptRoot = Join-Path $runtime "live_receipts\operator_futures_v03"
$stateDir = Join-Path $runtime "live_state"
$dataDir = Join-Path $runtime "data"
$archiveRoot = Join-Path $runtime "historical_options_receipts"
$overlay = Join-Path $stateDir "OPTIONS_V21_PNL_CORRECTION_OVERLAY_V01.json"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V03_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V03_KILL_SWITCH"
$slot = Join-Path $stateDir "GLOBAL_POSITION_SLOT_V03.json"

$mainExe = Join-Path $BundleRoot "MEXCTripleFishingOperatorV03.exe"
$overlayExe = Join-Path $BundleRoot "BuildOptionsCorrectionOverlayV01.exe"
$catalog = Join-Path $BundleRoot "OPTIONS_V21_HISTORICAL_FEE_CORRECTION_CATALOG_V01.json"
$eventLog = Join-Path $stateDir "launcher_events_v03.jsonl"
$runId = [guid]::NewGuid().ToString("N")
$stage = "INIT"
$exitCode = 70
$hasLog = $false

function Write-LaunchEvent {
    param([string]$Stage, [string]$Outcome, [int]$Code)
    $event = [ordered]@{
        schema = "TRIPLE_LAUNCHER_DIAGNOSTIC_V0.1"
        run_id = $runId
        checked_at_utc = [DateTime]::UtcNow.ToString("o")
        stage = $Stage
        result = $Outcome
        numeric_code = $Code
        # Marker existence is diagnostic metadata, not exchange-position proof.
        armed_marker_exists = [bool](Test-Path -LiteralPath $armed)
        kill_switch_exists = [bool](Test-Path -LiteralPath $kill)
        local_slot_file_exists = [bool](Test-Path -LiteralPath $slot)
    }
    $line = $event | ConvertTo-Json -Compress -Depth 3
    Add-Content -LiteralPath $eventLog -Value $line -Encoding UTF8 -ErrorAction Stop
}

$apiKey = $null
$apiSecret = $null
try {
    $stage = "CREATE_RUNTIME_DIRECTORIES"
    New-Item -ItemType Directory -Force -Path $runtime,$receiptRoot,$stateDir,$dataDir -ErrorAction Stop | Out-Null
    $hasLog = $true
    Write-LaunchEvent "LAUNCHER_START" "BEGIN" 0

    $stage = "VALIDATE_DEPENDENCIES"
    foreach ($p in @($mainExe,$overlayExe,$catalog,$archiveRoot)) {
        if (-not (Test-Path -LiteralPath $p)) {
            $exitCode = 11
            Write-LaunchEvent "VALIDATE_DEPENDENCIES" "MISSING" $exitCode
            throw [System.InvalidOperationException]::new("Required launcher input absent")
        }
    }
    Write-LaunchEvent "VALIDATE_DEPENDENCIES" "PASS" 0

    $stage = "BUILD_OPTIONS_OVERLAY"
    & $overlayExe --catalog $catalog --receipt-root $archiveRoot --out $overlay
    $overlayChildCode = [int]$LASTEXITCODE
    if ($overlayChildCode -ne 0) {
        $exitCode = 21
        Write-LaunchEvent "BUILD_OPTIONS_OVERLAY" "CHILD_NONZERO" $overlayChildCode
        throw [System.InvalidOperationException]::new("Overlay failed closed")
    }
    if (-not (Test-Path -LiteralPath $overlay -PathType Leaf)) {
        $exitCode = 22
        Write-LaunchEvent "BUILD_OPTIONS_OVERLAY" "OUTPUT_MISSING" $exitCode
        throw [System.InvalidOperationException]::new("Overlay output absent")
    }
    Write-LaunchEvent "BUILD_OPTIONS_OVERLAY" "PASS" 0

    $stage = "LOAD_DPAPI"
    $secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
    $keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
    $secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"
    function Unprotect-LocalSecret {
        param([string]$Path)
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            throw [System.InvalidOperationException]::new("DPAPI secret missing")
        }
        # Set-Content appends a record terminator; it is not part of the
        # DPAPI hex payload. Strip only terminal CR/LF, never internal data.
        $cipher = (Get-Content -Raw -LiteralPath $Path -ErrorAction Stop).TrimEnd([char[]]"`r`n")
        if ([string]::IsNullOrEmpty($cipher) -or $cipher -notmatch '\A(?:[0-9a-fA-F]{2})+\z') {
            throw [System.InvalidOperationException]::new("DPAPI payload invalid")
        }
        $secure = ConvertTo-SecureString $cipher -ErrorAction Stop
        $cred = New-Object System.Management.Automation.PSCredential("local", $secure)
        return $cred.GetNetworkCredential().Password
    }
    $apiKey = Unprotect-LocalSecret $keyPath
    $apiSecret = Unprotect-LocalSecret $secretPath
    if ([string]::IsNullOrWhiteSpace($apiKey) -or [string]::IsNullOrWhiteSpace($apiSecret)) {
        throw [System.InvalidOperationException]::new("DPAPI value empty")
    }
    Write-LaunchEvent "LOAD_DPAPI" "PASS" 0

    $env:MEXC_API_KEY = $apiKey
    $env:MEXC_API_SECRET = $apiSecret
    $env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY = $overlay

    $roots = @($archiveRoot)
    $legacyBnbReceipts = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02\live_receipts"
    if (Test-Path -LiteralPath $legacyBnbReceipts) { $roots += $legacyBnbReceipts }
    $env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS = ($roots -join [IO.Path]::PathSeparator)

    $mainArgs = @(
        "--receipt-root",$receiptRoot,
        "--armed-path",$armed,
        "--kill-switch",$kill,
        "--status-path",(Join-Path $stateDir "operator_futures_engine_v03.json"),
        "--global-slot-path",$slot,
        "--supervisor-state",(Join-Path $stateDir "triple_fishing_operator_v03.json"),
        "--bnb-state",(Join-Path $stateDir "bnb_operator_source_v03.json"),
        "--options-db",(Join-Path $dataDir "options_v21_operator.sqlite3"),
        "--options-state",(Join-Path $stateDir "options_v21_operator_source_v03.json"),
        "--dh03-market-db",(Join-Path $dataDir "dh03_market.sqlite3"),
        "--dh03-evidence-db",(Join-Path $dataDir "dh03_evidence.sqlite3"),
        "--dh03-state",(Join-Path $stateDir "dh03_operator_source_v03.json")
    )
    $stage = "RUN_SUPERVISOR"
    Write-LaunchEvent "RUN_SUPERVISOR" "CHILD_START" 0
    & $mainExe @mainArgs
    $mainChildCode = [int]$LASTEXITCODE
    if ($mainChildCode -ne 0) {
        $exitCode = 41
        Write-LaunchEvent "RUN_SUPERVISOR" "CHILD_NONZERO" $mainChildCode
    }
    else {
        # A continuously running supervisor is not expected to exit on its own.
        $exitCode = 42
        Write-LaunchEvent "RUN_SUPERVISOR" "UNEXPECTED_CLEAN_EXIT" 0
    }
}
catch {
    # Report ONLY the stage and fixed numeric class, never $_, exceptions,
    # raw account data, filenames from exceptions, or secret values.
    if ($exitCode -eq 70) {
        switch ($stage) {
            "CREATE_RUNTIME_DIRECTORIES" { $exitCode = 90 }
            "VALIDATE_DEPENDENCIES" { $exitCode = 12 }
            "BUILD_OPTIONS_OVERLAY" { $exitCode = 23 }
            "LOAD_DPAPI" { $exitCode = 31 }
            "RUN_SUPERVISOR" { $exitCode = 43 }
            default { $exitCode = 70 }
        }
    }
    if ($hasLog) {
        try { Write-LaunchEvent $stage "FAIL_CLOSED" $exitCode }
        catch { $exitCode = 90 }
    }
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS -ErrorAction SilentlyContinue
    $apiKey = $null
    $apiSecret = $null
}
exit $exitCode

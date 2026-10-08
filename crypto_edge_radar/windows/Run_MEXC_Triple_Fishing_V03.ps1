param([string]$BundleRoot = $PSScriptRoot)

# Operator launcher. Do not arm, disarm, reset a slot or place an order here.
# Diagnostics contain fixed stage codes only: never exception strings, stdout,
# stderr, command-line arguments, credentials or exchange/account responses.
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
$diagnosticFile = Join-Path $runtime "diagnostics\TRIPLE_V03_LAUNCH_LAST.json"

function Write-TripleLaunchReceipt {
    param(
        [ValidateSet("REQUIREMENTS", "OVERLAY", "DPAPI", "ENVIRONMENT", "MAIN", "MAIN_RETURNED")]
        [string]$Stage,
        [int]$ExitCode,
        [string]$Status = "FAIL_CLOSED",
        [Nullable[int]]$ChildExitCode = $null
    )
    # This fixed schema is intentionally incapable of persisting arbitrary errors.
    try {
        $directory = Split-Path -Parent $diagnosticFile
        [void](New-Item -ItemType Directory -Force -Path $directory)
        $record = [ordered]@{
            schema = "TRIPLE_V03_LAUNCH_DIAGNOSTIC_V01"
            observed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
            stage = $Stage
            status = $Status
            exit_code = $ExitCode
            child_exit_code = $ChildExitCode
            contains_secrets = $false
            orders_created_by_diagnostic = $false
        }
        $temporary = "$diagnosticFile.tmp"
        [System.IO.File]::WriteAllText(
            $temporary,
            ($record | ConvertTo-Json -Depth 3 -Compress),
            [System.Text.UTF8Encoding]::new($false)
        )
        Move-Item -LiteralPath $temporary -Destination $diagnosticFile -Force
    } catch {
        # Diagnostics are best effort: never output exception text or alter safety.
        Write-Warning "TRIPLE_V03_DIAGNOSTIC_WRITE_FAILED"
    }
}

$stage = "REQUIREMENTS"
$apiKey = $null
$apiSecret = $null

function Unprotect-LocalSecret {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "LOCAL_SECRET_MISSING" }
    $cipher = Get-Content -Raw -LiteralPath $Path
    $secure = ConvertTo-SecureString $cipher
    $cred = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $cred.GetNetworkCredential().Password
}

try {
    [void](New-Item -ItemType Directory -Force -Path $runtime,$receiptRoot,$stateDir,$dataDir)
    foreach ($p in @($mainExe,$overlayExe,$catalog,$archiveRoot)) {
        if (-not (Test-Path -LiteralPath $p)) { throw "REQUIRED_PATH_MISSING" }
    }

    $stage = "OVERLAY"
    & $overlayExe --catalog $catalog --receipt-root $archiveRoot --out $overlay
    $overlayCode = $LASTEXITCODE
    if ($overlayCode -ne 0) { throw "OVERLAY_FAILED_CLOSED" }

    $stage = "DPAPI"
    $secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
    $apiKey = Unprotect-LocalSecret (Join-Path $secretDir "mexc_api_key.dpapi")
    $apiSecret = Unprotect-LocalSecret (Join-Path $secretDir "mexc_api_secret.dpapi")

    $stage = "ENVIRONMENT"
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

    $stage = "MAIN"
    & $mainExe @mainArgs
    $mainExit = $LASTEXITCODE
    if ($null -eq $mainExit) { $mainExit = 70 }

    # A returned long-running supervisor is not proof of operational health.
    Write-TripleLaunchReceipt -Stage "MAIN_RETURNED" -ExitCode ([int]$mainExit) -ChildExitCode ([int]$mainExit) -Status "PROCESS_RETURNED"
    Write-Host ("TRIPLE_V03_LAUNCH_STAGE=MAIN_RETURNED EXIT_CODE=" + [int]$mainExit)
    exit ([int]$mainExit)
} catch {
    # No exception messages; they may contain secrets or private API payloads.
    $exitCode = switch ($stage) {
        "REQUIREMENTS" { 10 }
        "OVERLAY" { 20 }
        "DPAPI" { 30 }
        "ENVIRONMENT" { 40 }
        "MAIN" { 50 }
        default { 70 }
    }
    Write-TripleLaunchReceipt -Stage $stage -ExitCode $exitCode
    Write-Host ("TRIPLE_V03_LAUNCH_STAGE=" + $stage + " EXIT_CODE=" + $exitCode)
    exit $exitCode
} finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS -ErrorAction SilentlyContinue
    $apiKey = $null
    $apiSecret = $null
}

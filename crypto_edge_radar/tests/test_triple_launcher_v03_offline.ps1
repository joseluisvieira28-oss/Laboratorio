# Offline-only synthetic launcher tests. NEVER use installed CryptoLab state.
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '..\windows\Run_MEXC_Triple_Fishing_V03.ps1'
$source = (Resolve-Path -LiteralPath $source).Path

$tokens = $null; $parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw "Launcher PowerShell parser errors: $($parseErrors.Count)" }

$root = Join-Path $env:RUNNER_TEMP ('triple-v03-launcher-test-' + [guid]::NewGuid().ToString('N'))
$originalLocalAppData = $env:LOCALAPPDATA
$originalStubExit = $env:TRIPLE_TEST_OVERLAY_EXIT
$testPasses = 0
New-Item -ItemType Directory -Force -Path $root | Out-Null
try {
    $env:LOCALAPPDATA = Join-Path $root 'isolated-profile'
    New-Item -ItemType Directory -Force -Path $env:LOCALAPPDATA | Out-Null
    $bundle = Join-Path $root 'mock-bundle'
    New-Item -ItemType Directory -Force -Path $bundle | Out-Null

    $runtime = Join-Path $env:LOCALAPPDATA 'CryptoLab\TripleFishingV03'
    $state = Join-Path $runtime 'live_state'
    $log = Join-Path $state 'launcher_events_v03.jsonl'
    $slot = Join-Path $state 'GLOBAL_POSITION_SLOT_V03.json'
    $marker = Join-Path $runtime 'OPERATOR_FUTURES_V03_ARMED.json'
    $kill = Join-Path $runtime 'OPERATOR_FUTURES_V03_KILL_SWITCH'

    function Test-Case {
        param([int]$ExpectedExit,[string]$Stage,[string]$Result)
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $source -BundleRoot $bundle *> $null
        $actual = $LASTEXITCODE
        if ($actual -ne $ExpectedExit) { throw "Expected launcher exit $ExpectedExit, got $actual" }
        $events = @(Get-Content -LiteralPath $log -ErrorAction Stop | Where-Object { $_ } | ForEach-Object { $_ | ConvertFrom-Json })
        $last = $events[-1]
        if ($last.stage -ne $Stage -or $last.result -ne $Result) {
            throw "Unexpected final event: $($last.stage) / $($last.result)"
        }
        if ($events | Where-Object { $_.PSObject.Properties.Name -match 'secret|credential|token|api_key|response' }) {
            throw 'Unexpected sensitive field in diagnostic event'
        }
        $script:testPasses++
    }

    # 1. Missing required path must fail without starting any executable.
    Test-Case -ExpectedExit 11 -Stage 'VALIDATE_DEPENDENCIES' -Result 'FAIL_CLOSED'
    New-Item -ItemType Directory -Force -Path $state | Out-Null
    $slotContent = '{"synthetic_test_only":true}'
    [IO.File]::WriteAllText($slot,$slotContent)
    [IO.File]::WriteAllText($marker,'{"synthetic_test_only":true}')
    [IO.File]::WriteAllText($kill,'synthetic_test_only')

    # Compile two inert offline child programs. Both filenames are production-shaped;
    # neither file contains exchange code or imports network clients.
    $cs = @'
using System;
using System.IO;
public class TripleLauncherTestStub {
    public static int Main(string[] args) {
        string exe = System.Diagnostics.Process.GetCurrentProcess().MainModule.FileName;
        if (Path.GetFileName(exe).StartsWith("BuildOptions")) {
            int overlayExit;
            if (Int32.TryParse(Environment.GetEnvironmentVariable("TRIPLE_TEST_OVERLAY_EXIT"), out overlayExit) && overlayExit != 0)
                return overlayExit;
            for (int i = 0; i + 1 < args.Length; i++) {
                if (args[i] == "--out") { 
                    Directory.CreateDirectory(Path.GetDirectoryName(args[i+1]));
                    File.WriteAllText(args[i+1], "{\"overlay_id\":\"SYNTHETIC_TEST_ONLY\"}");
                    return 0;
                }
            }
            return 18;
        }
        File.WriteAllText(Path.Combine(Environment.GetEnvironmentVariable("LOCALAPPDATA"),"TRIPLE_STUB_MAIN_CALLED"),"synthetic");
        return 17;
    }
}
'@
    $stubPath = Join-Path $bundle 'stub.exe'
    Add-Type -TypeDefinition $cs -OutputAssembly $stubPath -OutputType ConsoleApplication
    Copy-Item $stubPath (Join-Path $bundle 'MEXCTripleFishingOperatorV03.exe')
    Copy-Item $stubPath (Join-Path $bundle 'BuildOptionsCorrectionOverlayV01.exe')
    [IO.File]::WriteAllText((Join-Path $bundle 'OPTIONS_V21_HISTORICAL_FEE_CORRECTION_CATALOG_V01.json'),'{"synthetic_test_only":true}')
    New-Item -ItemType Directory -Force -Path (Join-Path $runtime 'historical_options_receipts') | Out-Null

    # 2. Child overlay fails: no DPAPI or supervisor executable should start.
    $env:TRIPLE_TEST_OVERLAY_EXIT = '2'
    Test-Case -ExpectedExit 21 -Stage 'BUILD_OPTIONS_OVERLAY' -Result 'FAIL_CLOSED'
    if (Test-Path (Join-Path $env:LOCALAPPDATA 'TRIPLE_STUB_MAIN_CALLED')) { throw 'Main started despite overlay failure' }

    # 3. Overlay succeeds; absent DPAPI files must block before the main child.
    $env:TRIPLE_TEST_OVERLAY_EXIT = '0'
    Test-Case -ExpectedExit 31 -Stage 'LOAD_DPAPI' -Result 'FAIL_CLOSED'
    if (Test-Path (Join-Path $env:LOCALAPPDATA 'TRIPLE_STUB_MAIN_CALLED')) { throw 'Main started without DPAPI' }

    # 4. Synthetic DPAPI generated under isolated user/profile; child fails with 17.
    # This does NOT use or test real MEXC secrets or account.
    $secretDir = Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets'
    New-Item -ItemType Directory -Force -Path $secretDir | Out-Null
    $fake = ConvertTo-SecureString 'SYNTHETIC_NON_SECRET_TEST_VALUE' -AsPlainText -Force | ConvertFrom-SecureString
    Set-Content -LiteralPath (Join-Path $secretDir 'mexc_api_key.dpapi') -Value $fake
    Set-Content -LiteralPath (Join-Path $secretDir 'mexc_api_secret.dpapi') -Value $fake
    Test-Case -ExpectedExit 41 -Stage 'RUN_SUPERVISOR' -Result 'CHILD_NONZERO'
    if (-not (Test-Path (Join-Path $env:LOCALAPPDATA 'TRIPLE_STUB_MAIN_CALLED'))) { throw 'Inert test child was not reached' }

    if ([IO.File]::ReadAllText($slot) -ne $slotContent -or -not (Test-Path $marker) -or -not (Test-Path $kill)) {
        throw 'Runner changed a persisted slot or protective marker'
    }
    Write-Output "TRIPLE_LAUNCHER_OFFLINE_INERT_TESTS_PASS: $testPasses / 4"
} finally {
    $env:LOCALAPPDATA = $originalLocalAppData
    $env:TRIPLE_TEST_OVERLAY_EXIT = $originalStubExit
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}

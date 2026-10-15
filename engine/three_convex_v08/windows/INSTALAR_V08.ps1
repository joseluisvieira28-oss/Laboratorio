# V08 Windows package installer. One-time local install, NO scheduled trade service.
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'CryptoLab_V08_Futures_Executor_PreLive.exe'
$manifest=Join-Path $PSScriptRoot 'SHA256_EXE.txt'
if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or
    -not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw 'V08_ZIP_INCOMPLETO_REEXTRAIR_EM_PASTA_NOVA'
}
$expected=([string](Get-Content -LiteralPath $manifest -Raw)).Trim().Replace('SHA256_EXE=','').ToLowerInvariant()
$actual=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) {
    throw 'V08_EXE_HASH_MISMATCH_DO_NOT_EXECUTE'
}
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV08'
New-Item -ItemType Directory -Force -Path $root,(Join-Path $root 'data') | Out-Null
Copy-Item -LiteralPath $source -Destination (Join-Path $root 'CryptoLab_V08_Futures_Executor_PreLive.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'VERIFICAR_V08.ps1') -Destination (Join-Path $root 'VERIFICAR_V08.ps1') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ESTADO_V08.ps1') -Destination (Join-Path $root 'ESTADO_V08.ps1') -Force
& (Join-Path $root 'CryptoLab_V08_Futures_Executor_PreLive.exe') --synthetic-proof --data-dir (Join-Path $root 'data')
if ($LASTEXITCODE -ne 0) {
    throw 'V08_OFFLINE_SYNTHETIC_STOP_PROOF_FAILED'
}
Write-Output 'V08_INSTALADO_WINDOWS: SIM'
Write-Output 'MODO: PRELIVE_SEGURANCA_DO_EXECUTOR (SEM_ORDENS_REAIS)'
Write-Output 'V07_TELEGRAM: PRESERVADO_NAO_ALTERADO'
Write-Output 'MEXC: NENHUM_POST_NENHUMA_ORDEM'
Write-Output 'AGORA: executar .\VERIFICAR_V08.ps1 na pasta ZIP, para MEXC GET autenticado'

$ErrorActionPreference = "Stop"

$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null

Write-Host "MEXC dedicated API credentials will be encrypted with Windows DPAPI for this Windows user."
Write-Host "Nothing is written to GitHub, Google Drive, Render, or chat."

$apiKey = Read-Host "MEXC API Key" -AsSecureString
$apiSecret = Read-Host "MEXC API Secret" -AsSecureString

$apiKeyCipher = ConvertFrom-SecureString $apiKey
$apiSecretCipher = ConvertFrom-SecureString $apiSecret

Set-Content -Path (Join-Path $secretDir "mexc_api_key.dpapi") -Value $apiKeyCipher -Encoding ASCII -NoNewline
Set-Content -Path (Join-Path $secretDir "mexc_api_secret.dpapi") -Value $apiSecretCipher -Encoding ASCII -NoNewline

$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Harden the local DPAPI secret directory without touching the SACL.
# Set-Acl can require SeSecurityPrivilege on some Windows configurations,
# even when the current user owns the directory. icacls only changes the DACL.
& icacls.exe $secretDir /inheritance:r | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to disable inherited ACLs on secret directory."
}

& icacls.exe $secretDir /grant:r "${currentUser}:(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to grant current Windows user FullControl on secret directory."
}

Write-Host ""
Write-Host "PASS: encrypted MEXC credentials stored under LOCALAPPDATA for the current Windows user."
Write-Host "Secret directory: $secretDir"
Write-Host "Do not copy these files to the repository or cloud storage."

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

$acl = Get-Acl $secretDir
$acl.SetAccessRuleProtection($true, $false)
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $currentUser,
    "FullControl",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl -Path $secretDir -AclObject $acl

Write-Host ""
Write-Host "PASS: encrypted MEXC credentials stored under LOCALAPPDATA for the current Windows user."
Write-Host "Secret directory: $secretDir"
Write-Host "Do not copy these files to the repository or cloud storage."

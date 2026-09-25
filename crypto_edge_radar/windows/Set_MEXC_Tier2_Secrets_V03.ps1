$ErrorActionPreference = "Stop"
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$bindingDir = Join-Path $HOME ".crypto_edge_radar"
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null
New-Item -ItemType Directory -Force -Path $bindingDir | Out-Null

$key = Read-Host "MEXC API Key" -AsSecureString
$secret = Read-Host "MEXC API Secret" -AsSecureString

$keyCipher = ConvertFrom-SecureString $key
$secretCipher = ConvertFrom-SecureString $secret
Set-Content -Path (Join-Path $secretDir "mexc_api_key.dpapi") -Value $keyCipher -NoNewline
Set-Content -Path (Join-Path $secretDir "mexc_api_secret.dpapi") -Value $secretCipher -NoNewline

$cred = New-Object System.Management.Automation.PSCredential("local",$key)
$keyPlain = $cred.GetNetworkCredential().Password
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($keyPlain)
    $hash = -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") })
} finally {
    $sha.Dispose()
    $keyPlain=$null
}
$binding = @{
    binding_version = "MEXC_LOCAL_ACCOUNT_BINDING_V0.3"
    api_key_sha256 = $hash
    created_at_utc = [DateTime]::UtcNow.ToString("o")
    note = "Non-secret hash binding only. API key/secret remain DPAPI protected."
}
$binding | ConvertTo-Json | Set-Content -Path (Join-Path $bindingDir "mexc_account_binding.json") -Encoding UTF8
Write-Host "PASS: DPAPI secrets + non-secret API-key binding installed."
Write-Host ("Binding: " + (Join-Path $bindingDir "mexc_account_binding.json"))

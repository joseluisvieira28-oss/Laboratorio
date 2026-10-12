param([Parameter(Mandatory=$true)][ValidateSet('status','once','run','arm','kill','selftest')][string]$Command)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$python=Get-Command py -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3 nao esta instalado (https://www.python.org/downloads/windows/).' }
$pyArgs=@('-3', (Join-Path $root 'app\engine.py'), $Command)
$credentialRoot=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadar\private'
function Reveal([string]$Path) {
  $cipher=(Get-Content -Raw -LiteralPath $Path).TrimEnd([char[]]@(13,10))
  $ss=ConvertTo-SecureString $cipher
  $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($ss)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
# GET+POST use exactly the DPAPI pair already configured for the existing Convex preflight.
$needsKeys=$Command -eq 'arm' -or $Command -eq 'run'
if($Command -eq 'once') {
  $authority=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarTrade\state\LIVE_AUTHORITY.json'
  if(Test-Path $authority){$needsKeys=$true}
}
try {
  if($needsKeys) {
    $a=Join-Path $credentialRoot 'api_key.dpapi';$b=Join-Path $credentialRoot 'api_secret.dpapi'
    if(-not(Test-Path $a) -or -not(Test-Path $b)){throw 'Chaves DPAPI antigas ausentes: executa 06_GUARDAR_CHAVES.cmd do pacote anterior.'}
    $env:MEXC_API_KEY=Reveal $a
    $env:MEXC_API_SECRET=Reveal $b
  }
  & py @pyArgs
  if($LASTEXITCODE -ne 0){throw ('Engine terminou com codigo '+$LASTEXITCODE)}
}
finally {
  Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
}
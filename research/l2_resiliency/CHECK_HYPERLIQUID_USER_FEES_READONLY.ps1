$ErrorActionPreference = 'Stop'
Write-Host "=== L2R HYPERLIQUID USER FEES READ-ONLY CHECK ==="
Write-Host "READ ONLY | NO ORDERS | NO WALLET MUTATION"
$wallet = Read-Host "Enter Hyperliquid trading address (0x...)"
if ($wallet -notmatch '^0x[0-9a-fA-F]{40}$') { throw "Invalid EVM address format." }
$body = @{ type = "userFees"; user = $wallet } | ConvertTo-Json -Compress
$r = Invoke-RestMethod -Method Post -Uri "https://api.hyperliquid.xyz/info" -ContentType "application/json" -Body $body
$maker = [double]$r.userAddRate
$taker = [double]$r.userCrossRate
$makerBps = $maker * 10000
$takerBps = $taker * 10000
Write-Host ""
Write-Host ("userAddRate  = {0} ({1:N4} bps/fill)" -f $r.userAddRate,$makerBps)
Write-Host ("userCrossRate= {0} ({1:N4} bps/fill)" -f $r.userCrossRate,$takerBps)
if ($maker -le 0.00004) {
  Write-Host "L2R_FEE_TRIGGER=PASS (effective maker <= 0.4 bps/fill)"
} else {
  Write-Host "L2R_FEE_TRIGGER=FAIL (effective maker > 0.4 bps/fill)"
}
Write-Host ""
Write-Host "Paste ONLY the three lines above if you want ChatGPT to adjudicate the gate."

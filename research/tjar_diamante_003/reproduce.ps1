param([switch]$DownloadEvidence)

$ErrorActionPreference = 'Stop'
$ledger = Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'hookr_release_ledger.csv')
$bySender = $ledger | Group-Object operator_prefix | Sort-Object Count -Descending
$times = $ledger | ForEach-Object { [DateTimeOffset]::Parse($_.timestamp_utc) }
$rolling = foreach ($end in $times) {
    @($times | Where-Object { $_ -gt $end.AddDays(-7) -and $_ -le $end }).Count
}

$grossWei = [decimal]4017730291234839
$gasWei = [decimal]($ledger | Where-Object nonce -EQ '2').gas_wei
$netETH = ($grossWei - $gasWei) / [decimal]1000000000000000000
if ($ledger.Count -ne 20 -or @($ledger.transaction_hash | Sort-Object -Unique).Count -ne 20) {
    throw 'Unexpected release count or duplicate transactions.'
}
[pscustomobject]@{
    Releases = $ledger.Count
    RecentCreditWithinOneSecond = @($ledger | Where-Object { [int]$_.latest_hookr_credit_to_release_s -le 1 }).Count
    Senders = $bySender.Count
    LargestSender = $bySender[0].Count
    MaxRollingSevenDays = ($rolling | Measure-Object -Maximum).Maximum
    NetETH = $netETH
    IndicativeNetUSD = [math]::Round($netETH * [decimal]2132.138072356442, 2)
}

if ($DownloadEvidence) {
    $base = 'https://robinhoodchain.blockscout.com/api/v2'
    $winner = ($ledger | Where-Object nonce -EQ '2').transaction_hash
    $evidence = [ordered]@{
        Details = Invoke-RestMethod -Uri "$base/transactions/$winner"
        Logs = Invoke-RestMethod -Uri "$base/transactions/$winner/logs"
        ERC20 = Invoke-RestMethod -Uri "$base/transactions/$winner/token-transfers"
        InternalFirstPage = Invoke-RestMethod -Uri "$base/transactions/$winner/internal-transactions"
        InternalSecondPage = Invoke-RestMethod -Uri "$base/transactions/$winner/internal-transactions?index=49&transaction_index=1&block_number=109917234&include_zero_value=true"
        LastCredit = Invoke-RestMethod -Uri "$base/transactions/0xfd6f854e0da60c90a7e085a86a65cd9dfb4fad6d132c6021ea8fc460e0f26507/token-transfers"
    }
    $evidence | ConvertTo-Json -Depth 40
}

# MEME-007 — 29 October 2026, 16:37 UTC, full 60m historical momentum audit

**NO-GO trading, full MEME006 original economic strategy still INCONCLUSIVE.** Read-only historical SolanaStreaming source archives user-provided in this conversation. No capital, payments, signatures or changes to prospective MEME006. Strict `[2026-10-29 15:37:00,16:37:00)` UTC. Frozen 36-event manifest SHA256 `bde40bdcf898bca8354a005594b8f3cf0cd5d81577ac90f5517034af1f948b2f`; historic price report SHA256 `477b3a69edc4e2dd8a08c1d40a5a9d0e7584a0a43143791224c692b1ba4121a4`.

## Source artifacts read and verified
- `20261029-150000.zip` SHA256 `d228f243305691f9fb915cfd5c350cc39e58551ddb787a14f7f94a5d9b996e51`; swaps JSONL 1,336,006, SHA256 `f66b0f9ee27d6853c012edb53376870cb9a706b48decdc325ac189659496d979`; newpairs JSONL 2,579.
- `20261029-160000.zip` SHA256 `addc72a558aeba67330451585b286ce88c0b767367bb8a27294a11523b0759f9`; swaps JSONL 1,231,669, SHA256 `1f02179cc50cdf5b32a4f64b865a8a61a9c2ce5a2a75f578e4b470ac35153c32`; newpairs JSONL 2,774.
- Total **2,567,675 source swap JSON records** read, **0 JSON errors**. Filter `swap.ammAccount`==frozen pool, `baseTokenMint`==frozen mint, quote==WSOL, `blockTime` strictly before signal; 820 exact-pool signatures, **0 duplicated/conflicted signatures** and 0 multiwallet signatures. Actual pool provenance matches PENGU **Orca**, USELESS **Raydium**. No raw wallet identities published.

## Frozen historical 60m flow counts and subsequent price proxies

| Target | 15:37–16:00 buy/sell | 16:00–16:37 buy/sell | 60m buy | sell | unique swaps | frozen buys>=sells & >=20 | 4h gross close | 4h less hypothetical 2.5pp | 24h gross close | 24h less 2.5pp |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| PENGU/Orca | 212/1 | 96/107 | **308** | 108 | 416 | **PASS** | -4.569% | **-7.069%** | -8.898% | **-11.398%** |
| USELESS/Raydium | 79/16 | 94/215 | 173 | **231** | 404 | **FAIL** | -6.974% | -9.474% | -17.188% | -19.688% |

PENGU 50 wallet addresses (35 buyer), largest wallet **107/308 buys=34.74%**; excluding all its activity still **201 buys vs 107 sells (PASS)**. Source USD buys **$96,941.34**, sells **$57,281.83**. USELESS 89 wallets (36 buyer); largest **66/173=38.15%**; without that wallet **107 buys/183 sells (FAIL)**; source USD buys **$47,136.01**, sells **$63,011.21**. Addresses are not proven independent individuals.

## Cumulative after four verified archive-date batches
- Earlier: 02 Oct 22:37 WIF PASS/USELESS FAIL, 24 Oct 00:37 BONK FAIL/WIF PASS/USELESS PASS, 25 Oct 00:37 BONK FAIL/USELESS PASS.
- New: 29 Oct 16:37 PENGU PASS / USELESS FAIL.
- **9/36 frozen price-only observations** with independently reconstructed 60m flow. **5 PASS/4 FAIL**, **27 remaining**.
- 5 flow-pass price-only proxy outcomes, cost **hypothetically** -2.5 percentage points, average **-0.873339% at 4h**, **-2.515969% at 24h**. Positive count 2/5 each horizon. No real fills or actual PnL; extreme survivor bias, tiny clustered selection.
- Required unique source-hour ZIPs for all 36 historical windows: **58**. Already operator-uploaded **8**, so **50 unique archives remain**, representing 27 signals at 25 timestamps. Do not request duplicates. At 15 Oct 20:37 UTC (MELANIA + USELESS), archives 20261015-190000 and 20261015-200000; at 05 Nov 20:37 (PENGU + USELESS), archives 20261105-190000 and 20261105-200000. Selected only by simultaneous signal density, NOT later results.

## Limits and safe next steps
This confirms only the **original 60m flow count subgate**, not full exact MEME006 eligibility. Historical instantaneous age/liquidity, 24h volume and tx count, DEX Screener/GeckoTerminal reconciliation, marketable 0.05 SOL routes, fees, MEV and fills unknown. Price h1/h6 rules in the retrospective are approximations from prior closed bars not the exact as-of rolling DEX h1/h6. No full trading edge proved. **Financial decision stays NO-GO**. Prefer staged bulk-archive processing/stop-rule versus 50 manual ZIP uploads; MEME006 prospective protocol unchanged.

Operator has full audited report `MEME007_20261029_1637_AUDIT_REPORT.md`, derived JSON `MEME007_20261029_1637_MOMENTUM_FULL_60M.json`, cumulative 9-event JSON, exact missing-hour manifest, and reproducible parser bundled in `MEME007_20261029_REPRODUCIBLE_AUDIT.zip` in this conversation. Source ZIPs not committed.

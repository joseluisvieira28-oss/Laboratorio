# MEME-007 — ACCESS / COST GATE 19 NOV 2026

## Explicit operator objective
Verify everything needed and execute the 36 authentic historical October/November token trade windows, **without authorizing any payment, card hold, extra credit billing, use of private credentials, or live trading**.

## Actual executed checks
1. Readback of prior Dune research bundle `MEME007_Dune_36_janelas_preparadas.zip`, frozen SQL SHA256 `3a5e7e3c9d3c9d522393032e7df7658dcfcabf0f5f0c71e87c91417f802c2bcd`, frozen window SHA256 `bde40bdcf898bca8354a005594b8f3cf0cd5d81577ac90f5517034af1f948b2f`.
2. Github [credential preflight run #44482704140](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44482704140) SUCCESS. **No registered standard Github Actions secrets** `DUNE_API_KEY`, `DUNE_API_KEY_PAID` or `SOLANASTREAMING_API_KEY` on this branch's PR job. Script checked boolean existence only; no values logged; `API_CALLS=0 ORDERS=0 CREDIT_SPEND=0`.
3. Connected plugin discovery for Dune returned no matching app. Corresponding email-provider search did not establish a connected account. No automatic assertion that operator never has a Dune account elsewhere.
4. Prior direct unauthenticated Dune results probe HTTP **401**, consistent with documented API requirements. Dune Free account is view-only; an API session needs trial/paid credits. Their official 2026 price page says trial 7 days and adding card may place temporary hold. Do not activate without explicit user action.
5. Source docs say SolanaStreaming hourly historical trade archives are **currently free**, but their `ss-cli download` requires user's account API key and an order ID from dashboard; sample files are ~100MB/hour (36 event-hours roughly 3.6GB compressed, before overlap and scope). An archive may not cover all target venue pools; validate venue support before counting missing data.
6. The 36 frozen price-only trigger windows actually involve **5 unique target coin mints/pools**, not all 6 preselected coins; `pudgy-penguins`, `bonk`, `dogwifcoin`, `useless-3`, `melania-meme`. `official-trump` had **no** October/Nov price trigger, so omitting it from the 36 event SQL is correct. Unique `block_date` partitions for those 36 1-hour windows = **23** versus 45 full calendar days. Exact local optimization package has two-tier direct-pool preflight / raw export and full mint fallback, retaining source hashes and no claims of SQL server validation.

## Verdict
**ACCESS_BLOCKED, not failed strategy.** The SQL is validated against original file hashes and is execution-ready *for an authorized account*, but the Dune live query was NOT executed and no historical October swaps have been newly recovered. Financial NO-GO, economic edge unproved. No money, trading, test orders, credentials, accounts or paywall bypass. Report separately from prospective MEME006.

## Next single dependency
Provide a legitimate connected Dune trial/paid account and an agreed zero-extra-spend credit budget, OR connect a free SolanaStreaming archive account/order via its official workflow. Never request a private key or ask the user to paste Dune API secrets in chat. With access, run inexpensive 36-window **count preflight** first; never mistake `project_main_id` not matching the screener pool for true zero swap flow. If cannot verify the quota/price, stop before SQL execution.

## Sources
- Dune pricing: https://dune.com/pricing
- Dune execute query: https://docs.dune.com/api-reference/executions/endpoint/execute-query
- Dune dex_solana.trades: https://dune.com/data/dex_solana.trades
- SolanaStreaming historical archives: https://solanastreaming.com/docs/archive
- SolanaStreaming CLI: https://solanastreaming.com/docs/libraries-and-sdks/cli
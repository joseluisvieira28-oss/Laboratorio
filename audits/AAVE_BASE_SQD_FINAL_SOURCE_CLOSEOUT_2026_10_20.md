# AAVE BASE DIRECT LIQUIDATION BONUS / SQD V0.1 — FINAL SOURCE CLOSEOUT
2026-10-20 UTC; terminal for this low-cost transport attempt.

## Tested official mechanistic source
Aave V3 Base Pool at `0xA238Dd80C259a72e81d7e4664a9801593F98d1c5`, official contract address book. The `LiquidationCall` event is real and represents debt repaid for discounted collateral including reserve-specific bonus, but does not establish a profit available to the user.

## Two real GitHub Actions outcomes
1. **Run 39385990791, artifact 12246944010:** 10/10 synthetic PASS, public SQD POST HTTP 200, first page yielded 21 NDJSON rows, 1 real Aave Pool LiquidationCall record at block 33,000,012 with matching source topic/address. On that run raw page only to block 33,000,366, while frozen logical 25,000-block boundary was 33,024,999. Original parser correctly refused to mark incomplete page as complete: `SOURCE_BLOCKED(NO_END_RANGE_SENTINEL)`. Archived immutable 1,857-byte source first page SHA in artifact; no 2026 outcomes or prices.
2. **Run 39386546174, artifact 12247876911:** Preregistered technical-only pagination amendment 5fa18789ab88c44676421773008739ad622ab250; exact original 100,000 block interval and ABI unchanged, introduced cursor pagination. 10/10 synthetic PASS; first SQD page request immediately returned HTTP **529**; no second complete canonical census; terminal `SOURCE_BLOCKED`. The initial freeze literally specified four HTTP requests; the amendment explicitly documented departure to paginated logical partitions before trying, not passed off as satisfying the original limit.

The censuses do NOT support total number of liquidations across the full window, liquidator market shares, accessibility, actual bonus USD, gas, failed transactions, private competition, flashloan costs, DEX liquidity or PnL. No trading, wallet or account actions. The source has been proven PARTIALLY ACCESSIBLE, **not a reliable complete free dataset under this tested workflow**. Green workflow tests are technical only.

## Scientific and resource verdict
**AAVE_BASE_SQD_001 = SOURCE_BLOCKED / ZERO EXECUTABLE NET EDGE DEMONSTRATED / STOP CODING.** This is NOT NO_EDGE and not proof that liquidation bonuses cannot be profitable. But the first cheapest falsifier failed; do not spend on a liquidation execution bot, private MEV relays, paid archive or RPC remediation to rescue it. Do not change scientific source window/filters after seeing one real event.

All branch workflow automatic trigger paths have been removed in commit 27d03c291eaf2b823981a4a938b9e5abba276c9d; manual workflow is disabled (job if:false) to prevent noisy retries. No merge to main.

## Next capital/effort allocation
No new strategy coding here. Reuse the separate **BTC-OPTIONS-VRP-001** lab, PR #163, as the only currently better-supported *economic phenomenon* for feasibility adjudication, not as GO. It has 192 weekly 2021–24 observations, VRP positive in ~74.5%, mean IV-RV gap ~10.43 vol points but historic execution not proven. Existing public Deribit 0.01 BTC_USDC options minimum source supports a hypothetical ~301 USDC short-call+short-put initial margin estimate **before hedging margin**; public dated tape route could not prove exact paired executable entries/exits. Existing forward source bank is UNDERPOWERED and cannot be rescued by lowering gates. Meaningful next scientific output: determine whether public prospective two-sided BBO/depth and collateral/risk capacity ever make even ONE locked trade family executable without assumptions of perfect passive fills; only afterwards consider independent net forward economic protocol. Source: https://github.com/joseluisvieira28-oss/Laboratorio/blob/btc-options-vrp-v2-forward-2026-10-07/research/btc_options_vrp_v2/V2_RESEARCH_CLOSEOUT_2026-10-07.md

No claim of option-selling safety: unlimited/tail losses for unhedged short options, liquidity shocks, volatility regime change, gap and hedge costs; the user should not deploy funds based on historical IV-RV alone.

Final: zero crypto trading machines proven. This investigation delivered a verifiable partial real protocol event, a repeatable source failure proof, and clear STOP allocation decision.

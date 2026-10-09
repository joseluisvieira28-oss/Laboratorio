# ASYMMETRIC PAYOFF LAB — MEXC FUTURES PUBLIC QUOTE SOURCE CLOSEOUT
Date: 2026-10-09
Mode: Source-only, NO account/orders/trading; independent of BTC-CONVEX Binance strategy.
Workflow https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37886587975
Frozen source spec commit 801f6ef2f29fd865a0ab6d21f1439f1451e75677, source runner commit 66cf3b82ebb3305ca0fd37730813ac0a82baf5b1, artifact 11597025458.

## Evidence chain
- All 5 synthetic cases PASS, compilation PASS.
- Public `GET contract.mexc.com/api/v1/contract/ping`, contract detail (1 per 5 sec rate limited) and contract/depth snapshots completed for all four fixed symbol contracts. All four source snapshots passed the freshness/depth validation in this single probe.
- Contract sizes and units correctly distinguished: book quantities represent contracts; market notional = contracts * contractSize * price. NO account balance/authenticated API.
- Frozen source gate required all of $10/$25/$50/$100 hypothetical order sizes pass for all 4. Two $10 cells failed min volume quantization => global **SOURCE_BLOCKED_NO_TRADING**; original gate NOT relaxed after seeing it.

| Symbol | Public snapshot spread bps | $10 sample | $25/$50/$100 samples | Public detail takerFeeRate (per side) | apiAllowed |
|---|---:|---|---|---:|---|
| BTC_USDT | 0.01217 | source size/depth sample pass | pass/pass/pass | 0.0002 (2 bps) | true |
| ETH_USDT | 0.04024 | LOT_SIZE_BLOCKED | pass/pass/pass | 0.0002 (2 bps) | true |
| SOL_USDT | 0.91029 | LOT_SIZE_BLOCKED | pass/pass/pass | 0.0004 (4 bps) | true |
| BNB_USDT | 1.34834 | source size/depth sample pass | pass/pass/pass | 0.0002 (2 bps) | true |

The fees are **exchange public metadata**, NOT verified operator-specific realized fees. Spreads/depth are a **single short-lived snapshot**, not future fills, order acceptance, market impact or recurring alpha; funding, exit liquidity, gap losses, actual fill slippage and min capital/margin risk are NOT validated. Source gate code uses top-20 levels; any future marketability analysis must also enforce contract-specific `marketOrderMaxLevel` and limit-price constraints before claiming executable depth.

## Economic and scientific verdict
- Under the preregistered **all four sizes** criterion: SOURCE_BLOCKED_NO_TRADING, because ETH and SOL $10 cells fail.
- Descriptively: at hypothetical **$25, $50 and $100 notionals**, minimum lot and sampled 20-level depth were sufficient in all four frozen symbols.
- This is useful *source feasibility* for an entirely new MEXC-specific experiment, NOT an independent trading edge, not a legitimate transfer of Binance Parent V5 performance.
- No executable NET edge established, no valid live authority, no capital spent. Do not retune strategy based on this sample.
- If a fresh research family is desired, freeze an MEXC-specific signal/execution/funding/cost estimand FIRST and collect contemporaneous quotes and 1h signals append-only. Missing evidence => fail closed. No old outcome receives prospective credit.

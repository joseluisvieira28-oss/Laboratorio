# STABLECOIN-DEX-STRESS-001 — SQD SOURCE REMEDIATION V0.2 CLOSEOUT

Date: 2026-09-18
Lab: STABLECOIN-DEX-STRESS-001
MVE: SDS-CURVE3POOL-PEG-001
Source gate: SDS-CURVE3POOL-PEG-001-SOURCE-002-SQD
Branch: stablecoin-dex-stress-source-v0.2-sqd
Canonical run: 35334465172
Trigger head: 3456d127b2e64b376d85ba6fd8a716cb6c204559

## FINAL SCIENTIFIC CLASSIFICATION

PROVENANCE_FAILURE — FROZEN SOURCE FORMULA INCOMPATIBLE WITH CANONICAL EVENT CORPUS

This is NOT NO_EDGE and no ETH market outcome was opened.

## WHAT PASSED

- SQD Ethereum-mainnet transport is reachable and returns canonical Curve 3pool TokenExchange history.
- Exact frozen 3pool address and TokenExchange topic are producing historical events.
- Event data decodes under the frozen 4-word ABI layout.
- 2025/2026 firewalls remained closed.
- ETH prices, returns, PnL, threshold signals and performance statistics remained unopened.

## HARD FAILURE

The frozen source contract requires every retained TokenExchange event to have strictly positive tokens_sold and tokens_bought before applying the frozen normalization/log-deviation formula.

Canonical SQD history contains TokenExchange events with a zero token quantity. This is not an isolated transport glitch:

- shard 0, blocks 11,565,000..12,187,555: failure non-positive token quantity after 3,642 decoded events and seven 2021 UTC source days.
- shard 4, blocks 14,055,224..14,677,779: the same non-positive token quantity failure after 3,481 decoded events in 2022.

Because ln(bought_norm/sold_norm) is undefined when either normalized amount is zero, the exact frozen V0.1 source formula is not defined on the full canonical event corpus.

## NO RESCUE

Do not silently drop zero-quantity events, replace zero with epsilon, winsorize/clip, switch pool/stablecoin subset, change the stress formula, lower source gates, or open ETH outcomes under SDS-CURVE3POOL-PEG-001.

Any future stablecoin-DEX stress study must use a NEW prospective mechanism/source formula ID frozen before market outcomes. The original SDS-CURVE3POOL-PEG-001 remains economically untested but closed for this exact source definition.

2025 accessed: false
2026 accessed: false
ETH/BTC market values opened: false
returns/PnL/performance: false
live trading / exchange mutation / main merge: false

# MSEL-001 — SEMANTIC AUDIT14 V0.1

Status: PRE-OUTCOME TECHNICAL AUDIT  
Outcomes: LOCKED  
Purpose: classify the 14 suspicious transactions extracted from the T+5 forensic reconstruction and identify any feature-semantic defects before feature freeze.

## Executive verdict

The 14 suspicious transactions do not reveal missing economic transfers. They reveal three distinct technical/market-structure phenomena:

1. 11 Pump BUY instructions are deterministic no-delivery dust/probe transactions: each requests exactly 1 raw token unit with max_sol_cost=5 lamports, aliases associated_user to associated_bonding_curve, produces no target-mint token balance change, and moves only 1 lamport each to fee recipient / bonding curve / creator vault while the signer pays the transaction fee. All 11 share the same signer wallet and occur ~33–43s after launch across 11/25 pilot mints.
2. 1 alleged non-Pump balance change is actually the original Pump CREATE/MintTo of 1,000,000,000 tokens. It is launch-state initialization, not a transfer.
3. The remaining 2 alleged non-Pump balance changes are explicit SPL Token burn + close-account dust-cleanup transactions (0.457730 and 0.129545 token respectively), not transfers.

Therefore `direct_non_pump_token_change_tx_count` MUST NOT be interpreted as transfer count.

## Critical decoder defect

Historical Pump IDL authority for June 2025 defines BUY and SELL accounts as:

0 global
1 fee_recipient
2 mint
3 bonding_curve
4 associated_bonding_curve
5 associated_user
6 user (signer)
...

Current collector decodes:

- bonding_curve = accounts[3]  [correct]
- associated_user = accounts[4] [incorrect: this is associated_bonding_curve]
- user = accounts[5] [incorrect: this is associated_user token account]

The real signer wallet is accounts[6]. This affects BUY and SELL.

Consequences:

- `unique_buyers` invalid
- `unique_sellers` invalid
- `unique_external_buyers_ex_creator` invalid
- `associated_user` field mislabeled
- creator-vs-buyer exclusions invalid
- any wallet-level organic-demand feature derived from current trade_events is blocked pending rerun/correction

Holder concentration features reconstructed from token balance owner fields remain structurally usable because they do not depend on the mislabeled Pump trade `user` field.

## Atomic round-trip contamination

Across the full T+5 `trade_events.jsonl`:

- 1081 Pump trade instructions
- 929 unique (tx,mint) trade transactions
- 151 transactions contain exactly one BUY + one SELL for the same mint
- all 151 have identical buy/sell token amount
- all 151 leave only +1 lamport net change on the bonding curve
- those 302 instructions are 27.94% of all Pump trade instructions
- adding the 11 no-delivery dust buys yields 313 / 1081 = 28.95% clearly non-organic/no-delivery/atomic-roundtrip instructions

Atomic round-trips occur in only 4/25 pilot mints but are highly concentrated:

- AGhc...: 66 round-trips
- By7S...: 59
- BgM7...: 20
- CYfK...: 6

Example raw T+5 instruction counts are therefore badly inflated for some launches. AGhc has 89 BUY and 84 SELL instructions raw; subtracting 66 atomic round-trips and one no-delivery dust buy leaves only 22 non-roundtrip BUY instructions and 18 non-roundtrip SELL instructions before any further semantic filtering.

## Gross turnover semantic defect

`curve_lamport_gross_turnover_raw` is currently calculated as the sum of absolute transaction-level net bonding-curve lamport deltas (deduplicated per transaction).

This is NOT gross trade turnover whenever a transaction contains multiple Pump instructions. A same-transaction BUY+SELL can move substantial SOL in both directions while ending with ~0 net curve balance change. The 151 atomic round-trips all record +1 lamport net curve delta, so the current feature materially understates churn and is semantically misnamed.

Required correction:

- rename current raw balance-derived measure to something like `abs_tx_net_curve_lamport_change_sum_raw`; and
- reconstruct actual per-instruction SOL amounts from the historical Pump `TradeEvent` emitted data (preferred) or another independently validated per-instruction source before defining true gross turnover / Organicity denominator.

## Feature validity after this audit

PASS / usable as raw point-in-time structural features:

- raw_owner_count_including_curve
- raw_external_holder_count
- bonding_curve_token_balance_raw
- external_token_balance_raw
- creator_external_balance_raw
- creator_share_external
- raw_external_top1/top3/top5/top10_share
- token balance state itself (subject to normal entity-clustering limitations)

BLOCKED / must be corrected before feature freeze:

- unique_buyers
- unique_sellers
- unique_external_buyers_ex_creator
- wallet-level buyer/seller identity
- direct_non_pump_token_change_tx_count as transfer proxy
- curve_lamport_gross_turnover_raw as gross turnover
- final Organicity Ratio

RAW-ONLY / not economic without semantic filtering:

- buy_instruction_count
- sell_instruction_count
- buy_token_amount_raw_sum
- sell_token_amount_raw_sum
- transaction-level net curve lamport delta

## Scientific classification

- Cohort selection integrity: PASS
- Raw RPC traceability: PASS
- Token-balance reconstruction: PASS with semantic event classification correction
- Pump trade wallet attribution: FAIL — technical decoder bug
- Gross turnover semantics: FAIL — transaction net is not gross per-instruction turnover
- Outcomes: remain LOCKED
- Edge: UNKNOWN

No result in this audit may be used to infer future performance. This is a pre-outcome data/semantics correction only.

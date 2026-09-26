# AMM-LVR-CROSSVENUE-001 — INCLUSION COST SOURCE FREEZE V0.1

**Frozen:** 2026-09-23 before inclusion-cost attribution output  
**Scope:** source/cost attribution only; no edge adjudication

## Objective

Bind two objectively observable on-chain transaction cost components for prospectively observed registry hits:

1. priority fee paid through EIP-1559 gas;
2. direct ETH value transferred inside the transaction trace to the block fee-recipient address.

This reduces the ACCESSIBILITY_UNPROVEN cost gap without pretending that every competitive builder/searcher payment is publicly observable.

## Frozen formulas

For each transaction with a valid receipt and block:

- base_fee_per_gas = block.baseFeePerGas
- effective_gas_price = receipt.effectiveGasPrice
- priority_fee_per_gas = max(effective_gas_price - base_fee_per_gas, 0)
- priority_fee_paid_wei = priority_fee_per_gas × gasUsed
- direct_fee_recipient_transfer_wei = sum(call.value) for trace calls whose to equals block.miner / fee recipient
- observed_inclusion_payment_wei = priority_fee_paid_wei + direct_fee_recipient_transfer_wei

Base fee burn is a transaction execution cost but is not classified as an inclusion payment.

## Important limitation

direct_fee_recipient_transfer_wei is an observable fee-recipient transfer, not a claim that every such transfer is a builder payment, and zero does NOT prove zero off-chain / bundle / builder economics.

Competitive failure probability and unobserved private-orderflow economics remain UNBOUND until separately proven.

## Evidence population

Input is the already-frozen forward_hit_registry_v0_2.json. Registry touches are not assumed to be CEX-DEX arbitrage.

No price, quote, PnL, return, or opportunity outcome is opened by this probe.

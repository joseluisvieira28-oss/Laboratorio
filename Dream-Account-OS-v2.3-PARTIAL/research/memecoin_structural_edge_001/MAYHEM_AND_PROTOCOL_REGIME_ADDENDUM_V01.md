# MSEL-001 — MAYHEM / PROTOCOL REGIME ADDENDUM V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Why this addendum exists

Pump.fun launch mechanics are not stationary. The research universe now contains multiple protocol regimes whose early-flow statistics are not comparable without explicit controls.

The primary Killer Filter thesis concerns whether *human/economic early-flow structure* predicts future downside risk. Any protocol feature that injects artificial or mechanically different flow must therefore be isolated before feature generation.

## 2. Mayhem Mode is a separate population

Official Pump documentation states that Mayhem Mode can be enabled at creation and cannot be toggled later. A Pump-funded autonomous trading agent may trade the coin during its first 24 hours, buying and selling probabilistically and subject to risk caps. The mode also changes token-supply mechanics and routes protocol fees through dedicated reserved fee recipients.

### Scientific consequence

For a Mayhem coin, the following candidate MSEL features are contaminated by protocol-generated activity:

- raw volume;
- buyer/seller counts;
- buyer-arrival rate;
- transaction count;
- price variance;
- gross turnover;
- flow imbalance;
- wallet concentration if the known agent wallet is not excluded;
- supply-normalized concentration if the different Mayhem supply regime is ignored.

### Hard rule

**Primary MSEL-001 Killer Filter excludes Mayhem Mode coins.**

A later secondary analysis may study Mayhem separately only if:
1. the mode is identified point-in-time from the creation instruction/account state;
2. known protocol-agent wallets and Mayhem-specific flow can be removed or explicitly modeled;
3. supply normalization is regime-correct;
4. the analysis is never pooled with ordinary coins without a pre-registered interaction design.

Mayhem activity must never be interpreted as independent organic buyer diffusion.

## 3. Fee-recipient / buyback-recipient regime

Current official Pump docs define separate fee-recipient sets for ordinary vs Mayhem coins and separate buyback fee recipients. These protocol-controlled addresses are not market participants.

### Hard rule

Protocol fee recipients, buyback fee recipients, bonding-curve PDAs, PumpSwap pool accounts and other protocol-owned accounts are excluded from holder/buyer concentration and wallet-independence metrics.

## 4. `user` is not necessarily `creator`

The launch transaction signer/payer can differ from the economic creator. Free-creation / create-and-buy flows can cause the first buyer to be the `user` while the declared `creator` is another pubkey.

### Hard rule

MSEL tracks separately:
- transaction payer / `user`;
- declared `creator`;
- mint signer/keypair role where observable;
- first buyer;
- fee recipient / sharing beneficiary when applicable.

No creator-history feature may substitute `user` for `creator` without proof of identity equivalence.

## 5. Create-and-buy contamination

Official SDK flows can place creation and an initial buy in the same transaction.

### Hard rule

The launch-associated seed buy is recorded separately from external market demand. Primary buyer-diffusion features report both:

- `buyers_all`;
- `buyers_external_ex_creator_cluster`.

The external version is the thesis feature. A token is not credited with organic buyer diffusion simply because the creator/payer seeded its own curve.

## 6. Quote-asset and token-program regimes

`create_v2` supports SOL-paired and non-native quote assets such as USDC, and current creation uses Token-2022 fields. Quote asset changes the economic meaning of notional, fee accounting and reserve state.

### Hard rule

Primary MSEL-001 pilot uses one homogeneous quote-asset regime. SOL and USDC/custom-pair launches are not pooled until independent replication shows compatible behavior after normalization.

## 7. Holder-reward / creator-fee variants

Current Pump mechanics include holder-reward coins, where the creator-fee stream is routed to holders rather than a creator wallet. Other historical creator-fee / sharing configurations also exist.

### Hard rule

`is_holder_reward`, creator-fee configuration and sharing configuration are mandatory regime fields in the launch schema. They are not silently ignored.

## 8. Schema Regime Map — required fields

Every launch entering the pilot must carry:

- `protocol_version_bucket`
- `create_instruction_variant`
- `quote_asset`
- `token_program`
- `is_mayhem_mode`
- `is_holder_reward`
- `creator_fee_regime`
- `fee_schedule_bucket`
- `creator`
- `user_payer`
- `create_and_buy_same_tx`

A row with unresolved critical regime fields is quarantined.

## 9. Main new risk to false edge

A model can appear predictive simply by learning protocol-regime differences. Example:

`Mayhem mode -> more early volume/variance -> different survival distribution`

That is not evidence that organic early buyer flow has predictive content.

Therefore all MSEL performance must be reported both:
1. inside a homogeneous protocol regime;
2. across later regimes only as external replication.

## 10. Immediate action

Before the 25-launch pilot is allowed to open outcomes, the reconstruction code must prove that it can identify and exclude Mayhem launches and correctly distinguish creator, payer and launch-associated seed buys.

No live trading. No main merge. No post-outcome tuning.

# AAVE-LIQUIDATION-OVERHANG-001 — R1 SCALED-LEDGER AUDIT SHARDING REMEDIATION V0.2

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE FIRST SHARDED R1 AUDIT RESULT / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

Two executions of the frozen monolithic audit were terminated only by explicit GitHub Actions wall-clock ceilings:

- run `35226616121`: cancelled at the 45-minute workflow ceiling;
- run `35355395431`: cancelled at the 120-minute workflow ceiling.

Neither run produced the canonical audit receipt. Therefore neither produced a reconstruction, provenance, or scientific verdict.

## Immutable scientific contract

This remediation MUST NOT change:

- borrower universe: all unique `Borrow.onBehalfOf` identities in blocks 16,490,000..21,525,890;
- deterministic borrower ranking: `keccak256(raw 20-byte borrower address)`, ascending by `(digest,address)`;
- sample size: exactly 16;
- reserve universe: exact canonical 37-reserve R0 bootstrap;
- audit blocks: 17,748,972; 19,007,945; 20,266,917; 21,525,890;
- token-native Mint/Burn/BalanceTransfer semantics;
- Aave round-half-up ray arithmetic;
- variable-debt non-transferability rule;
- validation target construction;
- frozen independent archive RPC set;
- minimum two-RPC quorum, exact agreement, and exact replay equality;
- all terminal classifications and fail-closed precedence;
- 2023-2024 protected block envelope;
- all no-outcome firewalls.

## Operational remediation only

V0.2 replaces the repeated monolithic transport with deterministic source reuse + fixed block shards:

1. **Sample derivation** reuses the already-canonical eight Source Census shard receipts from run `35214027573`.
   - Those receipts were created before R1 and contain the exact `Borrow` participant identities by fixed disjoint block shard.
   - V0.2 must verify all eight canonical ranges, `SHARD_PASS`, total Borrow event count = **204,952**, and unique Borrow participant count = **30,691** before deriving the sample.
   - The sample ranking rule remains exactly the frozen R1 rule.

2. **Token-event acquisition** is split over the same eight fixed disjoint block ranges used by the canonical Source Census:
   - 16,490,000..17,119,486
   - 17,119,487..17,748,973
   - 17,748,974..18,378,460
   - 18,378,461..19,007,946
   - 19,007,947..19,637,432
   - 19,637,433..20,266,918
   - 20,266,919..20,896,404
   - 20,896,405..21,525,890

3. Each shard imports the frozen `r1_scaled_ledger_audit_v01.py` implementation and calls its existing:
   - `build_token_maps`;
   - `acquire_sample_token_deltas`;
   - exact decoding/ray helpers.
   Only the module's block bounds are set to that shard's frozen disjoint range.

4. The canonical aggregator reconstructs the exact union of block deltas, then calls the original frozen:
   - `replay_targets`;
   - `validate_targets`.
   RPC validation therefore remains the original V0.1 implementation.

## Integrity requirements

PASS to canonical adjudication requires:

- exactly one deterministic sample receipt;
- exactly eight shard receipts with the exact fixed ranges and no gaps/overlaps;
- identical sample SHA256 in every shard;
- exact canonical R0 envelope and 37 reserves;
- no duplicate shard IDs;
- all shard transport/decode classifications PASS;
- no dropped user/token pair, block delta, failed target, reserve, endpoint, or event class.

Any variable-debt BalanceTransfer, negative replay state, RPC disagreement, replay mismatch, insufficient RPC quorum, incomplete shard, source error or malformed receipt must be preserved and adjudicated exactly under the parent R1 V0.2 rules.

## Safety

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcomes;
- market-return prices;
- returns, PnL, PF, win rate or drawdown;
- 2025/2026 access;
- live trading, orders, wallets, authenticated exchange mutation, alerts/webhooks;
- merge to main.

This remediation is infrastructure only. It cannot create an edge verdict.

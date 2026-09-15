# MSEL-001 — Pilot25 PumpSwap Historical Event Lock V0.1

Status: PRE-EVALUATION / RESEARCH-ONLY / FROZEN
Date: 2026-09-15
Branch: `memecoin-structural-edge-v0.1`

## Purpose

Freeze the historical PumpSwap decoding authority used by Pilot25 before any return, label, slice statistic or verdict is computed from the already-sealed V13 future source bytes.

This is a technical/schema lock only. It does not change V11 risk ranks, V12 outcome definitions, thresholds, horizons, notional floors or costs.

## Historical authority

Official repository: `pump-fun/pump-public-docs`

Historical commit already frozen for the June-2025 pilot:

`e2b66e4fce2fc130955912315167dc41e56956ad`

Historical PumpSwap IDL:

`idl/pump_amm.json`

Git blob SHA:

`7a1cf37270f6015f5af53b9ce58d8a6890254020`

Program ID:

`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

Canonical SOL quote mint required by the Pilot25 outcome schema:

`So11111111111111111111111111111111111111112`

## Historical PumpSwap instruction authority

Sell instruction discriminator:

`[51, 230, 133, 164, 1, 127, 131, 173]`

Historical sell account prefix:

0. pool
1. user
2. global_config
3. base_mint
4. quote_mint
5. user_base_token_account
6. user_quote_token_account
7. pool_base_token_account
8. pool_quote_token_account
9. protocol_fee_recipient
10. protocol_fee_recipient_token_account
11. base_token_program
12. quote_token_program
13. system_program
14. associated_token_program
15. event_authority
16. program

Historical sell arguments:

- `base_amount_in: u64`
- `min_quote_amount_out: u64`

Buy instruction uses the historical Anchor buy discriminator `[102, 6, 61, 18, 1, 218, 235, 234]`, with the same account prefix through base/quote mint and pool identity. Its arguments are `base_amount_out: u64`, `max_quote_amount_in: u64`.

## Historical events

### BuyEvent

Discriminator:

`[103, 244, 82, 31, 44, 245, 119, 119]`

Encoded length including discriminator: `360` bytes.

Fields in exact Borsh order:

1. timestamp i64
2. base_amount_out u64
3. max_quote_amount_in u64
4. user_base_token_reserves u64
5. user_quote_token_reserves u64
6. pool_base_token_reserves u64
7. pool_quote_token_reserves u64
8. quote_amount_in u64
9. lp_fee_basis_points u64
10. lp_fee u64
11. protocol_fee_basis_points u64
12. protocol_fee u64
13. quote_amount_in_with_lp_fee u64
14. user_quote_amount_in u64
15. pool pubkey
16. user pubkey
17. user_base_token_account pubkey
18. user_quote_token_account pubkey
19. protocol_fee_recipient pubkey
20. protocol_fee_recipient_token_account pubkey
21. coin_creator pubkey
22. coin_creator_fee_basis_points u64
23. coin_creator_fee u64

For Pilot25 executable entry reference, the realized quote side is `user_quote_amount_in`; base token quantity is `base_amount_out`.

### SellEvent

Discriminator:

`[62, 47, 55, 10, 165, 3, 220, 42]`

Encoded length including discriminator: `360` bytes.

Fields in exact Borsh order:

1. timestamp i64
2. base_amount_in u64
3. min_quote_amount_out u64
4. user_base_token_reserves u64
5. user_quote_token_reserves u64
6. pool_base_token_reserves u64
7. pool_quote_token_reserves u64
8. quote_amount_out u64
9. lp_fee_basis_points u64
10. lp_fee u64
11. protocol_fee_basis_points u64
12. protocol_fee u64
13. quote_amount_out_without_lp_fee u64
14. user_quote_amount_out u64
15. pool pubkey
16. user pubkey
17. user_base_token_account pubkey
18. user_quote_token_account pubkey
19. protocol_fee_recipient pubkey
20. protocol_fee_recipient_token_account pubkey
21. coin_creator pubkey
22. coin_creator_fee_basis_points u64
23. coin_creator_fee u64

For Pilot25 executable future exit evidence, the realized quote side is `user_quote_amount_out`; base token quantity is `base_amount_in`.

### CreatePoolEvent

Discriminator:

`[177, 49, 12, 210, 160, 118, 167, 116]`

Encoded length including discriminator: `333` bytes.

Relevant fields include `base_mint`, `quote_mint`, `pool`, and the contemporaneous pool creation amounts.

## Canonical migration-link rule

A PumpSwap pool may be used for Pilot25 continuity only when all of the following are proven from the captured on-chain transaction itself:

1. the transaction invokes the historical Pump program with the Anchor `migrate` discriminator `[155, 234, 231, 146, 236, 158, 162, 30]`;
2. the same successful transaction emits a historical PumpSwap `CreatePoolEvent`;
3. `CreatePoolEvent.base_mint` equals the target Pilot25 mint;
4. `CreatePoolEvent.quote_mint` equals wrapped SOL `So11111111111111111111111111111111111111112`;
5. all historical event bytes decode exactly under the frozen May-2025 PumpSwap IDL.

No arbitrary PumpSwap pool, later-discovered pool, name/symbol match, DEX aggregator route or heuristic address match is accepted.

If a PumpSwap trade for a target mint cannot be linked to a pool satisfying this rule, it is `SOURCE_BLOCKED_MIGRATION_LINK`; it is not silently treated as a valid outcome.

## Governance

- V11 feature matrix and risk order remain frozen.
- V12 entry/outcome definitions remain frozen.
- V13 future source bytes remain immutable and sealed.
- No parameter tuning after outcomes.
- No live trading, exchange mutation or main merge.
- Pilot25 cannot by itself claim `SURVIVES_MVE`.

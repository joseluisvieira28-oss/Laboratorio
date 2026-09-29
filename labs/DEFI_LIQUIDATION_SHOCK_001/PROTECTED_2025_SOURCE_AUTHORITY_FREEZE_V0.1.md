# DEFI-LIQUIDATION-SHOCK-001 — PROTECTED 2025 SOURCE AUTHORITY FREEZE V0.1

Date: 2026-09-29
Status: FROZEN / SOURCE-ONLY / BEFORE 2025 MARKET OUTCOMES

## Objective
Construct the complete 2025 source-event population for the already-frozen SOL-collateral strategy without opening any 2025 price, return, PnL, funding or directional market outcome.

Window:
2025-01-01T00:00:00Z <= event timestamp < 2026-01-01T00:00:00Z

2026 event/outcome data is excluded.

## Protocols/classes
Exactly:
- marginfi / lending_account_liquidate
- save0c / LiquidateObligation
- kamino / liquidate_obligation_and_redeem_reserve_collateral
- save11 / LiquidateObligationAndRedeemReserveCollateral

No Drift is introduced because the canonical SOL population that survived Discovery/OOS contains no Drift SOL target cluster.

## Decoder inheritance
Use the same pinned protocol IDs, discriminators, success conditions and semantic account roles already validated through 2024.

2025 source mapping:
- Marginfi collateral asset: asset_bank account position 1; mint/decimals resolved from finalized Marginfi bank account dataSlice offset 8 length 33. Owner must equal Marginfi program.
- Save0c collateral underlying: withdraw_reserve position 4; finalized reserve dataSlice offset 42 length 33 yields underlying mint/decimals and offset 227 length 32 yields collateral mint. Owner must equal Solend program.
- Kamino: require V1.6+ fixed prefix >=20 accounts; withdraw_reserve_liquidity_mint position 8 is collateral-underlying mint; fixed token/sysvar layout checks remain enforced.
- Save11: exactly 15 accounts; data length 9 or 10 only; collateral-underlying unit comes from reserve liquidity supply position 8 token-balance metadata, optional user destination liquidity position 2 may only confirm the same unit.

No amount, oracle, price, balance quantity or economic-value field is decoded.

## Completeness
Each protocol collector scans the full 2025 slot/time interval to documented stream termination.
Every successful matching instruction must have:
- canonical signature + instructionAddress identity;
- valid frozen account/ABI shape;
- resolved collateral-underlying mint;
- no duplicate canonical identity;
- no source conflict.

## 60-second clustering
After all collectors PASS:
- group by protocol/class/collateral mint;
- sort by timestamp;
- same frozen quiet rule: events <=60 seconds apart remain in one cascade;
- T0 = last event +60 seconds;
- any cluster whose T0 >= 2026-01-01T00:00:00Z is excluded from 2025 to preserve 2026.

Target:
mint:So11111111111111111111111111111111111111112

## Terminal classification
PASS only when all four collectors PASS and aggregate has zero conflicts/errors:
PROTECTED_2025_SOURCE_AUTHORITY_PASS

Otherwise:
PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED

This PASS authorizes only the already-frozen 2025 economic holdout. It does not authorize 2026 or live trading.

## Firewall
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
funding_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false

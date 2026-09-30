# MARGINFI SOL ROUTE MIGRATION V0.1 — SOURCE PASS + ORCA IDENTITY CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-route-migration-v01

Canonical route-migration run:
36769933849

Canonical terminal artifact:
dls-marginfi-sol-route-migration-source-v01
artifact ID 11123630129
digest sha256:eb0f960993e25661d023ad3c3acd22e150c471466e2ffe65adeb228238d9325b

Classification:
MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_PASS

Deterministic samples:
- July 2024: 128 / 128 exact transactions complete
- August 2024: 128 / 128 exact transactions complete
- September 2024: 128 / 128 exact transactions complete
- identity conflicts: 0
- unresolved transport failures: 0

Single frozen migration candidate:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc

Transaction-presence share after canonical Marginfi SOL liquidation:
- July: 46 / 128 = 0.359375
- August: 116 / 128 = 0.90625
- September: 119 / 128 = 0.9296875

For comparison, Jupiter V6:
- July: 76 / 128 = 0.59375
- August: 7 / 128 = 0.0546875
- September: materially lower than July in the same frozen census.

## Program identity authority

Official upstream repository:
orca-so/whirlpools

Pinned upstream commit:
f4b99e79e7140f3917e4ce81a2e8ad06ccdf8ce4

Official README states the Whirlpools contract is deployed at:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc
on Solana mainnet and devnet.

Official program source:
programs/whirlpool/src/lib.rs
contains:
declare_id!("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc");

Identity:
ORCA WHIRLPOOLS program.

This identity is authoritative program identity only.
It does NOT yet prove:
- that every occurrence is a swap;
- the token direction of a specific post-liquidation instruction;
- realized SOL sell amount;
- market edge.

## Structural conclusion

The source evidence supports a real post-liquidation program-composition regime change:

July:
Jupiter is common and Orca Whirlpools is present in a minority of sampled transactions.

August/September:
Orca Whirlpools is present in >90% of sampled post-liquidation transactions while Jupiter presence
collapses sharply.

This motivates a separate source-semantic Orca swap calibration.

No market outcome was used.

Firewall:
prices=false
returns=false
pnl=false
market_2024_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false

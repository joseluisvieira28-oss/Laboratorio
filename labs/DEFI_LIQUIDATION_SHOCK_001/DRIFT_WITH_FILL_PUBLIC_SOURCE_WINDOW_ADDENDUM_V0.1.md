# DLS — DRIFT WITH-FILL PUBLIC-SOURCE WINDOW ADDENDUM V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE BOUNDED WITH-FILL CENSUS

## Source authority

Canonical historical protocol repository:
- GitHub repository ID 497045217
- current path velocity-exchange/protocol-v2

Public source commit:
- a259778564afcf563b21399359eb2781753db20a
- committed: 2024-07-30T17:21:13Z
- message: "program: add liquidation via fill (#1106)"

The commit explicitly introduces `liquidate_perp_with_fill`.

## Source-audited population window

For the parent SIGNED_FLOW_SOURCE_AUTHORITY mission, define a conservative public-source-authorized
window for this subfamily:

2024-07-30T17:21:13Z <= source timestamp < 2025-01-01T00:00:00Z.

This boundary is chosen exclusively from public source-code authority before bounded on-chain census results.

It does NOT claim that the public commit timestamp equals the exact on-chain deployment time.
It simply avoids asserting source semantics before public source authority exists.

Events before this boundary are outside this subfamily's source-audited period and are not used
to pass or fail the family coverage rule.

## Census rule

Use the already frozen discriminator:
5f6f7c6956a9bb22

and the exact realized instruction rules in:
DRIFT_LIQUIDATE_PERP_WITH_FILL_CENSUS_FREEZE_V0.1.md.

For transport efficiency, the source-audited window may be split into fixed calendar partitions:
- 2024-07-30T17:21:13Z .. 2024-08-01T00:00:00Z
- 2024-08-01 .. 2024-09-01
- 2024-09-01 .. 2024-10-01
- 2024-10-01 .. 2024-11-01
- 2024-11-01 .. 2024-12-01
- 2024-12-01 .. 2025-01-01

All partitions are included.
No partition may be omitted because of its results.

## Outcome firewall

This is source-only.
No price, return, PnL, 2025 market outcome, or 2026 market outcome is authorized.

## Firewall

prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

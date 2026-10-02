# DLS ROUTE A3A — ADAPTIVE PROGRAM-HISTORY TRANSPORT ADDENDUM V0.1

Date: 2026-10-02
Status: FROZEN TECHNICAL TRANSPORT / SCIENCE UNCHANGED / PROTECTED OUTCOMES CLOSED
Branch: dls-field-enrichment-v01

## Authority
Parent scientific/source authority:
- DLS_ROUTE_A3_GTFA_EQUIVALENCE_FREEZE_V0.1.md
- ROUTE_A3_GTFA_EQUIVALENCE_PASS run 36969189081 / artifact 11210144684
- DLS_ROUTE_A3_PROTECTED_2025_ACQUISITION_FREEZE_V0.1.md

A3 program-level monthly capacity failed only because all three bounded probes exceeded the
predeclared 25-page transport ceiling:
- marginfi Jan 2025: >=25,000 successful program transactions
- Save/Solend Jan 2025: >=25,000
- Kamino May 2025: >=25,000

That result is transport density, not source/scientific divergence.

## Scientific semantics — unchanged
Preserve exactly:
- four frozen protocol classes;
- current frozen program IDs;
- exact discriminators;
- canonical RAW normalizer validated by A2/A3;
- explicit successful-transaction rule;
- canonical historical/current account shapes applicable to 2025;
- exact collateral-unit mapping;
- source window [2025-01-01, 2026-01-01);
- canonical identity = signature + instructionAddress;
- SOL target mint;
- 60-second clustering;
- existing V0.2 finalizer;
- strategy/direction/timing/cost/economic gates.

No market data is part of this route.

## Adaptive transport
Initial shard = each exact UTC calendar month.

For each program/month:
1. signatures-only gTFA probe:
   - address = frozen program ID
   - transactionDetails = signatures
   - sortOrder = asc
   - limit = 1000
   - status = succeeded
   - exact blockTime [start,end)
   - max 8 non-empty pages.
2. If terminal pagination occurs <=8 pages, interval is a LEAF.
3. Otherwise split at exact integer Unix-second midpoint and recurse.
4. Minimum interval = 60 seconds.
5. Maximum recursion depth = 20.
6. Exhaustion at minimum interval = TRANSPORT_BLOCKED; never treated as empty/complete.
7. Every leaf is refetched with transactionDetails=full, same filter.
8. Full count must equal signatures-probe count.
9. Maximum full pages per leaf = 10.
10. Leaves must form an exact gap-free, non-overlapping partition of the month.

No transaction is sampled or dropped.

## Solend shared transport
Save0c and Save11 share one program ID. A single monthly full-history transport may feed both
canonical decoders. It MUST emit two separate finalizer-compatible receipts:
- save0c-2025MM.json
- save11-2025MM.json

Each receipt is independently adjudicated under its own discriminator/shape/unit rules.

## 2025 shapes/unit mapping
Marginfi:
- liquidation discriminator d6a997d5fba756db
- account_count >=10
- collateral role asset_bank = accounts[1]
- mint/decimals resolved with the same finalized Bank dataSlice offset 8 length 33 and owner check.

Save0c:
- discriminator 0x0c
- exactly 12 accounts, 9-byte data
- withdraw_reserve = accounts[4]
- mint/decimals resolved with same finalized Reserve dataSlice offset 42 length 33, owner check;
  collateral mint slice offset 227 length 32 retained.

Kamino 2025:
- discriminator b1479abce2854a37
- Release-1.6+ layout only: account_count >=20; token-program accounts 16..18; sysvar 19;
  32-byte data
- collateral-underlying mint = accounts[8] (direct withdraw_reserve_liquidity_mint)
- dynamic accounts >=20 retained but do not alter semantics.

Save11:
- discriminator 0x11
- exactly 15 accounts; data length 9 or 10
- collateral-underlying authority = token unit on primary account[8]
- optional account[2] absent or exact-match only
- canonical pre/post token metadata only.

## Output contract
Exactly 48 finalizer-compatible protocol-month receipts:
- classification PROTECTED_2025_PROTOCOL_SOURCE_PASS only if that exact partition has zero
  decoder, timestamp, duplicate, mapping or transport errors;
- exact window_start/window_end;
- rows include protocol/class/signature/instructionAddress/slot/timestamp/collateral_mint;
- duplicate_count=0; error_count=0.

Additional transport diagnostics are allowed.

## Final gate
Run unchanged:
source/finalize_protected_2025_source_v0_2.py

Only PROTECTED_2025_SOURCE_AUTHORITY_PASS may authorize market access.

## Firewall
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
post_outcome_tuning=false
purchases=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE

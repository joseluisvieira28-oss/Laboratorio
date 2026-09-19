# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY PREDICTOR ACTIVE-RESERVE DECIMALS UNION REMEDIATION V0.1

Status: **FROZEN AFTER PREDICTOR ASSEMBLY FAILURE / BEFORE FUTURE LIQUIDATION OUTCOMES**
Date: **2026-09-19**

## Triggering state

Run `35427783826` attempt 2 completed:
- preflight PASS;
- calendar PASS;
- global/eMode/oracle source PASS;
- all **8/8 reserve shards PASS**.

The predictor then failed before persistence with:

`DISCOVERY_RECONSTRUCTION_FAILURE — reserve decimals union mismatch`

Safety receipt confirms:
- health-factor reconstruction had begun;
- overhang was **not** persisted/computed to a Discovery predictor receipt;
- future liquidation outcomes remained unopened;
- 2024 outcomes unopened;
- 2025/2026 unopened;
- market returns/PnL unopened.

## Root cause

The reserve-shard layer was already prospectively remediated to require decimals only for reserves whose canonical `init_block` is at or before the frozen 2023 event ceiling. This is necessary because the 37-reserve master includes reserves initialized after the 2023 Discovery period.

The predictor aggregator still enforced the obsolete pre-remediation invariant:

`set(all_37_reserves) == set(reserve_decimals)`

The exact eight PASS shard receipts contain:
- 37 unique canonical master reserves;
- **27 unique active-2023 reserve decimals**;
- the 27 decimals keys are a strict subset of the 37 master reserves.

This is internally consistent with the already-frozen temporal eligibility rule and is not an economic result.

## Authorized remediation

Replace only the obsolete predictor assembly guard with the same temporal invariant already frozen upstream:

- exact master reserve union remains 37;
- active-2023 decimals union must be exactly 27;
- decimals keys must be a subset of the 37-reserve master.

No missing decimal is imputed.
No active 2023 reserve may lack decimals.
No reserve is dropped from the canonical master.

## Frozen science unchanged

No changes to:
- 2023 period or snapshot clock;
- borrower universe;
- Aave oracle/eMode semantics;
- 10% primary shock;
- overhang definition;
- next-24h liquidation outcome;
- statistic/inference/gates;
- 2024 firewall;
- 2025/2026 lock;
- trading/execution rules.

This correction is assembly consistency only. Future liquidation outcomes were not opened before this freeze.

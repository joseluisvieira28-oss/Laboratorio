# V0.4.4 FIFTH-CHAIN SOURCE-ONLY EXPANSION AMENDMENT

Date: 2026-10-07
Parent V0.4 freeze: 71ac365e709b0e0d7074caed7e842f513207aa85
Valid V0.4 census/event counts inspected before this amendment: NO
Market outcomes opened: NO

## Reason

The originally frozen KAVA -> INJ -> SEI qualification order produced no fifth chain with two independent public/free historical paths. This amendment expands source qualification BEFORE any valid V0.4 event census or materiality counts.

No candidate is added because of observed unbonding frequency or economic outcome.

## Frozen expanded order

After exhausting KAVA, INJ and SEI, test:
6. Terra 2 / LUNA (phoenix-1)
7. Archway / ARCH
8. Coreum / CORE
9. Axelar / AXL

Stop at the first candidate that passes all source-only qualification requirements.

## Qualification requirements

Candidate must prove, before any event census:
- production chain active for enough of the frozen 2023-2024 interval to contribute valid chain-days;
- native token uses comparable Cosmos SDK x/staking voluntary undelegation semantics, version/fork pinned;
- at least two independently operated public/free historical evidence paths covering the eligible interval;
- historical raw block and block_results capability sufficient for the frozen V0.4 lifecycle;
- >=12 consecutive months pre-2026 liquid-market source capability metadata, without reading prices/returns/volume outcomes.

Archive labels in chain-registry are discovery hints only, not proof. Fixed historical blocks must be fetched and reconciled.

## Governance

Materiality remains 10 bps.
Hard sample bar remains >=40 material chain-days TOTAL across >=5 chains.
No market outcomes.
No chain may be skipped after passing source qualification because another candidate appears richer in events.

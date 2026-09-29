# DLS PROTECTED 2025 SOURCE — PARTITIONED TRANSPORT ADDENDUM V0.2

Date: 2026-09-29
Status: FROZEN TECHNICAL TRANSPORT ADDENDUM / OUTCOME-BLIND

The V0.1 full-year source scan is scientifically unchanged but may create very large SQD responses.

V0.2 permits only this transport decomposition:
- Q1 [2025-01-01, 2025-04-01)
- Q2 [2025-04-01, 2025-07-01)
- Q3 [2025-07-01, 2025-10-01)
- Q4 [2025-10-01, 2026-01-01)

for each of the exact four frozen protocols.

The collector implementation, program IDs, discriminators, account roles, mint resolution, success conditions and firewalls are unchanged.

Finalization must:
- require exactly 16 partition receipts;
- require all 16 partition receipts PASS;
- verify exact expected interval identity;
- union all event rows;
- fail on duplicate canonical event identity across partitions;
- apply the identical 60-second clustering rule once to the full union;
- exclude T0 >= 2026-01-01;
- never open prices or outcomes.

Terminal classification is identical:
PROTECTED_2025_SOURCE_AUTHORITY_PASS / PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED.

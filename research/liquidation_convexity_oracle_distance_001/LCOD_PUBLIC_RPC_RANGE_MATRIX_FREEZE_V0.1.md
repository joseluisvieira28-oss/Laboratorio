# LCOD PUBLIC RPC BORROW-RANGE MATRIX FREEZE V0.1

Frozen: 2026-09-25
Source transport only. Outcomes closed.

Use the already cross-checked BLUECHIP Borrow truth fixture at block 25398769.
Probe only transport capability; do not infer protocol state from endpoint failure.

For each public Ethereum RPC route test total ranges:
1, 101, 1001, 5001, 10001, 50001 blocks centered on the fixture.

A probe PASS requires the exact expected Borrow transaction plus filter-clean logs.

A route is eligible for a bounded historical census only if >=1001 blocks pass.
The chosen census chunk must not exceed that route's largest passing tested size.

Any event set used scientifically must later be checked for complete contiguous
coverage and current-MCP contradiction coverage.

No market/liquidation outcome is accessed.

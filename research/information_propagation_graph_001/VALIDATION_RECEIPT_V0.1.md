# VALIDATION RECEIPT V0.1

Lab: INFORMATION-PROPAGATION-GRAPH-001
Date: 2026-09-24
Scope: local offline unit validation of canonical event-schema logic.
Market outcomes inspected: NO.
Exchange mutation: NO.
Live trading: NO.

## Command

python -m pytest -q

## Result

3 passed in 0.05s

Validated invariants:
1. Binance aggTrade normalization prefers semantic trade time T while preserving exchange publish/event time E.
2. Deribit order-book normalization preserves change_id and prev_change_id sequence evidence.
3. Missing source event timestamp fails closed for event-time use.

## Limitations

This receipt validates parser/schema invariants only.
It does NOT validate:
- network clock synchronization;
- live exchange connectivity;
- historical source completeness;
- cross-venue causal ordering;
- predictive edge;
- profitability.

Next valid step remains source/corpus pinning and collector/replay validation under the frozen protocol.

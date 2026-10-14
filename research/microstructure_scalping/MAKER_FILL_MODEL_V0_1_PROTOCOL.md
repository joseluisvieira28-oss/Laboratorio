# MAKER FILL MODEL V0.1 — CONSERVATIVE PROTOCOL

Date: 2026-09-25
Status: PRE-OUTCOME

## Purpose
Provide a lower-bound passive-fill model that does not manufacture fills from aggregated L2.

## Frozen rules
1. Order becomes eligible only after the effective placement timestamp.
2. Trade at exactly the same timestamp as placement is NOT credited.
3. BUY maker can be filled only by subsequent taker SELL volume.
4. SELL maker can be filled only by subsequent taker BUY volume.
5. Only trades at the exact passive order price count.
6. Trades through the level are deliberately ignored.
7. Quote touches, quote deletion and book movement are never sufficient for a fill.
8. Full fill requires cumulative eligible executed volume >= assumed queue ahead + our full order size.
9. Queue-ahead sensitivity must be reported at 1x, 2x and 5x displayed queue.
10. Cancellations ahead never reduce assumed queue.
11. Ambiguous/non-monotonic event time = fail closed.
12. Partial fills are ignored in V0.1.

## Consequence
This model is intentionally pessimistic. A candidate that fails under it may still be executable in reality, but the lab will not claim that without stronger order-level data.

A candidate that survives still requires forward MEXC replication because historical research source and intended execution venue differ.

# DLS ROUTE A2 — TIME-BOUND CURSOR TRANSPORT PROBE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY TECHNICAL PROBE

Purpose:
Validate a free archival-RPC transport technique for month-bounded Protected-2025 acquisition without
using Helius paid getTransactionsForAddress.

Frozen validation interval:
2024-07-19T19:30:52Z <= blockTime < 2024-07-20T00:00:00Z

Target address:
So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo

Immutable expected census from Route A2 equivalence execution:
- in-window program signatures = 1,868
- explicit-success transactions = 1,708

Probe:
1. Resolve approximate boundary slots from the already-used SQD timestamp resolver.
2. Using Helius archival standard RPC getBlock only, locate:
   - one arbitrary transaction signature strictly before START;
   - one arbitrary transaction signature at/after END.
3. Use those signatures solely as time/slot cursors for standard getSignaturesForAddress.
4. Paginate deterministically with limit 1000 and finalized commitment.
5. Count unique target-address signatures whose blockTime is inside the frozen interval.
6. Do NOT fetch transaction payloads and do NOT inspect prices/outcomes.

PASS requires:
- exact 1,868 unique in-window target-address signatures;
- zero duplicate signatures;
- all returned blockTime values present;
- deterministic lower-bound termination;
- start cursor blockTime < START;
- end cursor blockTime >= END.

This validates transport cursor semantics only. It changes no decoder, event population, scientific rule,
strategy, cost, threshold or outcome boundary.

Forbidden:
- paid gTFA / getTransactionsForAddress;
- market prices;
- 2025 economic outcomes;
- 2026 outcomes;
- live trading / orders / wallets / exchange mutation;
- main merge.

Trading authority: NONE.

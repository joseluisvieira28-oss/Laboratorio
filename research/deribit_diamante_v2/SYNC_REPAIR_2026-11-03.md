# Parallel source repair — 3 November 2026

Technical change only. Scientific freeze e34ad0732abf1574735006b33307ddf5653fbaa9 and economic parameters remain unchanged. No main changes, orders, private exchange credentials or paid sources.

## Proven failure
The original six raw responses, retained in entry-0809.zip at commit 91f5f9873db731004a271560186563daaf6ff6c2, independently reproduce book skew 4161ms (maximum 1000ms) AND index distance 22.223010063s (maximum 10s). Book ages 0.728770018s and 2.661046028s individually pass. Original status remains SOURCE_BLOCKED, zero accepted entries. No replacement or replay into the economic sample.

## Repair
- Preserve the same six public GETs, symbols selected by the frozen rule, quantities, depth, source gates and costs. Move the index GET after metadata, summaries and deliveries, immediately before selection and book dispatch. This uses a fresher current index without changing the selection rule.
- Dispatch both books once using two threads in one Python process. No retry, substitute symbol or relaxed skew. Parallel dispatch reduces avoidable serial waiting; it does not guarantee atomic quotes or fills.
- Reserve source names/request budget under a lock; bind each book's age to its own received timestamp rather than the final manifest item. Wait for all in-flight requests even if one fails; retain successful raw responses and failed-request errors.
- Persist raw server timestamps, local request/receipt timestamps, hashes, measured skew and index distance. Existing economic formulas and independent economics audit are unchanged.
- Separate sync-check mode records no structures, forecast, entry selection or PnL and is rejected by settlement. Uses next-day ATM pair and production books, once only, outside the economic sample. Independent audit_sync.py imports no collector code and recalculates raw hashes/timestamps.

## Validation and deployment
13 offline tests passed locally: seven inherited economics checks plus concurrent rendezvous/reversed completion, own-receipt age, failed request preservation/no retry, request budget, exact 1000/1001ms boundary and diagnostic settlement rejection. One bounded GitHub Actions diagnostic is configured for this repair, not recurring and not a replacement for today's attempt. Its measured result is authoritative; a network or source failure is not an economic rejection. No repeated live attempts to obtain a PASS.

Future scheduled sessions must load the updated branch's probe.py and use the parallel collector directly; never reconstruct serial GETs with an alternative tool. If that runtime cannot reach public Deribit, preserve SOURCE_BLOCKED. Keep original schedule, window, one daily attempt and no backfill. This repair establishes neither profitability nor a valid economic entry today.

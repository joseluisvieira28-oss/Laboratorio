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

## Measured result and independent replay
One diagnostic [run 41602441575](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41602441575) succeeded at code ae2ab0ca818a4a7d5e7700cc30252e6f50f4392f. Six GETs, 08:19:45.407646–08:19:46.696596 UTC. Call/put server timestamps 1793693985558 / 1793693986141: skew **583ms <=1000ms**. Index distance **0.320705891s <=10s**; individual ages 1.133037806s / 0.555595875s. Separate audit verified all six raw SHA256s and independently reproduced timings, both in Actions and from the downloaded original ZIP. No forecast or economic entry was computed.

Original Actions artifact 13214996919, 188276 bytes, ZIP SHA256 f18f8b45cae28abb29db50135d5369c839590c89bcd024720057111d22a5a60c. Exact original ZIP preserved as evidence/2026-11-03/sync-diagnostic-41602441575.zip; it is NOT an entry archive.

## Next scheduled session
This Work runtime's direct Deribit connection timed out; the GitHub runner succeeded. A dedicated branch-only forward-request workflow therefore runs the actual Python collector in one job, triggered ONLY by a dated FORWARD_REQUEST.json update. Adding its workflow does not request a session. The existing daily task must submit that request within the unchanged frozen window, rather than reconstructing serial API calls. Runner queuing can still miss the window; the wrapper then preserves MISSED_SESSION with zero market requests. A previously preserved day, including a failure, is skipped without recollection. ZIP evidence is committed only to the research branch; no main merge or extra scheduler is introduced.

15 offline tests now include duplicate blocked-day protection and late-runner zero-source behavior. The new daily runner is prepared and tested offline; its first scheduled valid entry remains unproven. Preserve today's blocked entry, diagnostic separation, P1/C0 and all frozen gates. No economic promotion.

# DEFI-LIQUIDATION-SHOCK-001 — SQD TIMESTAMP RESOLVER TECHNICAL CORRECTION V0.4.2

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / TECHNICAL ONLY / SOURCE-ONLY

V0.4.1 fail-closed receipt is preserved unchanged.

Observed:
- timestamp endpoint returns JSON field `block_number`;
- for known boundary timestamps it returned a nearby block at/before the event slot;
- one control returned HTTP 529 overloaded.

V0.4.2 changes transport/parser only:
1. parse `block_number` as the resolver seed;
2. retry HTTP 429/529/5xx with bounded exponential backoff;
3. query `finalized-stream` from the seed through seed+64 requesting block number+timestamp only;
4. select the first returned finalized block whose timestamp is >= target timestamp;
5. for known calibration timestamps, require the selected slot <= the known event slot and the selected block timestamp >= the target timestamp;
6. no transaction/instruction/event data is requested during timestamp calibration.

Scientific populations, event filters, dates, success semantics and firewalls remain unchanged.

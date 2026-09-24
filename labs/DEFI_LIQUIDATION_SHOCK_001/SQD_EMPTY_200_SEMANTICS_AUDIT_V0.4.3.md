# DEFI-LIQUIDATION-SHOCK-001 — SQD EMPTY-200 SEMANTICS AUDIT V0.4.3

Date: 2026-09-24
Status: SOURCE-CONTRACT AUDIT / TRANSPORT ONLY / OUTCOME-BLIND

## Official contract checked

SQD Portal API RFC `network-rfc/11_portal_api.md` states for HTTP 200 stream responses:
- clients must use the last returned block number to continue scanning when more blocks are needed;
- matching blocks up to the returned progress block are guaranteed not to be skipped;
- a returned block may be included solely to designate scan progress;
- for Solana, an empty block list is allowed only when the query is bounded and the entire requested block/slot range has been skipped.

The same RFC states `/finalized-stream` has the same response semantics as `/stream`, except it only returns finalized blocks and never returns 409.

## Consequence for this census

A normal UTC-day census interval spanning many existing Solana slots cannot infer completeness from an HTTP 200 body containing zero NDJSON lines unless it independently proves the entire requested slot interval was skipped.

Therefore:
- V0.4.2 logic that treats an arbitrary empty 200 body as a complete zero-additional-match termination is NOT sufficient for authoritative daily completeness.
- Any V0.4.2 full census run using that behavior is transport-superseded for final authority.
- This is not a scientific result and not NO_EDGE.

## V0.4.3 rule

For the identical request:
- retry empty HTTP-200 bodies up to six times with bounded backoff;
- if a non-empty response arrives, resume normal last-block continuation;
- if the empty body persists, classify the UTC day `SOURCE_CHUNK_BLOCKED`;
- never infer zero events/completeness from an unproven empty-body response.

No population, decoder, date boundary, success rule, dedup rule, RAW sample or economic firewall changes.

# OKXFIBR V0.1.2 TABLE-CONTEXT PARSER REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Run 37573687669 successfully enumerated the official archive through before 2023.
- 305 official Trading-update articles were enumerated.
- 48 funding-interval candidate articles were identified.
- Exact publication timestamps were recovered for nearly all candidates.
- Funding interval tables were parsed (including multi-row/multi-contract tables), but 0 events became eligible because the first parser required effective date/time to appear inside the same table row.
- Official OKX articles commonly place adjustment date/time in a heading or paragraph immediately before the table.

This is a source-structure/parser limitation, not a sample or outcome verdict.

Allowed remediation:
- deterministically associate each parsed interval table with nearest preceding official heading/paragraph containing an adjustment date/time;
- for single-event articles, use an unambiguous article-level adjustment date/time only when exactly one post-publication candidate exists;
- preserve official article URLs, 2023-2025 calendar, interval-shortening definition, clustering, sample gates and verdict taxonomy;
- preserve all candidate articles irrespective of expected market outcome.

Forbidden:
- no mark/index/funding/return/PnL values;
- no search-engine-defined sample;
- no event selection from outcomes;
- no threshold changes;
- no 2026;
- no main merge/trading/private endpoints.

Runs 37573428179 and 37573687669 remain preserved.

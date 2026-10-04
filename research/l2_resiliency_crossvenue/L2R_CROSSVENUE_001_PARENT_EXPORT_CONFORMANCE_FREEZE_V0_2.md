# Parent event-state export conformance freeze V0.2

Status: FROZEN_PRE_OUTCOME_SOURCE_ONLY. Starting authority commit e43e33c84d735635f99cc012118e33da0583c6d9.

The V0.1 export specification and parent science are unchanged. V0.2 adds the required field names, stable segment/creation-order event IDs, UTC anchor dates, exact round-trip float serialization, R selected envelope/payload timestamps, lateness, same-side top-five depth, RR and class. Zero depth and missing source timing use the specified status labels. Gzip headers use mtime=0 and an empty filename for deterministic output bytes.

Exporter SHA256: 9ff76012f1796549232481da97832404dfe98c6e6737cf4f591823a05b53fabe.
Parent runner SHA256 remains 7f135689afd9f51a758e2c98b5c8da9fe3c7f3eca15f40eced7fdb53b03d2eaf. Its bytes are verified before importing source parsing/constants. Its main and real-data outcome functions are never invoked.

Historical reference receipt SHA256 c4892879f06df02d57685f8bebd4653e3a1fd2457e6d90c522c1ac065714a627 is bound to the branch's parent closeout. Only source identity, timing, group counts and mean RR enter new identity checks; parent response fields do not enter computations.

All 8,707 RAW bindings, 50,717,748 records, 50,717,668 accepted states, 80 stale states, 158 equal payloads, 11 segments, 9,181,478 sweeps, ASK/BID and per-segment counts must reproduce exactly. Every horizon 1/5/15/60s must reproduce available, late-missing and segment-end-missing counts exactly. The 60s state is used only for cell timing eligibility; only its timestamp/status is exported, never a price or response.

Each of the six cells must reproduce exact anchors, zero-depth, timing-missing, valid and WEAK/STRONG counts. Mean RR uses math.isclose with absolute tolerance 1e-10 and relative tolerance 1e-12, frozen solely for deterministic float summation/serialization differences. Counts have no tolerance. No failed identity gate permits scientific repair.

Synthetic conformance tests compare parsing/state, counts, timing and RR aggregation directly with the byte-frozen parent on synthetic books, including stale/equal payloads, ambiguity, exact horizons and repeated deterministic export. All three tests passed on 2026-10-04. They do not run real parent outcomes.

No Binance access, protected-year source access, parent price response, PnL, trading, private/account endpoint, mutation, wallet, spending or main merge is permitted in this export.

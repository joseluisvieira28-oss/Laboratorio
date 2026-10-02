# DLS PROTECTED 2025 — MARGINFI PROGRAM-ONLY SQD TRANSPORT ADDENDUM V0.3

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY TECHNICAL TRANSPORT / OUTCOMES CLOSED

Problem:
The canonical Protected-2025 Marginfi query using SQD server-side programId + d8 discriminator repeatedly
returns HTTP 503 availability_error / retries_exhausted across 2025. Other protocol/month partitions can
complete. This is transport/index availability, not scientific evidence.

Authority:
Use the same SQD finalized-stream dataset, timestamp resolver, canonical Marginfi program ID, exact
d6a997d5fba756db instruction prefix, success predicate, account shape, asset_bank collateral mapping,
current finalized bank dataSlice mapping, canonical event identity and monthly window.

Only the server-side query is widened:
- OLD transport: programId + d8 discriminator
- V0.3 transport: programId only
- Local decoder MUST retain only instructions whose decoded bytes begin exactly d6a997d5fba756db.

Pre-outcome equivalence evidence:
The existing Marginfi/Save0c field-enrichment population route queried programId-only and locally filtered
the frozen prefix. It exact-joined the pre-existing canonical source population through 2024.
Specific latest frozen Marginfi partition:
- 2024-12 FIELD_ENRICHMENT_PARTITION_PASS
- artifact 10927608033
- artifact SHA256 0228f85921f9a30d6310b0fa3e5798f2695b9750c4add737e82a7611959892a4
- 4,880 exact canonical rows
- missing=0, extra=0, duplicates=0, semantic conflicts=0.

Canonical Protected-2025 collector blob at freeze:
8d59b5798770d43bbc7a7e15cd239dd355998145

Implementation requirement:
The V0.3 Marginfi collector must be generated from that canonical collector with exactly one scientific-
neutral query change: omit c[filter_key]/filter_value from the SQD request. Local prefix filtering,
transaction success, mapping, month boundaries, dataSlice semantics, row schema and firewalls remain exact.

No token amount, price, return, PnL, funding or market-direction field may be opened.
No 2026 source population.
No paid source.
No trading, orders, wallets, exchange mutation or main merge.

Classification remains:
PROTECTED_2025_PROTOCOL_SOURCE_PASS / PROTECTED_2025_PROTOCOL_SOURCE_BLOCKED

Trading authority: NONE.

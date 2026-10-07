# V0.5.1 — ARCHWAY KYVE + REST ARCHIVE AMENDMENT

Date: 2026-10-07
Parent V0.5 freeze: c77013a5da826498c936b86a42902aed61c7dcd4
Outcomes opened: NO
Archway event counts inspected: NO

Before opening any Archway completion/event count, V0.5.1 freezes two additional source-only historical paths:

1. KYVE mainnet block pool for source-id archway-1, pool id 2, using KYVE finalized bundle metadata + checksum-verified public storage payloads.
2. Public Archway REST archive providers exposing Cosmos base Tendermint block-by-height APIs.

Qualification test is fixed-height only. Use Archway upgrade height 3,554,500 as the initial canonical anchor because it is independently pinned in KYVE source-registry as the v6.0.0 upgrade boundary. Do not query complete_unbonding counts until source reconciliation succeeds.

PASS requires:
- height 3,554,500 is inside 2023-2024 by canonical timestamp;
- KYVE returns the block for that exact height from pool 2 and bundle checksum validates;
- an independently operated REST/RPC archive returns the same canonical block hash/time/app-hash or equivalent complete header commitment;
- chain id = archway-1.

If the anchor falls outside 2023-2024, choose the next earlier/later version-pinned upgrade height from the source-registry before opening event counts.

No market data or economic outcomes.

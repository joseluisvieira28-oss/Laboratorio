# LCOD BLAST BORROW-RANGE CAPABILITY FREEZE V0.1

Frozen: 2026-09-25
Stage: SOURCE TRANSPORT ONLY
Outcomes: CLOSED

Truth fixture:
- Spoke: BLUECHIP 0x973a023a77420ba610f06b3858ad991df6d85a08
- Borrow block: 25398769
- Expected tx: 0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f
- Borrow topic0: 0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd

Probe symmetric total block windows centered on the fixture:
1, 101, 1001, 5001, 10001, 50001, 100001, 250001 blocks.

A range PASS requires:
- eth_getLogs succeeds;
- expected tx is present;
- every returned log matches the pinned address/topic.

Largest passing range <=100001 is eligible as the conservative full-census
chunk size. 250001 is diagnostic only and may pass without being selected.

No market/liquidation outcome is accessed.

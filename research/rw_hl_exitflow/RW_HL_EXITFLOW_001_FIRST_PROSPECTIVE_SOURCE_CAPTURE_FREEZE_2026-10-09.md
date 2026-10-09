# RW-HL-EXITFLOW-001 — FIRST PROSPECTIVE SOURCE CAPTURE AUTHORITY V0.1
Date: 2026-10-09
State: AUTHORIZED_FOR_PUBLIC_MARKET_DATA_COLLECTION_ONLY

Precursor source-only G1 technical PASS:
https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37938587198
- 14/14 synthetic tests; 178 valid current asset contexts twice (~75 seconds apart).
- 24 2024-01-01 BTC hourly funding records from unauthenticated `fundingHistory`, historical PRICE RETURNS not opened.
- Public OI values only existed in current live `metaAndAssetCtxs`. Official S3 historical asset contexts are requester-pays, NOT accessed; 2023–2024 historical OI is source-blocked under no-spend authority.

## Public-only forward SOURCE authority (no trading)
Trigger *exactly one* bounded recording from branch `research/rw-hl-exitflow-source-first-2026-10-09`:
1. Make 3 public `metaAndAssetCtxs` calls (no account address, auth, trades, orders) spaced exactly **60 seconds** between call starts after the first network read.
2. Capture all returned public base-perp markets with aligned `coin`, `openInterest`, `markPx`, `funding` and `dayNtlVlm`, including zero OI if valid. Delisted/unavailable context fields explicitly counted as excluded; no filling or symbol backfilling.
3. Record receive timestamp UTC and official response, SHA256 per snapshot, SHA-linked order and market-universe intersection count. No price-change calculation or event classification in source run.
4. Immutable output under `research/rw_hl_exitflow/intake/2026-10-09/[time]_[run_id]/` on SAME research branch and mirrored GitHub artifact. If path exists, FAIL rather than overwrite. No main merge or PR merge.
5. If an API call fails: emit explicit fail-closed receipt and preserve only existing partial observations as PARTIAL, never claim a continuous source stream.
6. No 2025/2026 backfill; these are prospective 2026 observations captured AFTER original G0/G1 authority. Do not name a new token `listed` based solely on its first appearance (snapshot detection interval is NOT exact listing timestamp).

This 3-observation first block is only an end-to-end transport/durability test. It CANNOT test the Robot Wealth informed-short thesis or any economic edge; future signal rules, event thresholds and economic costs must be separately pre-frozen after source feasibility and adequate coverage.

No scheduled GH `schedule` on a research branch can be relied upon; the workflow is one-shot on push to its script or a manual permitted trigger. Automatic daily observation remains an explicitly **operational blocker** if a long forward is pursued, and no hidden paid cron/cloud resource is authorized.

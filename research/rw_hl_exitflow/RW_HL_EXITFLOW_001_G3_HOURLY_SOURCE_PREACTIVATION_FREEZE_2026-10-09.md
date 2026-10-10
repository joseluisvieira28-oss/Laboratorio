# RW-HL-EXITFLOW-001 — G3 HOURLY POINT-IN-TIME SOURCE / FAIL-CLOSED PREACTIVATION FREEZE
Date: 2026-10-09
State: FROZEN **SOURCE ONLY**, 2026-10-09 market economic outcomes still CLOSED.
Parent evidence: G1 178 live markets / G2 178 source-bound markets, 159 OI changed, 15 last-negative-funding, 6 OI-up+negative-funding within ~2minutes. Those counts are SOURCE PILOT, **NOT training/trading outcomes**. Do not use them to pick target coins.

## Primary source identity
Unauthenticated read-only Hyperliquid `POST https://api.hyperliquid.xyz/info`, body EXACTLY `{"type":"metaAndAssetCtxs"}` for validator-operated base perpetual markets (no HIP-3 dex selected). Capture all markets, do not filter by result. Source version: original HL public response; coin identity includes exact case/name; capture local **receive-time** UTC (does not prove exact exchange T0). Preserve full source fields available: `coin,openInterest,markPx,funding,dayNtlVlm`, raw numerical strings; never combine spot and HIP-3 assets without a new distinct authority.

## Prospective hourly sampling only
- Candidate operational slot = **hour of actual received response timestamp in UTC**, never slot claimed by GitHub trigger; no hidden backfill. At most ONE canonical sample per actual UTC hour, first writer wins. Concurrency serialized by branch job group.
- Snapshot serialized in unambiguous deterministic sorted JSON and SHA-256, immutable path `research/rw_hl_exitflow/forward_source/hourly/YYYY-MM-DD/HH.json`; any duplicate or change fails closed. Preserve ORIGINAL issue/receive times and GitHub run ID; do not rewrite previous samples.
- Do not invent a source observation from missing hours; track absent UTC hours explicitly as `MISSED_SOURCE_HOUR`. A GitHub CI green indicator never counts as a snapshot absent exact append-only receipt.
- A GitHub Action `schedule` in this **non-default scientific branch is NOT a functioning autonomous scheduler**. This branch uses a manual/current-hour one-shot trigger with the existing `source_hourly_trigger.txt`; no claim of automatic hourly capture. Automatic scheduling requires an authorized external orchestration route, or a separate deployment/default-branch action (not permitted here by original no-main/no-Render guardrail).
- Freshness of quote, trading conditions and execution prices NOT verified from `markPx`; mark is not actual fill.
- Test contract: source identity, no account/private endpoints, OI>=0, markPx>0, funding finite, >=100 valid current perp market rows, stable exact market name keys, timestamp timezone UTC and no duplicate per-hour slot.

## Ex ante source coverage gate for future activation
First 14 **complete UTC days** beginning with the first full UTC day AFTER an explicitly approved *automated* hourly source scheduler starts (not today's ad-hoc G1/G2 snapshots). Exactly 336 expected UTC hours.
- >=320/336 timely unique canonical hourly snapshots (>=95.238%).
- >=14 distinct UTC days each containing at least one eligible source snapshot.
- >=100 markets with valid nonzero OI/mark/current funding in >=95% of all source snapshots.
- no unresolved source SHA/identity/time/duplicate conflict; record no-data outages as missed, never resynthesize.
- candidate market cohort must be first-seen observationally; to claim official new-listing T0 require separate official listing evidence.
- Events remain `SOURCE_NOT_READY` until a **different immutable G4 source-event definition freeze** is committed before analyzing any future cross-asset price/returns. G3 currently counts only source observations/coverage.

If these gates fail, classify `G3_SOURCE_COVERAGE_INSUFFICIENT_OR_BLOCKED` and do NOT perform post-outcome tuning; no economic verdict. Strong source gate is necessary but insufficient for economics.

## Compulsory economic model design, NOT YET AUTHORIZED
One separate forward G4 authority must freeze **signal-time** OI growth/funding sign/price-relative weakness, exact control groups and cost/execution source. A potential signal of short-side pressure is not a confirmed insider trade: short OI growth implies corresponding LONG newly opens too. Hyperliquid negative funding means short pays financing hourly. Base taker fees 4.5bps entry+4.5bps exit=9bps before spread/slippage, special accounts/markets may vary (official fees page). No static `markPx` source proves fill quality, queue, spread, liquidity, funding settlement or capacity.

Protected 2023/2024 historical OI `s3://hyperliquid-archive/asset_ctxs/*.csv.lz4` requester-pays; no payment authorized. Existing 2025/2026 study holdouts cannot be recycled. No main merge, Render deploy/mutation, wallet, capital, auth exchange, order or profit resolution.

Terminal source label for this authority until 14 real future dates accrue: **`G3_FORWARD_COVERAGE_NOT_READY`**. This is not `NO_EDGE` nor `MICRO_LIVE_GO`.

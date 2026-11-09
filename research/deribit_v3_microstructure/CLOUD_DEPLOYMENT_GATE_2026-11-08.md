# V3 — cloud deployment gate (2026-11-08)

Status: **DESIGN / NO DEPLOYMENT**. No cloud job was activated, no prospective session was started or scheduled; still 0/20. LIVE and expiry economics NO-GO. Existing V2 freeze, PR #340, and default branch must remain untouched until independent review.

## Confirmed infrastructure
- Render workspace `Laboratorio` contains multiple already deployed web services. One unrelated service has a 1GB persistent disk. Reusing that service without an isolation and security review would risk unrelated application/data: **DO NOT MODIFY IT**.
- No Render Postgres instances returned in workspace.
- Render Cron Jobs have at least US$1 monthly charge and **cannot mount persistent disks**. Do not create a paid cron without a separate spending decision.
- GitHub Actions `schedule` runs on the **default branch only**, may be delayed or dropped, and a workflow present solely on draft PR #341 is NOT activated. Do not merge V3 / PR #340 simply to schedule.
- GitHub workflow artifacts on a public repo expire in at most 90 days. Artifacts alone do not satisfy the extended 180-day / six-month scientific retention: keep long-lived source evidence in a separately protected evidence branch or object storage, with SHA-256 and external anchor.

## Proposed no-new-spend architecture (NOT DEPLOYED)
1. Separate and code-reviewed scheduling launcher on the default branch ONLY after explicit authorization; it must fetch a **pinned, immutable V3 collector commit**, not track a moving PR branch.
2. Single-writer Git evidence branch `evidence/deribit-v3-forward` checked out with full history each run. Root: `research/deribit_v3_microstructure/forward_evidence` on that branch. The collector's day claims, rejected attempts, raw source responses, manifests and receipts must be committed and pushed to that same branch on **every attempt**; never use a fresh ephemeral root as if it were a continuous 20-session ledger.
3. Schedule a few minutes before 08:05 UTC; launcher may wait until 08:05 only if job actually started early. Before calling the collector, compare actual UTC clock to `[08:05:00,08:10:00)`. If started too late, log `MISSED_WINDOW`, do NOT backfill, count or label a successful observation.
4. Use GitHub job `concurrency` to prevent overlapping execution, but independently enforce one daily claim and no force-push. A push conflict or failed archive upload must be flagged `EVIDENCE_NOT_PERSISTED`; no valid session claim until evidence has been committed and independently verified.
5. Allowlist only public Deribit GET endpoints. Use repo-scoped GitHub token only for writing evidence, **not** an exchange key; permissions least privilege, no secrets printed, no new service/billing.
6. Preserve original raw bytes and all invalid attempts; second independent reader verifies manifest/raw SHA-256, metadata, ATM, expiry, UTC time, individual book/index distances, skew, cohort day uniqueness and valid-session cap.
7. Keep controlled diagnostics / historical replay / prospective observations in distinct namespaces and reports. Count **technical quote sessions** only. No fill assumptions, PnL or LIVE.
8. First stage: one paper dry-run of scheduling/storage with **fixtures only**, then controlled public diagnostic; only then freeze code SHA and begin forward attempts. A service that is triggered 5+ minutes late must fail closed and may generate missing days rather than fake data.

## Release gates
- Independent execution of all unit/integration tests in a Linux cloud runner on the **actual pinned commit**, not just previous Windows 66/66.
- Persistence conflict, interrupted uploads, repeated day and end-of-20 tests.
- Explicit scheduler and evidence branch activation review; ensure workflow additions do not alter unrelated jobs.
- Actual scheduled-run UTC start times measured over multiple dry runs, without assuming punctuality.
- Storage retention and archive accessibility via GitHub connector verified.
- Cost estimate $0 incremental verified under GitHub plan quotas before activating; otherwise ask first.

## Operational status
A user-facing authorization to prepare a cloud solution does not establish a working scheduled collection. Do not report GO until a scheduled invocation, durable evidence and independent audit have actually succeeded. Fee precedence for BTC_USDC daily delivery remains UNVERIFIED; `net_pnl=null`.

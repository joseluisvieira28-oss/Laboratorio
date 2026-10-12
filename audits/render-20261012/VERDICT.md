# Render / Laboratorio operational audit — 2026-10-12

Verdict: **ACTIVE_BUT_DEGRADED_SOURCE_BLOCKED / historical continuity review required**. No operational code repair is justified by current evidence. No deployment, configuration, plans, billing, accounts, orders, source history or scientific rules changed.

## Current proof (approximately 17:44–17:50 UTC)

- Canonical Render service `srv-dalqkpu1egvs73fhiehg`, free, unsuspended, autoDeploy=no; live deploy `dep-db542b5ckfvc738sul90`, commit `d645891a588c594b69f41938263cc4066652aa9b`. `/health` and `/api/state` return **503 DEGRADED_FAIL_CLOSED**, by intentional handler logic, while runtime produces fresh states and persists evidence. This is an application/source-integrity failure, not evidence that the HTTP process crashed.
- Frozen AVAXUSDT bookDepth **2026-10-08** ZIP HEAD and checksum GET both still return **404**. Prior independent census: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38057526064 . Remains SOURCE_BLOCKED, never NO_EDGE. No substitutions, interpolation, date skipping or false backfill performed.
- Canonical configured branch head independently checked by `git ls-remote`: `e5ce9f7290cae2dd1d42b4db6d7fbc146e9570f9`. GitHub unauthenticated rate limit 403 appears in runtime drift monitor; existing Atom fallback correctly identifies STALE_RUNTIME. Diff from deployed commit: 28 files, Windows operator scripts, QA workflows, receipts and source-only probe. **No differences in radar runtime or pyproject**. A redeploy would advance identity but would not fix this source hole or historic gaps. No redeploy warranted; no automatic drift deployment authority inferred from autoDeploy=no.
- Runtime gap history preserves **31 receipts**, `HISTORICAL_GAPS_REVIEW_REQUIRED`. Latest persisted heartbeat 17:45:15Z, prior 17:30:15Z, interval 900.007s, CONTINUOUS for that observed interval. This is not a 24/7 or full scientific continuity certificate.

## Persistence

- Supabase project `jqzdvgjeuveiktftyrlz` ACTIVE_HEALTHY. Independent read-only aggregate SQL at **17:46:15.233397 UTC**: radar_events **2778**, radar_event_keys **2700**. Both tables report RLS enabled. No payload/outcome queries executed.
- Runtime target SUPABASE_POOLER, watchdog PASS_CANONICAL_SUPABASE_SINGLE_WRITER, chain verified, max event/sequence=2778. Independent aggregate matches contemporaneous runtime identity. Full chain integrity is runtime-reported, not recomputed by this audit.
- Render PostgreSQL `dpg-dalqi4qd0e5s738a77kg-a` available/free, expires **2026-10-17T08:47:15Z**. Historical rollback-only after existing cutover; not canonical storage. Read-only MCP query blocked because external IP allowlist is empty. No allowlist relaxation or blind database URL rollback performed. Expiry threatens that rollback source, not demonstrated loss of active canonical Supabase evidence.

## Related services

Deploy receipts in related-deploys.json. Second bounded public health pass: Laboratorio, EMA6H source-equivalence, TradingView ingest, v09, v06 and v04 return HTTP 200. First cold pass timed out on several free canaries; second pass succeeded, so initial timeout alone is not classified as a defect. v07 `/health` returns 404: endpoint not proven supported; not a crash verdict. Older canary health is not canonical scientific authority. Laboratorio current deploy matches independently checked main `75fb36c8337c3221b7551c513e049cd472dad231`; current logs show public websocket PASS and completed source snapshot.

## Windows / Guardian

- Two live read-only Guardian inspections at **17:46:14Z** and **17:47:42Z**: same PID **3212**, one approved loopback listener, expected V0.14.4 build and registry 8/8, fresh forward state ages 6.3s and 4.7s. Updates continued during the 88-second observation window. Per-motor data coverage and unattended multi-day uptime not certified.
- **Guardian V0.8 task MISSING**. Legacy CryptoEdgeRadarV0144 enabled/Ready. Safe migration is prepared in existing installer but not executed: its documented operator gate requires review of PASS preflight and express acceptance of replacing the legacy task. This audit used only one-shot monitor mode, never Watch/EnableAutoRecover/Install. Local shadow remains separate from canonical Render/Supabase writer.
- Next concrete operational step: reviewed installer preflight, then explicit operator acceptance of legacy supervision migration; retain PID and logs. Historic October 8–11 local gap remains missing. No account/trading tasks changed.

## Validation and limits

Receipts: http-probes.json; render-log-operational-projection.json (bounded selected fields only); guardian-first.json; guardian-second.json; related-deploys.json. No economic verdict computed. Public source URL 200 is availability only, not archive validation. SQL connectivity of historical Render source remains unverified due allowlist restriction. Related service application health beyond sampled public endpoints is not certified. Operational evidence belongs to isolated branch; main and canonical configured branch remain unchanged.

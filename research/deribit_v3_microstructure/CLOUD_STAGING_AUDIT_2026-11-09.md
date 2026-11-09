# Cloud staging verification report — 2026-11-09

**CURRENT STATUS: CLOUD STAGING ONLY / AUTO-COLLECT NOT ACTIVATED / 0 OF 20 PROSPECTIVE SESSIONS / LIVE NO-GO.**

## Scope
Draft PR #343 stacked on V3 draft #341. Main, original V2 freeze, EPE and existing Render services unchanged. No new paid service, exchange credentials, private endpoints, orders or market calls initiated by this staging work.

## Verified
- At GitHub Actions run **42570000596**, job **129004936302**, on commit `39d38f0cd77b282a9162bb5eae22a2077fb6ba52`: 76 tests / 76 PASS on Ubuntu runner; runner log explicitly says `OFFLINE_STAGING_PASS; market_requests=0; forward_sessions=0`. The suite tested a *local bare Git remote*, not GitHub's persistent remote.
- The staging-only remote evidence branch `evidence/deribit-v3-staging-2026-11-09` was initialized from main, with no actual prospective observations. A synthetic receipt at `research/deribit_v3_microstructure/forward_evidence/dryrun/connector-write-read-2026-11-09.json` was committed via GitHub connector (`2efb581bd18a96a8649d0bd333122872fe5434ff`) and reread with exact same content and blob SHA `1834dd2cc3e4d81f59e1ba7dc830562c8846dc1a`. This verifies GitHub storage API write/read, **not** an Actions-scoped Git push.
- Staging code includes fail-closed UTC gate, synthetic dryrun mode, branch restrictions, prior manifest/raw hash verification, local Git non-force push and remote SHA check, and tests of concurrent push conflicts. The staging workflow does not contain schedule and never calls Deribit.

## Changes since that confirmed 76/76 run
- Cloud runner now restricts synthetic staging evidence branches to **dryrun only**, never `prospective`; adds fail-closed early wake-up and four hashed sources for successful receipts. New test written.
- A one-shot GitHub Actions job with `contents:write` has been declared, gated to exact trigger commit message `ci: trigger isolated persistence check`. Trigger commit `02fd4855b6b2ece2d2957bd275d7fd94a7741884` exists. **No successful runner-driven GitHub evidence push has yet been verified.** Do not label this gate PASS.
- The final post-change 77-test suite has not been independently confirmed as PASS. The earlier 76/76 PASS is valid only for its tested source SHA.

## Activation gates still closed
1. CI green on the **final reviewed SHA**, with logs/receipt, including tests of branch restrictions.
2. Real GitHub Actions dryrun Git push verified on staging-only evidence branch (not just connector write), plus SHA verification and restart/recovery.
3. Independent read-only audit of accepted prospective receipts: source identity, exact raw bytes, metadata, timestamps, expiry, and frozen eligibility. A stored `TECHNICAL_PASS` by itself is not independent certification.
4. Cost / entitlement review for any GitHub Actions usage and permission to write **only** the dedicated evidence branch; confirm evidence retention for >180 days. Do not use the unrelated Render disk or service.
5. Review the disabled schedule template `CLOUD_SCHEDULE_TEMPLATE_NOT_ACTIVE.yml.example`, replace pinned SHA, provision dedicated `evidence/deribit-v3-forward` branch, and obtain **separate explicit approval** to add a schedule to default branch. Schedule at 08:02 UTC is merely an attempt to begin early; a delayed or missed GitHub launch must fail closed.
6. Product-specific BTC_USDC daily expiry delivery fee remains UNVERIFIED: `net_pnl=null`; real trading permanently separate and NO-GO until independent economic proof.

**No scheduler was activated and no forward data counted.** The staging fixture has `prospective_v3=false`, `orders=0`, `net_pnl=null`, `market_requests=0`.

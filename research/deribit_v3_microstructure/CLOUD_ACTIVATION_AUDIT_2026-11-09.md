# Cloud V3: activation audit, 9 November 2026

**Staging tests PASS; production activation NO-GO; LIVE NO-GO. 0/20.**

## Live account and repository inspection

- PR #341 and #343 remain open drafts. PR #344 had ALREADY been merged by
  `joseluisvieira28-oss` at 07:52:36 UTC, before this operation, into main
  `1c786314da746e129aecc8c4ef403c2e2f3d385c`. Its description is stale.
  This operation did not merge anything or change main.
- Authenticated GitHub Settings showed **no repository or environment
  variables**. Therefore `DERIBIT_V3_FORWARD_ENABLED` and
  `DERIBIT_V3_FORWARD_APPROVED_SHA` are ABSENT, not false or approved.
  The installed job's two-variable guard keeps prospective capture OFF.
- Actions are allowed. Default token is contents/packages READ; automatic PR
  creation/approval is disabled. The quote job explicitly requests only
  `contents: write`. This is repository-wide contents access, not branch-scoped
  access. No exchange keys or private endpoints are involved.
- Default repository retention: 90 days. Artifacts alone cannot satisfy 180-day
  scientific retention. Primary evidence remains Git history with hashes.
- Initially no classic branch protection and no rulesets. During this operation,
  created ONE exact classic rule for `evidence/deribit-v3-forward`, blocking
  force-push and deletion for everyone including admins. No PR/status/lock
  requirement was added, so normal fast-forward evidence writes remain possible.
  This does not provide WORM or prevent an authorized user editing records in
  a new commit. No unrelated branch protection was changed.
- Production branch tip inspected: `72d47d2ff0b37a4f6c1e878dc460ffde209a58c7`;
  its evidence root contains only README, no prospective sessions.

## Cost inspection (account UI snapshot, not a future guarantee)

GitHub Free; November consumed usage $23.37, discounts $23.37, **billable $0**.
Compute $0/$12 included; Actions storage displayed **0 GB / 0.5 GB** (rounded).
Account Actions budget **$0, Usage blocked**; included-usage alerts ON.
No budget, plan, payment method or paid service was changed. Standard public
`ubuntu-24.04` runs are free; artifacts/logs have their own storage allowance.
An exhausted quota or $0 spending block may also block emergency upload.
Do not disable the spending block to recover data.

Official references:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/billing/reference/product-usage-included

## Implemented fixes (proposal, not production deployment)

Immutable source commit: `a16e13136db33a84191c25e5186fbbaa5da74058`.
Its tree `50fa7b0d6c3b8da1bcabfa4d70f6f448d87637e2` equals the locally tested tree.

1. Publish a daily reservation and verify remote SHA **before** calling public
   sources. Failed reservation push means ZERO source calls. A crash or failed
   final push leaves the remote reservation incomplete; later runs block until
   recovery. No resampling or fabricated replacement receipts.
2. Store `.gitattributes` with `* -text` inside the evidence root. A real local
   fresh-clone test exposed CRLF conversion altering raw hashes; the fix keeps
   Git from normalizing bytes. Long-path Git support is local to wrapper calls.
3. Audit reservations/completions independently. Audit missed-window-only
   archives instead of returning an early empty PASS.
4. `recovery.py` packs ONE UTC day, at most 64 MiB uncompressed. Restore requires
   independently retained bundle SHA256, rejects traversal/symlinks/duplicates,
   conflicting existing bytes, incorrect hashes and incomplete attempts, and
   audits a merged temporary copy before writing. Identical bytes are idempotent.
   The utility never pushes or counts an artifact as a retained session.
5. Proposed launcher packages failed/cancelled attempts and uploads the bounded
   bundle with seven-day retention, failing on missing files. SHA receipt goes
   to job logs. It pins source and third-party actions by immutable commit.

Hard runner termination can prevent packaging/upload. The durable reservation
still blocks later capture but cannot recreate lost raw bytes. Such a day stays
incomplete and requires explicit forensic reconciliation; never fabricate a
successful observation. Artifact availability is a separate gate from Git push.

## Executed verification

- Original pinned `08a1806`: 90/90 PASS locally (Python 3.12.10).
- Hardened source: 98/98 PASS locally with socket connections denied.
- Linux GitHub Actions run **42707830202**, job **129469236412**: **98/98 PASS**,
  Python runner, network blocked by suite; no real market requests, no orders.
  https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/42707830202
- Eight additional tests cover failed reservation push/no market, failed final
  push, fresh-runner blocking, restore/re-publish/fresh-clone independent audit,
  idempotence/bytes, wrong hash, conflicting bytes, traversal, missing receipt
  and missed-window-only contamination. All data synthetic and local bare Git.
- Earlier real GitHub fallback artifact **13657850178** remains accessible in
  API metadata: 261 bytes, non-expired, SHA256
  `04b20c8c2e081e146b3144d1387eea4a7cd787dc7c926e89f51bfa12bf4cc55c`,
  expires 9 December 07:46:37 UTC. This is an old synthetic fixture upload,
  not proof of restoring a market session with the new recovery utility.
- V2 tree unchanged: `ce05d2159823a0523b70c428e987910b09ac4214`.
  Economic engine tree unchanged: `019f938e48e5e73fe220907d99cc72388e3a967c`.
  Collector, adapter and PRE_REGISTRATION unchanged.
- Initial new recovery tests failed on CRLF conversion, then on Windows Git
  path length; both were corrected. Failed runs are not treated as passes.
- Local Git push was denied because its stored account is `sara67cs-ops`.
  Published isolated review branch through the authorized owner connector;
  no token was copied, exposed or added.

## Recovery procedure (before seven-day expiry)

1. Keep capture OFF. Retain run/attempt ID, source SHA and separately recorded
   bundle checksum. Download the recovery artifact through authenticated GitHub.
   Verify GitHub artifact digest separately from the inner `evidence.zip` digest.
2. Clone production evidence branch with full history. Use the immutable source
   above. Run `recovery.py restore --bundle <evidence.zip> --sha256 <inner SHA>
   --root <checkout>/research/deribit_v3_microstructure/forward_evidence`.
   Reject a conflict; preserve both copies for manual review. Do not delete claims.
3. Review exact additions, run independent archive audit, commit only evidence,
   fast-forward push, confirm remote SHA, clone again and repeat archive audit.
   Session remains uncounted until durable publication and independent audit.
4. Missing raw/receipt or interrupted restoration remains INCOMPLETE / NO-GO.
   No automatic source retries, backfill, force-push or claim removal.

## Pending activation gates

The installed main workflow still pins OLD source `08a1806`, so these fixes are
not active. Review the separate launcher-only proposal targeting main, verify
its final Linux CI, source/action pins and protected-branch write compatibility.
Do not merge the stacked research PR into main merely to install a launcher.

Run an authorized synthetic cloud bundle-download/restore/re-publish exercise
under the confirmed $0 budget before prospective activation. Existing evidence
demonstrates upload plus local restoration separately, not that complete cloud
round trip. Preserve logs/receipt outside expiring Actions retention.

Only after controls pass and release approval: install the revised launcher,
then set approved SHA to `a16e13136db33a84191c25e5186fbbaa5da74058`, with
`DERIBIT_V3_FORWARD_ENABLED=true` LAST. Neither variable was set here.
Schedule 08:02 UTC daily (09:02 Paris in November); observation [08:05,08:10) UTC.
Measure actual scheduled starts over multiple fixture cycles: GitHub can delay
or skip schedules. Late starts remain MISSED_WINDOW and never backfill.

Unresolved BTC_USDC daily delivery fees still block expiry economics;
`net_pnl=null`, LIVE NO-GO regardless of quote collection readiness.

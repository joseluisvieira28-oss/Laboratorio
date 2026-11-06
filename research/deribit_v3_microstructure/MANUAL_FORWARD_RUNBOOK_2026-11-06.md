# V3 forward — manual operator runbook (prepared 2026-11-06)

**State:** READY FOR OPERATOR'S MANUAL START ONLY. Not launched; V3 forward 0/20. This document is NOT a scheduler or permission to place trades. No orders, credentials, private endpoints, commissions or capital.

## Frozen time and venue
- Every prospective attempt must occur within **08:05:00–08:09:59 UTC** on the date of collection (09:05–09:09:59 Europe/Zurich during CET).
- Never backfill a missed day and never convert the 2026-11-06 09:05 UTC diagnostic into a prospective attempt.
- Record the exact Git commit, PRE_REGISTRATION.md SHA-256, collector.py SHA-256, Python version, OS, and the persistent output root used.
- Manual sessions require a continuously retained, **single** output root across all 20 sessions. Do not use temporary directories or independent clones/roots; that would undermine the one-claim-per-day and 20-cap controls.
- Choose the repository's V3 PR branch, inspect diff and run `research/deribit_v3_microstructure/run_checks.py` before the first session. Stop if tests fail or sources change.
- The CLI `collector.py --out ...` is **diagnostic-only**. It **does not** start a prospective session.

## Manual prospective execution (operator, at frozen window ONLY)
Example PowerShell from the repository root; replace the absolute path with a permanent dedicated directory, and replace `python` with the previously tested isolated interpreter:

```powershell
python -c "import sys; sys.path.insert(0, 'research/deribit_v3_microstructure'); import collector; a,r=collector.collect(r'C:\CryptoLab\deribit-v3-forward',mode='prospective'); print(a); print(r['status']); sys.exit(0 if r['valid_technical'] else 2)"
```

**This command has NOT been executed in preparing this runbook.** It uses the existing tested library entrypoint; no script, scheduler or workflow was created. The attempt is claimed before the API requests. Do not run twice to replace an invalid day. The collector refuses execution outside the window and retains invalid attempts, including incomplete claims requiring reconciliation. Verify exact production root and UTC clock before command.

## After each attempt
1. Confirm one new day claim and one attempt folder; retain all raw bytes, manifest and receipt, including rejections and transport errors.
2. Verify hashes from the actual saved source; check identity, expiry, UTC bounds, individual book/index distances, and leg skew. Compare against precommitted frozen rules.
3. Only count receipt `prospective_v3=true` with `valid_technical=true` after integrity review; independent audit remains desirable. A diagnostic is never one of the 20.
4. Keep `delivery_fee_status=UNVERIFIED`, `net_pnl=null`, `LIVE=NO-GO` while product-specific expiry fee remains unresolved; do not use the V2 weekday delivery shortcut as evidence.
5. Anchor evidence outside the mutable local root (retained checksums/immutable commit) without publishing private account data.
6. If UTC window, metadata, integrity, rate limit or API transport fails: record failure, do **not** retry the day's claimed prospective observation.

## Start decision
Technically qualified for **manual quote capture only** per integration audit 2026-11-06 (66/66 local tests reported, public controlled observation). This file does not initiate or guarantee any capture. Start needs an actively running, trusted operator-controlled Python environment in the exact daily window; otherwise 0/20 remains. Automatic/scheduled capture would be a separate infra change requiring explicit review and authorization. Economic PnL and live trading remain **NO-GO**.

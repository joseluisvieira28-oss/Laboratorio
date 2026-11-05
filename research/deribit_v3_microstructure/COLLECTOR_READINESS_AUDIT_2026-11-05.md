# Collector and test execution readiness audit — 2026-11-05

Scope: static inspection of `research/deribit_diamante_v2/probe.py` on V3 branch, and current V3 files. No Python execution or public API call was made in this review.

## Findings
1. Existing V2 `Source.get` is explicitly allowlisted to public endpoints, uses HTTPS, rejects redirects, sets timeout, limits response size, persists raw bytes, and records SHA-256, timestamps and errors. `collect(..., mode='entry')` checks 08:05–08:10 UTC; `assert_entry_times` verifies all six sources and decision timestamps. Preserve all of this.
2. V2 `parallel_books` concurrently requests both books and `synchronization` checks <=1000ms book skew and <=10s book-to-index distance. Its index-distance computation compares the **newest** book timestamp only; independent audit checks each book separately. V3 should retain the stronger per-book check; do not silently change V2.
3. V2 `payout` computes delivery fee conditional on `expiry.weekday()==4`, otherwise zero. This hardcoded weekday heuristic is **not authoritative product fee classification** and may be inconsistent with BTC_USDC linear daily documentation. Block net PnL until contract-specific fee schedule is verified. Do not rely on the zero-fee branch.
4. V2 `fee` models the taker formula using 0.0003*index capped at 12.5% option price, quantity .01. The metadata check hardcodes `taker_commission == .0003`; if terms change, fail closed and investigate rather than auto-accept.
5. V3 offline comparator currently replays three pinned archives and does NOT reconstruct entry fees separately, calculate actual hold-to-expiry cashflows, access live market data, or start prospective collection. This is intentional.
6. V3 unit tests are committed, but **not executed**. No GitHub Actions workflow runs were returned for commit `99661463c6877908bc8cf9d2f68dc66a8adcc106`. Do not claim PASS.

## Zero-cost execution instructions (local clone with Python 3.11+)
Run from repository root, using the V3 branch:
```sh
python -m unittest discover -s research/deribit_v3_microstructure -p 'test_*.py' -v
python research/economic_proof_v1/run_checks.py
python research/deribit_v3_microstructure/offline_compare.py --out /tmp/deribit-v3-offline-$(date -u +%Y%m%dT%H%M%SZ).json
```
Review output and preserve stdout, Python version, commit SHA, and hashes. The tests use existing pinned archives, no network is needed. If the first command fails, investigate before proceeding. The shell commands above have NOT been executed by this assistant.

## Collector go/no-go
Before any 20-session start: (a) tests actually PASS, (b) read-only V3 adapter tested with synthetic fixtures and a public-data-only controlled observation, (c) each raw response independently hashed and source timestamp verified, (d) no credentials/private calls/orders, (e) product-specific delivery fee ambiguity resolved or reported as unresolved blocking PnL, (f) explicit approval for any new scheduler/workflow/cost. No new workflow was created. V3 forward sessions: 0/20.

# CRYPTO LAB — THREE-WAY FORWARD VERDICT / OPERATIONAL CLOSEOUT
Date: 2026-10-13 | Branch: research/payoff-funding-aware-netstop-v01-2026-10-13

## Binary decision
**THREE_WAY_ENGINE_SYNTHETIC_PASS / FORWARD_SOURCE_NOT_YET_ELIGIBLE / EXECUTION_UNPROVEN / LIVE_NO_GO**

This is an **engineering / timing verdict**, NOT an economic forward result. Today is 2026-10-13: no bar on or after the chosen 2026-10-14 UTC boundary has closed. The strategy cannot receive valid future performance credit today.

## Exactly three untouched scientific tracks
1. **BTC-CONVEX Parent:** original V5 1h causal LONG signal and non-latched 12% trailing / 4% initial stop; same normalized 20% equity exposure comparator as PR #194. Original Parent V0.1/V0.2 separate forward authorities remain independent and unchanged.
2. **PAYOFF-40-10-BTC-001:** frozen +40% nominal margin target, -10% nominal margin stop, 60-day time exit, 10% equity initial margin at 2x; historic [PR #194](https://github.com/joseluisvieira28-oss/Laboratorio/pull/194) remains intact.
3. **PAYOFF-FUNDING-NETSTOP-001 child:** exact same 4R target and entry with *distinct* prospective adjusted stop, based on actual-to-date model funding and conservative fixed assumed 10bps fee/5bps adverse slip at exit. Its stop is recomputed after past funding but becomes active only on the **following 1h observation**. No historical path is allowed as child-promotion evidence.

All three simulated models are evaluated on the **same** input bars, marks and funding, with BASE and STRESS costs. Active positions and unrealized outcomes remain explicitly unsettled.

## New concrete deliverables
- `research/payoff_funding_netstop_001/net_risk_stop.py` pure cash-loss formula, no exchange action.
- `research/payoff_funding_netstop_001/forward_child_replay.py` forward-only deterministic sequential child portfolio simulator (cannot replay economic period before 2026-10-14 UTC), conservative same-bar stop-first, gap handling, monthly-equivalent funding event accounting at exact UTC hour, 60-day time expiry, explicit MTM loss/closure, no synthetic PnL for open trades. Validates source timeline, with marks for trading bars. **Not** a live order system.
- `research/payoff_funding_netstop_001/forward_three_way.py` common same-data paired Parent/4R/child comparison; source provenance, no-live authority, 200 wholly post-boundary hourly-bar warmup, manifest and funding attestation required before evaluation.
- `research/payoff_failure_execution_forward/forward_public_daily_source.py` only official checksum-verified post-2026-10-14 public market/mark daily archives and public funding history; checks 24h/day, source hashes and normalized funding timestamps. Hard bans pre-boundary economic outcomes.
- `research/payoff_funding_netstop_001/test_forward_three_way.py` synthetic sequence tests for funded child stop activating **next** hour, adverse gap, no funding at entry instant, target, no source leakage, no fabricated wins from open positions, strict authority.
- `research/payoff_failure_execution_forward/test_forward_public_daily_source.py` source checksum, coverage, wrong endpoints, funds and 200h warmup tests.

## Verified CI receipts
- [Original standalone NETSTOP math QA 38359438356](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38359438356): SUCCESS, 12 synthetic tests.
- [Forward daily public collector synthetic QA 38358778991](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38358778991): SUCCESS, nine tests.
- **[Three-way combined CI 38362996295](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38362996295): SUCCESS**, frozen 4R invariants PASS, pre-boundary and public-source QA PASS, new child synthetic path PASS, no-accounts/no-trading static guard PASS. Test results are code integrity only, not a price-derived performance receipt.

## First legitimate time boundary and operational blocker
- First permitted new price bar open: **2026-10-14 00:00 UTC**.
- Initial 200 complete consecutive NEW hourly bars from first boundary, no sealed pre-boundary 2026 warmup, no prefilling.
- Daily archive for UTC 2026-10-22 must first be available after the day closes; **first possible public daily-archive collector and 3-way replay: 2026-10-23 UTC**, subject to publication, public funding endpoint access, source SHA256, mark coverage and fully closed bar.
- A branch GitHub workflow with tests does not make the collector automatically scheduled. GitHub scheduled events run from the repository default branch; main merge is forbidden by operator authority. **No collector is currently deployed / running**, and no new forward economic result exists.
- No synthetic number or retrospective result is promoted to OOS. For this child, a fresh sequential forward sample and venue-specific account-independent execution feasibility receipts are required.

## Risks still open
- Source market is public Binance USD-M, NOT a live MEXC trade/quote; mark liquidation uses a heuristic and cannot substitute for exchange liquidation engine/account tiers.
- Bid/ask depth, taker fills, adverse stop gaps, min qty, lot/tick and exact position-level funding/commission receipts remain unknown. A stop at simulated -10% net **does not guarantee** real max loss.
- The child was motivated by already-known historical 2021 funding tail losses. It may close many positions early and underperform; **there is no new child economics result**.
- Parent and 4R historical +32.46%/+28.33% BASE equity figures are selected-period retrospective diagnostics only.

**Next operator action:** at or after 2026-10-23 UTC, verify official daily market and mark ZIP/CHECKSUM and public funding completeness for the freshly permitted dates, run `forward_public_daily_source.py` once and then `forward_three_way.py` on the verified source, or issue exact fail-closed source blocker. This requires a newly authorized runnable environment (or explicit user action), not a pretend scheduled GitHub branch job. Recheck economically at frozen future evidence checkpoints, not post-hoc chosen trade counts. No main merge or live orders.

# Diamond Structural — 20 Oct 2026, real source probe closeout

**Verdict: SOURCE_BLOCKED; 0/3 pairs economically assessable; NO EDGE PROVEN; NO LIVE GO.** This is a real-source negative access result, not an inferred failed strategy.

## Bound source verification
Frozen document: research/structural_edge/FUNDING_CHEAP_FALSIFIER_PRE_SOURCE_FREEZE_2026_10_20.md; frozen *before* the first source scan. No protected historic 2026 holdout touched.

Workflow #39384028506 completed SUCCESS at 2026-10-20 07:03:18 UTC. Job 118499522443. 12/12 source/economic invariant tests passed. Authentic public exchange GET results:

| Fixed pair | OKX funding HTTP | OKX BBO HTTP | Bybit ticker HTTP | Pair screen |
|---|---|---|---|---|
| BTC | OK with SHA receipt | OK with SHA receipt | 403 Forbidden | SOURCE_BLOCKED |
| ETH | OK with SHA receipt | OK with SHA receipt | 403 Forbidden | SOURCE_BLOCKED |
| SOL | OK with SHA receipt | OK with SHA receipt | 403 Forbidden | SOURCE_BLOCKED |

Started 07:03:16.796Z, finished 07:03:18.329Z. 0 authentic cross-venue fully valid comparison samples; 0 positive screens; 0 actual fills; account PnL NULL, never 0. Artifact ID 12246242578, artifact ZIP SHA256 12a5cf25825cbd8defad87940169b7266e616565ff813047d687d07299186b37. Source receipts include SHA256 for all six OKX public HTTP bodies. Full log https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39384028506.

**Crucial:** GitHub Actions SUCCESS refers to code completion and archived receipts. Bybit failed at the first required market ticker; script fail-closed, so cannot compute predicted funding benefit, fees or spread on a matched exchange pair. Do not interpret "positive_screen_count=0" as 0 real opportunities or NO_EDGE.

Bybit V5 official guide specifically states that US/mainland-China IP traffic receives HTTP 403. This GitHub-hosted runner's actual IP/geolocation has not been independently proven, so attribution remains an unverified plausible explanation. Do not bypass a legitimate geographic access restriction. Source: https://bybit-exchange.github.io/docs/v5/guide

## What this definitively does and does not establish
- **YES:** 3 authentic OKX public source funding+book snapshots collected with SHA custody. The programme ran offline synthetic tests and a live public GET-only source check.
- **YES:** This GitHub runner cannot access the Bybit ticker using the configured documented public endpoint at this time. Pairwise execution feasibility is not evaluable.
- **NO:** This is not economic NO_EDGE, not profitable and not a proof of executable carry.
- **NO:** No real cost-tier proof, settlement realized, close price, net PnL, hedge, notional feasibility or capital allocation.
- **NO:** Do not repurpose isolated single-venue funding into a delta-neutral arbitrage claim.

## Governance: stop test duplication
This source workflow initially had branch push/PR triggers and GitHub assigns run number 3 to the audited run; therefore **do not claim only one workflow invocation existed** without complete run census. All source attempts are informational, not independent scientific opportunities. Automatic triggers were removed in commit 744fc7fc3eef1ffe73d74d510bc3965f6c98f880. This closed probe is not an auto-run research campaign. No further Bybit retry; a separately frozen lawful-access collector would need fresh, explicit scope and independent source/fee justification.

Next useful commercial decision: stop dev work on this exact pair-source transport; focus the remaining Crypto Lab effort on mechanisms with a publicly accessible source and a clearly identifiable *net payer* before writing more code. For income, do not assume trading revenue.

Maintained boundaries: research only, no order, account, keys, wallet, money, Render, main merge, backtest parameter changes or opening protected historical holdout.

# OKX ONE-SNAPSHOT SPOT–PERP CARRY — REAL FROZEN ECONOMIC CLOSEOUT
2026-10-20 UTC, research-only. **FINAL: ALL 3 SOURCE-PASS; 0/3 8H HURDLE SURVIVORS. NO ECONOMIC PROMOTION.**

## Immutable original sequence
1. Before touching market data, freeze in `research/okx_carry_20261020/PRE_SOURCE_ECONOMIC_FREEZE.md`, commit `c62dd01d2ed01ae534a40fe1ec1a1b1bcd72351a`. Fixed BTC/ETH/SOL, OKX only, 8h settlement, USDT spot and linear SWAP, spot + perp BBO, min contract size, 30bps base / 60bps stress hypothetical four taker fills, no ROI prediction from multi-day constant funding.
2. Exact implementation and 14 hermetic tests frozen on branch before first market source, actions only triggered on PR-open; branch code ref `cd7aaff87dc85bc820ba5fbae037adf2958c633a`.
3. **Real [GitHub run 39386359969](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39386359969)** 2026-10-20 07:25 UTC: SUCCESS job 118507041594. **14/14 hermetic tests PASS; 15/15 genuine unsigned public OKX HTTP packet receipts OK; 3/3 matched source-complete valid 8h pairs; no accounts, fills, orders or real money**.
4. Original archived raw public response bodies and derived receipt in [artifact 12247027791](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39386359969/artifacts/12247027791), SHA256 of artifact ZIP `5de914f57074b38a4634ff7da23a12f79d01189d128d0e597b7a0cf64a63cd0f`; 15 per-HTTP source hashes separately in derived receipt.
5. Observation start 2026-10-20 07:25:07.504 UTC, end 07:25:10.019 UTC; data packet and fundingTime timestamp checks PASS; next settlement timestamp 1792483200000 ms (2026-10-20 08:00 UTC) for all three.

## ECONOMIC SCREENS — 8h funding RATE ESTIMATE, NOT ACTUAL FUTURE SETTLEMENT
All values in **basis points** (1 bp = 0.01% of matched notional). Frozen "fee" 30bps baseline, 60bps stress are hypothetical illustrative regular taker scenarios and NOT account-specific Swiss fee quotes.

| Pair | Next funding estimated gross | Static unchanged-book spread proxy | 8h base estimated after fees+spread | 8h stress estimated | If same rate for 24h (diagnostic) | If same rate for 7d (diagnostic) |
|---|---:|---:|---:|---:|---:|---:|
| BTC | +0.717536 | 0.024492 | **-29.306956** | -59.306956 | -27.871885 | -14.956242 |
| ETH | +0.540154 | 0.083493 | **-29.543339** | -59.543339 | -28.463031 | -18.740260 |
| SOL | +0.606916 | 1.913967 | **-31.307051** | -61.307051 | -30.093219 | -19.168726 |

Visible entry basis was **negative** on all pairs: BTC -5.5214 bps, ETH -4.0486 bps, SOL -8.6091 bps (perp bid minus spot ask relative to spot ask). This basis is not assumed to converge or booked as PnL. The book-spread sensitivity presumes unchanged future books, not evidenced actual exits.

Top-of-book minimal spot funding capital **lower bounds only** (not full collateral / executable hedge feasibility): BTC 8.1682 USDT, ETH 2.39589 USDT, SOL 1.0454 USDT. Tick/lot/size and real account eligibility, min order constraints, margin and liquidation protection remain unknown. These values are **not** proof the user can open a safe hedged position for these amounts.

## Quantitative necessary-condition consequence
The predicted rates correspond to **0.54–0.72 bps per 8-hour interval** versus a 30bps four-fill roundtrip cost before extra basis risk. Under the *unrealistic* diagnostic assumption of identical 21 funding payments at the observed rate and identical future books, ALL THREE still negative. This is robust reason not to build this precise currently-observed cash-carry micro-cycle into a bot. It is NOT a proof no future/cross-venue funding opportunities can ever exist.

## SCIENTIFIC CAVEATS
- Funding receipts public and predicted; actual paid rates can change, and the next payout occurred AFTER the observation. We did NOT inspect a realized later settlement for this exact snapshot.
- Negative estimates reflect the frozen **cost model**, not real account cashflows; actual PnL unknown and set to null.
- 30bps illustrative fees depend on real instrument/account/region; account-specific effective fees and Swiss availability NOT checked. Lower fee tiers could change feasibility, but do not retroactively rescue this one observed configuration. Source: https://www.okx.com/en-eu/help/trading-fee-rules-faq
- No liquidation, basis unwind, future exit, FX, hedge accuracy, actual slippage, funding receipt or risk sizing proof.
- Avoid 7d extrapolation as alpha; reported only because explicitly predeclared diagnostic.
- The original 2026 protected historical holdout and earlier V04 OKX linear/inverse outcomes remain sealed/unchanged.

## RESOURCE ALLOCATION VERDICT
**STOP building bots for this frozen 8h screen.** Keep the source adapter only as a proven public-data primitive. No live GO, no spend and no more point-in-time reruns to chase positive funding.

Given the repo alternatives, an independent *source-first* audit of BTC options VRP execution / statistical power (#163) is the only candidate with an empirically supported underlying risk-transfer premium (192 weekly history; ~74.5% positive IV–RV) AND extant public BBO route. However its current direct weekly test remains UNDERPOWERED (former planning estimate ~8600 effective weeks for a modest return differential) and has substantial short-option tail risk; allocation is conditional on a **pre-forward-data credible falsification/power redesign**, not on building an automated short-vol options trader. If no powered, capital-appropriate execution test exists, classify RESOURCE_NO_GO, leave trading research in low-maintenance mode. cbETH redemption accessibility and Pendle points provenance remain blocked, and direct Aave keeper free-source blocked. This is research routing, not alpha or promised earnings.

**CLOSED verdict: SOURCE PASS, COST SCREEN FAIL, MONEY MACHINE NOT DEMONSTRATED. ZERO STRATEGIES PROMOTED.**

# CRYPTO LAB — OPERAÇÃO CONVEX DIAMOND: CROSS-VENUE ECONOMIC ATTACK V0.1
Date 2026-10-17 UTC. Source: historical audits PR #215/#216/#217/#218 and real signal audit #241/#242. This is **NOT a market outcome**.

## Outcome of today's bounded attack

**REAL DELIVERY:** branch research/convex-crossvenue-cost-gate-2026-10-17 descended from source-gate research PR #216, preserving existing V5 source and original scientific freezes. New self-contained decimal reference fee scanner, 15 synthetic regression cases and branch-only CI job on Windows/Ubuntu, with public-source ledger and failure conditions. No main merge, Windows changes, API accounts, broker login, deposits, orders, live trading, holdout opening or external service deployment.

**COST FINDING, NOT NEW ALPHA:** Confirmed published MEXC Futures API 2026-06-01 base 6bps maker/8bps taker and its distinction from website/app promotions; Kraken Derivatives 2/5, OKX 2/5, Bybit Global 2/5.5, Bitget 2/6. Thus taker/taker is 16bps MEXC vs 10bps Kraken/OKX (6bps lower theoretical fee before venue factors). If SAME assumed 2bps slippage per side and no spread/funding, modeled hurdle MEXC 20bps vs Kraken/OKX 14bps. Not a gain to the 2023-25 V5 accounts and not a future trade expectancy estimate.

## Why lower execution fees do NOT equal portable model returns

- V5 reconstructed on Binance USD-M historical candle/funding sources and 1x 20%-equity notional; not a mechanical property of MEXC/Kraken/Bybit prices or stop executions.
- Equal-clock bid/ask and available depth in both directions are missing for Kraken and OKX; the 12 MEXC source snapshots from 13 Oct cannot substitute for time-matched signal entry or forced exit.
- Long-hold funding is material. Exact historical venue-specific funding / mark price absent; 1m Binance mark OPEN sensitivity is proxy, not MEXC/Kraken funding.
- Kraken geographic exclusion list does not enumerate Switzerland; **NOT sufficient** for actual Swiss account/product/contract/API eligibility. Confirm permission and fees without funding or placing orders.
- Historical original SOL1h 84 closes in 3y, BNB4h only 28. Need prospective outcomes, not forced statistical significance.
- SOL5m separate PR #217: 3y +59.99% BASE, 182 closed and more churn (PF 1.342 versus SOL1h 1.824) under the original model; never mix its performance with PR #215 timeframes as if identical evidence.
- V07/V11/V12 are signal-only Telegram observers, no broker-native stop. Nonlatched trailing reverts/weaken; original parent not safe for direct live 10x automatic port.
- Marker `NO_LIVE_GO` remains mandatory; reference fee comparison is not a credential, entitlement or authority.

## Required next independent tests (not yet carried out)

1. Auth-free public source checks for Kraken/OKX SOL and BNB instruments, tick/lot/min notional, public book and funding metadata, with timestamp and SHA receipts; do not fabricate snapshots if unavailable.
2. For new completed V5 closed-bar signals from existing 10-lane Windows outboxes, collect **only sanitized lane IDs, closes and receipt/coverage** using existing PR #242 scanner. No private DB sharing.
3. Introduce an explicitly pre-outcome frozen point-in-time multi-venue public quote witness with clock and causal source gates, only after operator approved local observer/deployment plan. A Binance signal and venue executable ASK/BID at +5m must be paired; if stale or missing, mark INVALID.
4. Net economic ledger from untouched future signal episodes, stress quote crossings, funding, spread, mark/execution, rejected orders and overlap. No maker-execution counterfactual without separate fill model.
5. Independently test prospective monotonic stop policy separately from original V5, include broker ACK + recovery under sandbox where verified available; synthetic PASS never equals venue-native real stop coverage.

## Decision / stop spending engineering cycles

PRIORITY 1: scientific candidate SOL1h / BNB4h; SOL5m also deserves separate observation despite greater churn.
PRIORITY 2: prove broker portability and real costs. Kraken is first cost/eligibility **research target**, not approved destination.
PARK: FAST-CONVEX 128 historically negative arms, SHORT-REJECTION 8/8 losses, and anything requiring hindsight tuning.
SCIENTIFIC VERDICT: **HISTORICAL CANDIDACY / COST IMPROVEMENT HYPOTHESIS / NO OOS CERTIFICATION / NO LIVE GO**.

Source references are preserved in research/convex_crossvenue_v01/PUBLIC_VENUE_COST_SOURCE_FREEZE_2026-10-17.md.

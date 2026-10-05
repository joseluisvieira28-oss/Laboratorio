# FUNDING-DISPERSION-DN-001 — PRE-OUTCOME FREEZE V0.1
Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES
Mode: research-only / no trading / no account reads / no private endpoints / no main merge

## Economic mechanism
Exploit persistent cross-exchange dispersion in realized perpetual funding for the same USDT-margined asset. At decision time t, use only funding observations already settled. If venue A's normalized funding exceeds venue B's by a threshold, the hypothetical next-interval portfolio is SHORT A / LONG B (reverse when B>A), notionally delta-neutral. The thesis is carry dispersion persistence, not directional price prediction.

## Source gate
Public unauthenticated historical funding endpoints only:
- Bybit V5 market funding history.
- OKX public funding-rate-history.
2026 is locked and MUST NOT be opened by this discovery run.

## Frozen discovery window
2024-01-01T00:00:00Z through 2025-12-31T23:59:59Z.

## Frozen universe
BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, LTC, BCH where a common USDT perpetual exists and both venues return valid observations.

## Causal construction
1. Convert every realized funding payment to bps/hour using the actual elapsed settlement interval on that venue.
2. Build only timestamps where both venues have a most-recent settled observation no older than 12h.
3. Signal at t = sign(Bybit_norm(t) - OKX_norm(t)); no future rate may enter signal formation.
4. Outcome = signed next realized normalized funding differential at the next eligible common observation.
5. Do not use 2026 data, predicted funding, account data, or post-outcome parameter tuning.

## Frozen thresholds / gates
Evaluate absolute lagged normalized dispersion thresholds: 0, 0.25, 0.50, 1.00 bps/hour. These are frozen as a grid, not selected after seeing outcomes.
For each threshold report N, mean/median next carry, win rate, PF-like positive/negative carry ratio, sign persistence, bootstrap 95% CI of mean, and asset concentration.

Promotion requires ALL:
- >= 300 eligible observations total;
- >= 5 assets with >= 30 observations each;
- pooled mean next carry > 0;
- bootstrap 95% CI lower bound > 0 for at least one pre-frozen nonzero threshold;
- >= 55% positive next carry at that same threshold;
- no single asset contributes > 40% of total positive carry;
- 2024 and 2025 both have positive mean at that threshold.

## Execution reality
Discovery is funding-only and cannot establish tradable net PnL. Even a statistical survivor remains RESEARCH_SURVIVOR_ONLY until a separate, pre-frozen execution layer includes both-leg entry/exit price divergence, spreads, slippage, trading fees, margin/liquidation risk, transfer/capital fragmentation, settlement timing and venue-specific funding mechanics.

Current retail fee reality is intentionally NOT subtracted in Stage A because positions are not yet modeled. Stage B, if authorized by this freeze through a Stage-A PASS, must use contemporaneous fee schedules and conservative taker stress; no fee rescue.

## Verdicts
SOURCE_BLOCKED / NO_EDGE / RESEARCH_SURVIVOR_ONLY.
No live trading authority can be created by this experiment.

# MEXC EVENT FUTURES LAB — ATTACK CLOSEOUT V0.1–V0.5

Date: 2026-10-02
Branch: `mexc-event-futures-crossasset-v0.5-2026-10-02`
Main: UNCHANGED
Live trading: NONE

## Scope attacked

Displayed Event Futures assets:
- BTCUSDT
- ETHUSDT
- NVDAUSDT
- MUUSDT
- SPCXUSDT

Event horizons:
- 10m
- 30m
- 1h
- 1d

Chart / information horizons:
- 5m
- 15m
- 1h
- 4h
- 1d where applicable
- cross-asset leader lookbacks 5m / 15m / 1h / 4h

## Source findings

Current public MEXC standard-futures index price and recent K-lines resolve for all five mapped underlyings.

Historical Min1 was not recoverable in the frozen historical probe.
Historical Min5 and coarser data were recoverable.

Clock audit identified that the Min5 K-line timestamp behaves as a bucket-start timestamp in the live control. Final proxy tests therefore map close availability to bucket-end time (+300 seconds).

## Scientific runs

### V0.3.1 — Simple continuation / reversal
Frozen cells: 200
Discovery passers: 0
OOS opened: 0
Verdict: NO_PROXY_SURVIVOR for this family.

### V0.4 — Technical chart-state families
Frozen cells: 800
Families:
EMA trend, RSI extreme reversal, Donchian breakout, Bollinger reversal, 3-bar streak continuation/reversal, ROC3 continuation, range-position reversal.

Basic discovery-eligible cells: 27
Benjamini-Hochberg FDR q=0.05 selected: 0
OOS opened: 0
Verdict: NO_PROXY_SURVIVOR for this family.

### V0.5 — Cross-asset lead/lag
Frozen cells: 640
Basic discovery-eligible cells: 7
Benjamini-Hochberg FDR q=0.05 selected: 0
OOS opened: 0
Verdict: NO_PROXY_SURVIVOR for this family.

## Aggregate

Scientifically usable frozen cells attacked:
200 + 800 + 640 = 1,640.

Robust discovery selections:
0.

August OOS remains unopened for these families because no frozen discovery candidate earned access.

September 2026 holdout remains LOCKED / NOT FETCHED.

## Product-level verdict

**No evidence yet that ordinary chart direction, common technical chart-state signals, or the tested cross-asset lead/lag rules can clear the 80%-payout reference hurdle robustly.**

This does NOT prove that MEXC Event Futures as a product has no exploitable structure.

Exact-product economics remain unresolved because:
1. payout is dynamic and historical payout-at-entry has not been recovered;
2. exact Event Futures settlement-index equivalence to the standard-futures index K-line proxy is not proven;
3. exact entry/expiry tick and rounding semantics are not reconstructed;
4. the public Event Futures guide states API trading is not supported.

## Next legitimate research directions

Priority A — exact-product observation:
prospectively record timestamp, asset, horizon, Up payout, Down payout, displayed index, expiry, settlement index, result and evidence reference. This attacks the missing payout/settlement layer rather than inventing it historically.

Priority B — calendar/session structure:
pre-freeze UTC session / US cash-session / weekday hypotheses and test them with multiplicity correction before opening OOS.

Priority C — event-conditioned signals:
macro releases, options/volatility shocks, liquidation/flow shocks, or other already-authorized Crypto Lab signals translated into an Event Futures directional horizon only after a clean pre-outcome mapping freeze.

No promotion.
No merge to main.
No live Event Futures order.

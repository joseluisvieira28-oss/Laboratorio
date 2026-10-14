# EARLY-PROFIT-HARVEST-001 — frozen preference / first offline technical receipt
Date UTC: 2026-10-14. Trading authority: NONE. Draft PR #223 on isolated branch; no merge to main.

## Operator intent
User explicitly selected realizing profits EARLY rather than solely trying to maximize big trend runs. The original candidate's positive expectancy is NOT conferred on this new exit management policy. Static/retrospective outcomes elsewhere must not be re-described as this child's forward.

## Freezes before economic market outcomes
- Immutable initial policy commit `c72ab51164998bc0d12552c25ee138f8f6d5cd63`: first eligible +1R favorable verified executable quote, proposed HALF (50%) position reduction, require projected closed net PnL >=+0.25R_cash including prorated entry fees/signed known funding, exit fees+slippage; if min contract/lot prevents half, **FULL** close fallback at same conditions.
- R_price is original entry-to-initial-stop price distance; R_cash is actual frozen full modeled stop dollar loss including conservative execution/funding reserve, NOT leveraged ROI. No time-to-profit claim or percentage bank increase promised.
- A partial fill must be independently confirmed and matching remaining broker stop coverage established BEFORE sending proposal to lift remaining protective stop to signed-funding/fee/slippage-aware net breakeven; round LONG up and SHORT down to protect the modeled breakeven, preserve strictly non-loosening previously acknowledged stop. If proposed stop is already crossed => fail closed, never claim a historical better fill.
- Neither model proposes authenticated exchange orders nor proves atomic stop replace/partial-fill reconciliation. Actual realized cash can be smaller than forecast, and surviving leg or full account can still lose from outage, gap, funding and slippage.

## Engineering evidence
- Pure Decimal hypothetical proposal functions: `research/operator_risk/early_profit_harvest.py`; no broker transport, credentials, app API or live exchange telemetry.
- 17 new synthetic tests cover LONG/SHORT +1R conditions, minimum net hurdle and signed funding, minimum contract fallback, price/lot/margin guards, bad source or broker stop ACK, stop tick rounding, no relaxation, quote already crossed, no fake filled state.
- Existing monotonic risk architecture carried 13 synthetic tests from earlier V0.1.
- [GitHub Actions QA 38576197766](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38576197766): SUCCESS **30/30** unit tests. Run tests pure synthetic data only; no backtest, future market event, venue fill or independent economic experiment was conducted.

## Economic/operational verdict
**OPERATOR_PREF_CONFIRMED / EARLY_PROFIT_POLICY_FROZEN / 30_SYNTHETIC_PASS / SOURCE_EXECUTION_UNVERIFIED / NO_LIVE_GO**.
The fact that 'profit in the pocket' motivates partial realized fills does not prove this exit policy maximizes expected net return: premature partial exits may destroy rare trend winners; stop-market orders are not hard loss guarantees. All existing original BTC-CONVEX/BNB/SOL/OPTIONS/LICP results remain untouched.
Next legitimate stage is forward shadow comparison of an original chosen entry signal versus the exact +1R/half child using truly prospective time-matched executable BBO and funding, with mock-lifecycle fault injections; separately verify broker partial-fill, stop resize and amend ACK via authorized risk-safe testing. If no fees/lot/depth/source access or no broker ACK proof, fail closed and keep all trading DISARMED.

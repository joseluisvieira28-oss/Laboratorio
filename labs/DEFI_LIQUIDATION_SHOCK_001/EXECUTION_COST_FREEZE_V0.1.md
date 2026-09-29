# DEFI-LIQUIDATION-SHOCK-001 — EXECUTION COST FREEZE V0.1

Date: 2026-09-29
Status: FROZEN / BEFORE 2025 PROTECTED OUTCOMES

## Intended live execution venue
MEXC SOL_USDT USDT-margined perpetual, automated API execution.

This freeze does not authorize any order.

## Public fee authority
MEXC announced API Futures trading fee changes effective 2026-06-01 08:00 UTC:
- API maker: 0.06%
- API taker: 0.08%
- API fee schedule takes precedence over website/app promotional rates for API trades.

V0.1 assumes market/taker entry and market/taker exit.

Known API fee round trip:
0.08% + 0.08% = 0.16% = 16 basis points.

## Primary cost hurdle
Primary all-in round-trip hurdle:
26 basis points = 0.26%.

Composition:
- 16 bps documented API taker fees;
- 10 bps fixed execution/funding stress reserve.

The 10 bps reserve is a deliberately predeclared conservative buffer, not an estimate fitted from holdout outcomes.

Primary economic classification uses c = 0.0026.

## Hard stress
Supportive hard-stress hurdle:
40 basis points = 0.40%.

This is reported but is not an additional PASS gate in V0.1.

## No fee rescue
After 2025 outcomes open:
- no lower fee assumption;
- no maker-fill substitution;
- no VIP/rebate/promotion assumption;
- no reduction of the 10 bps reserve;
- no selective exclusion of costly trades.

If live account-specific API fees are later higher than this freeze, live activation is blocked until the strategy is revalidated prospectively under the higher cost, without reusing protected outcomes for tuning.

## Funding
No historical funding optimization is permitted.
The fixed 10 bps reserve is the V0.1 allowance for slippage, spread, latency and occasional funding impact across a 5-minute hold.

## Firewall
protected_2025_outcomes_opened=false
protected_2026_outcomes_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
post_outcome_tuning=false
merge_main=false

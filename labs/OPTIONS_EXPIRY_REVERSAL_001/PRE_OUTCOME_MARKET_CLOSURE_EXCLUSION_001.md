# OPTIONS-EXPIRY-REVERSAL-001 — PRE-OUTCOME MARKET CLOSURE EXCLUSION 001

Status: FROZEN BEFORE ANY OUTCOME METRIC WAS COMPUTED

## Trigger

Discovery run 34900018454 and pre-outcome remediated continuation run 34900340495 both terminated during BTC price acquisition before r_pre, r_post, OLS, bootstrap, trade returns, PnL, or promotion gates were computed.

Both official Binance Vision monthly and daily BTCUSDT Spot 1m kline archives contain none of the four required exact minute opens for 2021-09-29: 07:30, 08:00, 08:01, 08:31 UTC.

## Independent exchange-closure evidence

Official Binance notice:
https://www.binance.com/en/support/announcement/detail/e2f674fc961d48af9b28edd82896607c

The notice states that a scheduled system upgrade started 2021-09-29 07:00 UTC, estimated duration approximately 2 hours, and Spot and Margin Trading were suspended during the upgrade.

Therefore the frozen execution window 07:30–08:31 UTC was inside an official Binance Spot trading suspension. There was no executable Binance Spot BTCUSDT 1m open at the required timestamps.

## Frozen rule

Date 2021-09-29 is classified NON_EVALUABLE_MARKET_CLOSED and excluded from outcome construction.

This is an operational feasibility exclusion, not an outcome filter.

Rules:
- exclude exactly 2021-09-29 from the protected Discovery rows before any return is computed;
- do not substitute another exchange, futures/perpetual data, interpolation, nearest-minute price, or synthetic price;
- do not alter any other protected date;
- keep signal definition, 07:30/08:00/08:01/08:31 timestamps, regression, bootstrap, costs, and promotion gates unchanged;
- expected protected evaluable rows after this closure exclusion: 1339;
- 2025 and 2026 remain locked;
- no live trading, exchange mutation, or post-outcome tuning.

## Governance

This exclusion is frozen only because both prior attempts failed before any outcome metric existed. It must not be changed after any r_pre/r_post, regression coefficient, bootstrap p-value, strategy return, PnL, or promotion gate is observed.

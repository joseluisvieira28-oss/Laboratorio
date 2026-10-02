# MEXC EVENT FUTURES LAB — PRE-OUTCOME FREEZE V0.1

Date: 2026-10-02
Status: RESEARCH-ONLY / FAIL-CLOSED
Branch: `mexc-event-futures-lab-v0.1-2026-10-02`

## Objective

Test whether simple, pre-specified directional signals derived from MEXC index-price history can predict the sign of the price move over MEXC Event Futures horizons strongly enough to overcome the fixed-return payout structure.

This lab MUST NOT place orders, mutate an exchange account, use live capital, or claim an exact Event Futures edge unless the Event Futures settlement index and historical payout-at-entry can be evidenced.

## Product facts frozen before outcome analysis

Official MEXC documentation states:

- Event Futures are Up/Down contracts.
- Supported expiry choices documented for the current product are 10 minutes, 30 minutes, 1 hour, and 1 day.
- A correct prediction earns `principal × payout` profit; an incorrect prediction loses the principal; a tie returns principal.
- The payout is dynamic, depends on volatility / market risk, and is fixed for a trade at submission time.
- Settlement is determined from the underlying asset's index price at expiry.
- Event Futures do not currently support API trading.
- Minimum order amount is currently documented as 1 USDT.
- Positions cannot be closed before expiry.

Operator screenshot on 2026-10-02 showed the current Event Futures selector containing:
`BTCUSDT`, `ETHUSDT`, `NVDAUSDT`, `MUUSDT`, `SPCXUSDT`.
This screenshot is observational evidence only; MEXC may change the list without notice.

## Exact-vs-proxy boundary

The official public contract API exposes standard futures index-price history, including:
`/api/v1/contract/kline/index_price/{symbol}`.

This lab may use that series only as an **INDEX-PRICE PROXY**.

It is NOT yet proven that:
1. the standard-futures index series is byte-for-byte identical to the Event Futures entry/settlement index;
2. historical Event Futures payout-at-entry values are recoverable;
3. Event Futures contract-specific timestamps / rounding are recoverable.

Therefore:
- source availability for standard index history can PASS;
- directional proxy tests can run;
- an exact economic backtest remains BLOCKED until equivalence + payout history are proven;
- no proxy result may be promoted directly to live Event Futures.

## Frozen asset mapping for the public MEXC contract API

| Event display | Proxy contract symbol |
|---|---|
| BTCUSDT | BTC_USDT |
| ETHUSDT | ETH_USDT |
| NVDAUSDT | NVIDIA_USDT |
| MUUSDT | MUSTOCK_USDT |
| SPCXUSDT | SPCXSTOCK_USDT |

If a mapping does not resolve, mark that asset SOURCE_BLOCKED. Do not substitute another symbol after viewing outcomes.

## Frozen horizons and chart lookbacks

Event horizons:
- 10m
- 30m
- 60m
- 1440m (1d)

Chart lookbacks:
- 1m
- 5m
- 15m
- 60m (1h)
- 240m (4h)
- 1440m (1d)

Two fixed signal families:
- CONTINUATION: sign of trailing return over the chart lookback predicts the same sign over the event horizon.
- REVERSAL: sign of trailing return over the chart lookback predicts the opposite sign over the event horizon.

No RSI / MACD / ML / threshold optimization is allowed in V0.1. This deliberately keeps the first attack simple and falsifiable.

## Entry clock

For a horizon H, evaluate only UTC timestamps aligned to H minutes since Unix epoch.
This avoids cherry-picking arbitrary entry seconds and reduces overlapping-event inflation.

## Frozen historical partitions

Development / discovery:
- 2026-04-01 00:00 UTC through 2026-07-31 23:59 UTC

Retrospective OOS:
- 2026-08-01 00:00 UTC through 2026-08-31 23:59 UTC

Locked historical holdout:
- 2026-09-01 00:00 UTC through 2026-09-30 23:59 UTC
- MUST NOT be fetched or evaluated by V0.1.

Prospective shadow boundary:
- >= 2026-10-02 after freeze commit
- not part of the historical V0.1 verdict.

## Economic math

For payout `q`, unit expected value is:

`EV = win_rate × q - loss_rate`

with ties contributing 0.

With no ties, break-even accuracy is:

`1 / (1 + q)`

Examples:
- payout 70% => 58.8235%
- payout 75% => 57.1429%
- payout 80% => 55.5556%
- payout 85% => 54.0541%
- payout 90% => 52.6316%

The 80% displayed in the operator screenshot is a current observation, NOT a historical constant.

## V0.1 statistical gate

For each asset × horizon × lookback × signal-family cell:

Discovery:
- minimum non-tie observations: 200 for 10m; 150 for 30m; 100 for 60m; 60 for 1d;
- Wilson 95% lower bound of directional accuracy must exceed the 80%-payout break-even accuracy (55.5556%);
- EV at 80% payout must be > 0;
- the same signal direction must remain above 50% in each of three chronological discovery thirds.

Only cells passing all discovery conditions are opened in August OOS.

OOS:
- no threshold or rule changes;
- Wilson 95% lower bound must exceed 55.5556%;
- EV at 80% payout must be > 0;
- otherwise the cell fails.

Because many cells are tested, any survivor remains a CANDIDATE only. No "diamond" status from V0.1.

## Required outputs

1. Source probe JSON.
2. Proxy matrix JSON and CSV.
3. Explicit list of discovery passers.
4. Explicit OOS result for only those passers.
5. Exact-product blocker list.
6. Holdout remains unopened.

## Hard prohibitions

- No live trading.
- No Event Futures order submission.
- No authenticated account mutation.
- No post-outcome retuning in V0.1.
- No changing symbol mappings after results.
- No opening September holdout in V0.1.
- No treating an 80% screenshot payout as a historical constant.
- No claim of exact Event Futures profitability from proxy data.

# STABLECOIN-EXCHANGE-FLOW-001 — FINAL PRE-DISCOVERY PROTOCOL V0.1

STATUS: **FROZEN BEFORE BTC OUTCOME ACCESS**

LAB: `STABLECOIN-EXCHANGE-FLOW-001`  
MVE: `SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`

## 1. Scientific question

Does a point-in-time-defendable increase in the aggregate USDT balance of the frozen Binance public Ethereum address basket predict a positive subsequent BTC return?

This is not total stablecoin supply, not all-exchange flow, not DEX peg stress, and not a current reconstructed exchange-label series.

## 2. Frozen entity universe

The only entity addresses are the nine Ethereum addresses from the Binance public transparency disclosure first published on 2022-11-10 and already frozen in `SOURCE_REMEDIATION_001_BINANCE_PUBLIC_BASKET.md`.

No address may be added, removed, relabelled or substituted after BTC outcomes are opened.

USDT Ethereum contract:

`0xdac17f958d2ee523a2206206994597c13d831ec7`

USDT decimals: `6`.

## 3. Frozen source measurement

For each UTC day `t`, define `B_t` as the sum of `balanceOf(address)` for all nine frozen addresses at the final Ethereum block whose timestamp is `<= 23:59:59 UTC` on day `t`.

The source signal is:

`net_flow_t = B_t - B_(t-1)`

This state-delta measurement is authorized because an outcome-blind reconciliation gate proved on protected 2022 and 2024 block windows that:

`change in total basket USDT balance == inbound Transfer value - outbound Transfer value`

exactly in raw USDT units, and independent archive providers returned the same historical states.

Primary source provider: `https://eth.drpc.org`.

Independent QA provider: `https://rpc.mevblocker.io`.

The raw Transfer/dump route remains a fallback for audit only; it may not be used to redefine the signal after outcomes.

## 4. Point-in-time and date boundaries

Baseline balance snapshot: end of `2022-11-11` UTC.

First eligible signal day: `2022-11-12` UTC.

Last eligible signal day: `2024-12-29` UTC.

Reason for the final date: the frozen 1-hour outcome for a 2024-12-29 source signal is fully contained in 2024. No 2025 market or source data is required.

2025 and 2026 are forbidden in Discovery.

## 5. Information-safe timing

A daily signal is not actionable until the source day is complete and Ethereum state has had an explicit finality/publication safety buffer.

For signal day `t`:

- source day ends at `23:59:59 UTC`;
- fixed safety buffer: `15 minutes`;
- entry timestamp: `00:15:00 UTC` on day `t+1`;
- exit timestamp: `01:15:00 UTC` on day `t+1`.

No same-day pre-close price is part of the signal.

## 6. Frozen BTC outcome source

Instrument: `BTCUSDT` Binance USD-M perpetual futures.

Granularity: official Binance 1-minute historical klines.

Entry price: open of the 1-minute candle timestamped exactly `00:15:00 UTC` on `t+1`.

Exit price: open of the 1-minute candle timestamped exactly `01:15:00 UTC` on `t+1`.

Gross return:

`r_t = exit_price / entry_price - 1`

No 2025 or 2026 candle may be requested.

## 7. Frozen primary statistical hypothesis

Only one primary predictive hypothesis is authorized:

`H1: beta > 0`

in the regression:

`r_t = alpha + beta * (net_flow_t / 1,000,000,000 USDT) + epsilon_t`

Dividing by one billion only changes units; it is not a fitted normalization.

Primary inference:

- OLS beta estimate;
- one-sided moving-block bootstrap p-value for `beta <= 0`;
- block length: `7 daily observations`;
- bootstrap replications: `20,000`;
- deterministic RNG seed: `20260914`;
- significance threshold: `0.05`.

No alternate lag, horizon, nonlinear transform, threshold, z-score, percentile, winsorization, interaction, regime or ML model is authorized inside this MVE.

## 8. Frozen companion economic sanity test

Direction:

- `net_flow_t > 0` -> LONG BTC for the frozen 1-hour window;
- `net_flow_t < 0` -> SHORT BTC for the frozen 1-hour window;
- `net_flow_t = 0` -> no position.

Gross signed return:

`strategy_gross_t = sign(net_flow_t) * r_t`

Cost views:

- `NET10`: gross minus `10 bps` round-trip;
- `NET14`: gross minus `14 bps` round-trip stress.

Funding is zero for this geometry because the frozen position is opened at 00:15 UTC and closed at 01:15 UTC and therefore does not cross the standard 00:00 UTC funding timestamp.

The statistical regression is primary. The companion strategy cannot rescue a failed primary beta test.

## 9. Promotion gate

MVE0 may be promoted to a separately frozen validation protocol only if **all** conditions hold:

1. source/data integrity gate passes with no 2025/2026 access;
2. `beta > 0`;
3. one-sided 7-day moving-block bootstrap `p < 0.05`;
4. mean `NET10 > 0`;
5. mean `NET14 > 0`;
6. profit factor at `NET14 > 1.0`;
7. at least two calendar partitions among 2022-partial / 2023 / 2024 have non-negative mean `NET14`, and neither full calendar year 2023 nor 2024 may be deeply negative (`< -10 bps/trade` mean NET14).

Failure of the primary beta test closes this exact MVE as `NO_STATISTICAL_EDGE` if data/integrity passed. Negative economic expectancy is classified separately when applicable.

No threshold may be weakened after outcomes.

## 10. Full source-data QA required before BTC access

The daily source dataset must pass all of the following before any BTC candle is fetched:

- exact UTC boundary block rule implemented deterministically;
- no requested block timestamp after 2024-12-29 23:59:59 UTC;
- no 2025/2026 source access;
- all nine balances available on every boundary;
- no duplicate/missing UTC boundary dates;
- balance totals stored in integer raw USDT units and decimal USDT;
- net-flow arithmetic reproducible from adjacent balances;
- exact second-provider reconciliation on a prospectively fixed QA subset: every first calendar day of each month in the dataset plus the first baseline and final boundary;
- any second-provider mismatch is fail-closed `DATA_FAILURE` until explained without opening BTC outcomes.

## 11. Hard governance

- research-only;
- fail-closed;
- no live trading;
- no exchange mutation;
- no live orders;
- no merge to main;
- no deployment;
- no 2025/2026 access;
- no post-outcome tuning;
- no cherry-picking;
- no rescue by changing horizon, threshold, address basket, source semantics, costs or statistical test;
- blocked/technical/data failures remain distinct from scientific no-edge.

## 12. Authorized next sequence

1. Build and independently QA the protected daily source dataset only.
2. Freeze hashes/receipt for the source dataset.
3. Only after source-data PASS, acquire the frozen 2022-11-13 through 2024-12-30 00:15/01:15 BTCUSDT outcome candles required by this protocol, without touching 2025/2026.
4. Run the one-shot frozen Discovery.
5. Emit a closeout or promotion artifact without tuning.

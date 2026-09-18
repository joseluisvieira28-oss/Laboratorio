# ETH-STAKING-FLOW-001 / ESF-NETQUEUE-XATU-7D-003 — FINAL PRE-DISCOVERY PROTOCOL V0.1

Date: 2026-09-18
Branch: `eth-staking-flow-v0.3-discovery`
Status: **FROZEN BEFORE FIRST MARKET OUTCOME ACCESS / ONE-SHOT DISCOVERY AUTHORIZED**

## Authorization and lineage

Parent source MVE: `ESF-NETQUEUE-XATU-7D-003`.

Canonical source reconstruction:
- GitHub Actions run: `35384444641`
- artifact: `ETH_STAKING_FLOW_001_XATU_FULL_QUEUE_V0_3D`
- artifact id: `10563431502`
- artifact ZIP digest: `sha256:73ab4209f268198c170f3b5a378abe184ae57796ec383b9008c2badccea7e98b`
- classification: `SOURCE_DATA_PASS`
- exact dates: 630/630, 2023-04-12 through 2024-12-31
- missing dates: 0
- daily series SHA-256: `95d225db9c4924852dfbca6333122fc78199092f0cdfd7a0995f4b5530cb2544`

The user explicitly authorized an aggressive continuation of the research campaign on 2026-09-18. Under the standing laboratory governance this authorizes this one-shot historical Discovery only. It does not authorize live trading, capital, wallets, exchange mutation, authenticated trading APIs, alerts/webhooks, 2025/2026 outcomes or merge to main.

## Frozen economic hypothesis

A large positive ETH validator net-entry queue-pressure state represents stronger marginal demand to lock ETH than demand to exit and is expected to precede positive ETH return.

Single predictor only:

`net_queue_count_t = pending_queued_count_t - active_exiting_count_t`

No secondary queue statistic, balance field, staking yield, funding, BTC filter, volatility filter or market regime is allowed.

## Frozen signal

For each source date `t`:

1. Require exactly 90 **prior** daily source observations; the current observation is excluded from the threshold window.
2. Compute the 80th percentile of `net_queue_count` across the immediately preceding 90 observations using linear interpolation on the sorted 90-value sample.
3. Signal iff `net_queue_count_t >= q80_prior90`.
4. Direction: **LONG ETH** only.

Signal scanning begins only once 90 prior observations exist.

## Frozen non-overlap rule

A signal at date `t` enters at the next UTC daily open, `t+1`, and exits at the UTC daily open exactly 7 calendar days after entry, `t+8`.

While that position is open, later source signals are ignored. Because signals are observed at 00:00 UTC and the prior position closes at its exit 00:00 UTC, the next eligible signal date is the prior exit date itself or later.

Operationally, after accepting a signal at `t`, the next source date eligible for another signal is `t+8`.

No pyramiding or overlapping positions.

## Frozen market instrument and source

Instrument: **Binance Spot ETHUSDT**.

Market source: official Binance Data Vision monthly 1d kline ZIP archives plus matching provider `.CHECKSUM` sidecars.

Protected-safe price archive window:
- 2023-07 through 2024-12 only.
- No URL containing 2025 or 2026 may be requested.

Required market field:
- daily open price only.

Open/close/high/low/volume fields other than the required UTC date/open value may not be used in the signal or performance rule.

Every downloaded ZIP must match the provider SHA-256 from its `.CHECKSUM` sidecar.

## Protected-period boundary

2025 and 2026 remain closed.

A signal is admissible only if both its entry and exit daily opens occur on or before 2024-12-31.

Therefore the last possible signal date is prospectively fixed at **2024-12-23**.

No event may be shortened, dropped after seeing its return, or rolled into 2025.

## Frozen return and cost model

For every admitted long event:

`gross_return = exit_open / entry_open - 1`

BASE:
`NET10 = gross_return - 0.0010`

STRESS:
`NET20 = gross_return - 0.0020`

Costs are fixed round-trip deductions.

No funding, leverage, stop, target, trailing exit, intraday execution, limit-order assumption or slippage rescue.

## Frozen primary statistics

Primary economic series: chronological event-level `NET10`.

Report:
- resolved event count;
- mean NET10;
- median NET10;
- win rate NET10;
- profit factor NET10 = sum(positive NET10) / abs(sum(negative NET10));
- mean NET20 and PF NET20 as fragility diagnostics;
- 2023 and 2024 event counts and mean NET10;
- stationary-bootstrap one-sided probability `p(mean NET10 <= 0)`.

No Sharpe optimization, parameter sweep or alternative horizon is authorized.

## Frozen stationary bootstrap

Chronological NET10 event sequence only.

- repetitions: 10,000;
- seed: `730031`;
- stationary restart probability: `0.25`;
- expected block length: 4 events;
- circular index continuation;
- one-sided p-value: `(1 + count(bootstrap_mean <= 0)) / (10000 + 1)`;
- bootstrap 95% percentile interval may be reported as a diagnostic but is not an additional promotion gate.

## Frozen promotion gates

All required:

1. source/provenance/leakage PASS;
2. >=30 resolved non-overlapping events;
3. mean NET10 > 0;
4. PF NET10 > 1.0;
5. one-sided stationary-bootstrap p(mean NET10 <= 0) <= 0.10;
6. 2023 mean NET10 >= 0 if 2023 contains >=5 events;
7. 2024 mean NET10 >= 0 if 2024 contains >=5 events.

NET20 cannot rescue a BASE failure.

If event count <30, terminal classification is `DISCOVERY_INSUFFICIENT_SAMPLE`.

If sample is sufficient but any other required gate fails, classification is `DISCOVERY_FAIL_NO_PROMOTION`.

Only if every gate passes may the result be `DISCOVERY_PASS_TO_INDEPENDENT_VALIDATION`.

A Discovery pass is not Tier 1, not Tier 2, not a Quase Diamante and does not authorize 2025 or live trading. Any independent validation/OOS requires a new frozen authority after this result.

## No-rescue rule

After market outcomes are opened, do not change:
- percentile;
- lookback;
- inclusion of current t in the threshold window;
- direction;
- instrument;
- entry/exit clock;
- holding period;
- overlap rule;
- costs;
- bootstrap settings;
- annual gate;
- source window;
- asset.

No subgroup, queue-sign inversion, BTC alternative or year selection is permitted.

## Safety

Research-only / fail-closed.
No live trading.
No exchange mutation.
No orders.
No wallets.
No authenticated exchange account/API.
No alerts/webhooks.
No 2025/2026.
No merge to main.

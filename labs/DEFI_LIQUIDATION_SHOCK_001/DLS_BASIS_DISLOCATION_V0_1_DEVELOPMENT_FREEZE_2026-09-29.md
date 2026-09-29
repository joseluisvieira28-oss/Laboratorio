# DEFI-LIQUIDATION-SHOCK-001 — BASIS DISLOCATION V0.1 DEVELOPMENT FREEZE

Date: 2026-09-29
Branch: dls-basis-dislocation-v01
Family ID: DLS-BASIS-DISLOCATION-001
Status: FROZEN BEFORE BASIS OUTCOMES ARE OPENED

## Scientific independence

This is a new economic family.

It is NOT:
- a rescue of DLS V0.2 executable volatility;
- a continuation/reversal rescue of DLS Signed Return V0.1;
- a signed BUY/SELL strategy.

The hypothesis concerns temporary relative-value dislocation between perpetual futures and spot after a
source-authorized DeFi liquidation shock.

No signed-flow label is used.

## Parent event authority

Canonical cluster source:
- run: 36465385517
- artifact: dls-source-cluster-sample-gate-v01
- artifact ID: 10988887983
- digest: sha256:7703f53869df186d20cf5c339327a1df2ee3f433c7ff0f8e6a02e1b9d053d97c
- receipt classification required: SOURCE_SAMPLE_GATE_PASS
- canonical cluster file: SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson

Admit only canonical clusters with:
- primary_market_identity = mint:So11111111111111111111111111111111111111112
- split = discovery
- t0 in the frozen development window below

All admitted protocols/classes remain in the population.
No protocol may be selected or removed from market outcomes.

## Economic hypothesis

A DeFi liquidation shock can create a temporary imbalance between SOL perpetual futures and SOL spot.

If the next tradable minute's perp/spot log basis is abnormally positive relative to the 60 complete
minutes immediately before entry, the perp is treated as relatively expensive and a market-neutral
convergence trade is opened:
- SHORT SOLUSDT perpetual
- LONG SOLUSDT spot

If the basis is abnormally negative:
- LONG SOLUSDT perpetual
- SHORT SOLUSDT spot

This is relative-value convergence. It does not require or use liquidation direction.

## Market data

Venue:
Binance public historical data archive.

Legs:
- Binance Spot SOLUSDT, 1-minute klines
- Binance USDT-M Futures SOLUSDT, 1-minute klines

Source:
data.binance.vision daily ZIP archives plus published CHECKSUM files.

Every downloaded archive must:
- return HTTP 200;
- expose a parseable 64-hex checksum;
- match SHA256 exactly;
- contain exactly one CSV member;
- contain monotonic unique UTC 1-minute timestamps inside the expected UTC day.

Any hard integrity failure:
DLS_BASIS_DEVELOPMENT_SOURCE_BLOCKED

## Development window

Event t0:
2021-12-08T00:00:00Z <= t0 < 2023-01-01T00:00:00Z

This uses only the already-open V0.1 discovery event split.

2023 basis outcomes remain closed unless development SURVIVES.
2024 basis outcomes remain closed unless 2023 OOS passes.
2025 and 2026 remain protected.

## Entry timestamp

For cluster t0:

A = floor_to_UTC_minute(t0) + 1 minute

This guarantees entry is not before the source-defined shock confirmation time.

Entry prices use the OPEN of both synchronized 1-minute bars at A.

If either leg is missing at A, fail closed for that cluster.

## Pre-event basis normalization

For exactly the 60 complete synchronized minutes:
A-60m, ..., A-1m

define:

b_t = ln(perp_open_t / spot_open_t)

mu = arithmetic mean of the 60 b_t observations
sigma = population standard deviation of the 60 b_t observations

Require:
- all 60 synchronized observations present;
- all prices > 0;
- sigma > 0 and finite.

Then:

z_A = (b_A - mu) / sigma

where b_A uses the synchronized OPEN prices at A.

No post-entry price is used to construct z_A.

## Frozen trigger

Threshold:
|z_A| >= 2.0

If z_A >= +2.0:
SHORT_PERP_LONG_SPOT

If z_A <= -2.0:
LONG_PERP_SHORT_SPOT

Otherwise:
NO_TRADE

There is no threshold grid.

## Position / collision rule

One market-neutral pair maximum.

Holding horizon:
15 minutes.

Exit timestamp:
X = A + 15 minutes

Exit prices:
OPEN of synchronized 1-minute bars at X.

While a pair is open:
- later clusters are ignored;
- no pyramiding;
- no reversal;
- no TP/SL;
- no discretionary exit.

If [A, X] touches a standard Binance funding timestamp at 00:00, 08:00 or 16:00 UTC:
exclude that candidate instead of modeling funding.

## Cost model

Equal gross notional on both legs.
Portfolio return is measured on total gross capital, therefore each leg has weight 0.5.

Spot:
- modeled taker fee = 10 bps per side
- adverse slippage = 5 bps per side

USDT-M Futures:
- modeled taker fee = 8 bps per side
- adverse slippage = 5 bps per side

Modeled nominal round-trip portfolio cost:
0.5 * [2*(10+5) + 2*(8+5)] = 28 bps

No lower-cost sensitivity is authorized for selection or rescue.

Execution price convention:

LONG leg:
- effective entry = open_A * (1 + slippage)
- effective exit = open_X * (1 - slippage)

SHORT leg:
- effective entry = open_A * (1 - slippage)
- effective exit = open_X * (1 + slippage)

Each leg also pays its own frozen taker fee on entry and exit.

Portfolio net return:
0.5 * spot_leg_net + 0.5 * futures_leg_net

## Development temporal folds

F1:
2021-12-08T00:00:00Z <= A < 2022-07-01T00:00:00Z

F2:
2022-07-01T00:00:00Z <= A < 2023-01-01T00:00:00Z

## Development gate

All conditions must pass:

1. total analyzable trades >= 100
2. overall mean net return > 0
3. overall median net return > 0
4. overall profit factor > 1.05
5. F1 analyzable trades >= 30
6. F2 analyzable trades >= 30
7. F1 mean net return > 0
8. F2 mean net return > 0
9. UTC-day block-bootstrap 95% CI lower bound for overall mean net return > 0

Bootstrap:
- resampling unit = UTC entry day
- replicates = 10,000
- RNG seed = 260930
- percentile interval = [2.5%, 97.5%]

PASS:
DLS_BASIS_DEVELOPMENT_SURVIVES

FAIL:
DLS_BASIS_DEVELOPMENT_NO_EDGE

SOURCE FAILURE:
DLS_BASIS_DEVELOPMENT_SOURCE_BLOCKED

A NO_EDGE result is terminal for this exact family and MUST NOT open 2023 OOS.

## Pre-frozen OOS boundary

If and only if development SURVIVES:

2023 OOS:
2023-01-01T00:00:00Z <= t0 < 2024-01-01T00:00:00Z

Exact same:
- event filter
- basis definition
- 60-minute normalization
- z=2.0 trigger
- side mapping
- entry latency
- 15-minute horizon
- collision rule
- funding exclusion
- fees/slippage
- adjudication metric definitions

No reselection.

## Pre-frozen holdout boundary

If and only if 2023 OOS passes under a separately frozen OOS gate:

2024 holdout:
2024-01-01T00:00:00Z <= t0 < 2025-01-01T00:00:00Z

No 2024 basis outcome may be opened before OOS PASS.

## Anti-rescue firewall

After this freeze it is forbidden to rescue this family by:
- changing z=2.0;
- adding a threshold grid;
- changing 60-minute normalization;
- changing 15-minute horizon;
- changing fees/slippage;
- switching to only one protocol;
- selecting clusters by event count after seeing PnL;
- adding amount/magnitude filters;
- changing collision handling;
- changing the convergence mapping;
- opening 2023 after development NO_EDGE;
- opening 2024 before OOS PASS.

Any materially different economic hypothesis requires a new family ID and new pre-outcome freeze.

## Operational firewall

signed_flow_used=false
market_2023_oos_opened=false
market_2024_holdout_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

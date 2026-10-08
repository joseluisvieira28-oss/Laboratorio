# PREMIUM-BASIS-PERP-TRANSFER-001 — PRE-OUTCOME FREEZE V0.1

Date: 2026-10-08
Status: FROZEN PROSPECTIVE TRANSFER / PUBLIC SHADOW ONLY

## Purpose

Test an economically distinct, automatable transfer of the already-frozen Premium Basis PRIMARY signal
to the standard MEXC `MUSTOCK_USDT` perpetual.

This study does NOT reinterpret, rescue, or replace the Event Futures V1.2/V1.4 results.
No historical perpetual outcome is opened under this transfer study.

## Parent signal — unchanged

Signal source and construction are inherited exactly from Premium Basis V1.4 PRIMARY:
- symbol: MUSTOCK_USDT
- public MEXC index Min5
- public MEXC fair-price Min5
- fair/index premium in bps
- trailing 24h z-score
- max 288 completed Min5 observations
- minimum 240 observations
- sample standard deviation
- PRIMARY only: 10m horizon, |z| >= 1.0
- z > 0 => LONG transfer
- z < 0 => SHORT transfer

Diagnostic V1.4 siblings are excluded and cannot rescue this study.

## Prospective boundary

The exact commit timestamp that first creates THIS freeze is the no-backfill boundary.
Only signals whose model entry timestamp is strictly later than that timestamp are eligible.

No prior October signal, V1.2/V1.3 holdout row, or V1.4 directional outcome may be reused as a
perpetual execution outcome.

## Public execution shadow

Venue/instrument:
- MEXC USDT-M Perpetual
- MUSTOCK_USDT

Entry for each eligible first-seen signal:
- first fresh public order-book snapshot captured after the signal is causally detected;
- LONG entry = best ask;
- SHORT entry = best bid.

Exit:
- first fresh public order-book snapshot captured at or after exactly 10 minutes from the entry snapshot;
- LONG exit = best bid;
- SHORT exit = best ask.

Freshness:
- public depth response timestamp must be <=5 seconds old at local receipt;
- crossed/empty books fail closed;
- no interpolation or later backfill.

Shadow observations may overlap. This is an execution-transfer measurement, not a capital/netting model.

## Returns and costs

LONG gross bps:
`10000 * (exit_bid / entry_ask - 1)`

SHORT gross bps:
`10000 * (entry_bid / exit_ask - 1)`

Frozen API fee model:
- maker/taker design is NOT searched;
- PRIMARY execution assumption = taker entry + taker exit;
- current official API taker fee = 8 bps per side;
- fixed fee hurdle = 16 bps round trip.

`net_bps = gross_bps - 16`

Observed BBO spread is already embedded in entry/exit prices.
No funding adjustment is applied to a 10-minute hold in V0.1; any funding-boundary overlap is
recorded and the event is excluded from the primary transfer sample rather than modeled after outcomes.

## Initial source/transport gate

Before economic accumulation can be trusted:
- public index Min5 source available;
- public fair-price Min5 source available;
- public MUSTOCK_USDT depth source available;
- exact source timestamps parse;
- best bid/ask finite, positive, non-crossed;
- at least 20 healthy depth snapshots over >=10 minutes;
- zero authenticated calls/orders/mutations.

## Economic readiness gate

No transfer verdict before:
- >=200 resolved eligible PRIMARY observations;
- >=14 distinct calendar days represented;
- missing/invalid entry-or-exit rate <=5%.

`PERP_TRANSFER_SURVIVES` requires ALL:
- mean net_bps > 0;
- median net_bps > 0;
- positive-net rate > 50%;
- day-block bootstrap 95% lower bound of mean net_bps > 0;
- at least 8 distinct UTC dates have positive daily mean net_bps.

If sample gate is met and any survival condition fails:
`PERP_TRANSFER_NO_EDGE`.

Before sample gate:
`PERP_TRANSFER_INSUFFICIENT`.

No alternate horizon, threshold, sign, asset, maker rescue, fee reduction, subperiod or outlier deletion
may rescue V0.1 after the first eligible transfer outcome is opened.

## Governance

Public unauthenticated read-only data only.
No order.
No API key.
No account/balance.
No wallet/capital.
No exchange mutation.
No live trading.
No main merge.

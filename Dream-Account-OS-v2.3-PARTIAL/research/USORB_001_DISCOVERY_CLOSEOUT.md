# USORB-001 — DISCOVERY CLOSEOUT / TOMBSTONE

Date: 2026-09-23
LAB_ID: `USORB-001`
Family: U.S. cash-open session / opening-range breakout
Primary family: TREND
Secondary family: MICRO
Governance: `CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN`

## Frozen question

On regular U.S. cash-market trading days, does the first confirmed 5-minute close outside the crypto range formed during 09:30–09:45 America/New_York predict same-direction continuation over the next 60 minutes after realistic round-trip costs?

## Canonical execution

Discovery only: 2022-01-01 through 2023-12-31.
Source: Binance Data Vision USD-M Futures monthly 5m klines.
Universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT.
Clock: America/New_York, DST-aware.
Opening range: 09:30, 09:35, 09:40 5m bars.
Signal window: 09:45–11:25 ET.
Signal: first close strictly outside OR high/low.
Entry: next 5m open.
Exit: close after 12 held 5m bars.
Costs: 10 bps base / 14 bps stress.
Source bundle SHA256: `a2b15380cc5cf6e71750db8a9af07abd2086df5dbd183cf96406d51b2746cc70`.

Protected periods opened: NONE.
Live execution: FALSE.
Merge to main: FALSE.

## Discovery result

Trades: **2,853**
Mean gross: **-0.398004 bps/trade**
Mean NET10: **-10.398004 bps/trade**
Mean NET14: **-14.398004 bps/trade**
Profit factor NET10: **0.757426**
Date-cluster bootstrap 95% NET10: **[-17.866052, -2.880501]**
Median opening-range width: **71.343639 bps**

Per-symbol NET10 means:
- BTCUSDT: -7.788895 bps (N=476)
- ETHUSDT: -5.556503 bps (N=475)
- SOLUSDT: -2.880526 bps (N=479)
- BNBUSDT: -14.354687 bps (N=481)
- XRPUSDT: -10.656718 bps (N=472)
- DOGEUSDT: -21.285755 bps (N=470)

Positive symbols: **0 / 6**.

Per-year NET10:
- 2022: -13.687076 bps (N=1,413)
- 2023: -7.170601 bps (N=1,440)

Positive years: **0 / 2**.

## Frozen classification

Scientific verdict: **NO_EDGE**
Operational lifecycle: **CLOSED_EXACT**
Mechanism state: **FALSIFIED_EXACT**

The exact continuation implementation is economically negative even before costs and remains negative across every tested symbol and both Discovery calendar years. The clustered confidence interval is wholly below zero after the frozen base cost.

## Forbidden rescues

Do not:
- invert the failed continuation result into a reversal under this LAB_ID;
- select SOL because it was least negative;
- alter 15m opening range duration;
- alter 09:45–11:30 signal window;
- change the 60m horizon;
- add EMA/VWAP/volume/ATR filters;
- isolate weekdays/months;
- reduce costs;
- open 2024, 2025 or 2026;
- relabel this exact experiment as unresolved.

## Successor boundary

The broader U.S.-session institutional-flow mechanism is not declared dead by this exact ORB failure. External literature can motivate materially new prospective questions, but a successor must use a new LAB_ID and a different causal contract, not a parameterized ORB rescue.

Examples of potentially material novelty include direct U.S.-session flow/ETF/benchmark observables or a prospectively frozen volatility-only mechanism. They receive zero inherited promotion credit from USORB-001.

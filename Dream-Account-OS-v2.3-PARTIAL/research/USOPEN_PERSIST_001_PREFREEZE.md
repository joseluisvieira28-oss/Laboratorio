# USOPEN-PERSIST-001 — U.S. CASH OPEN VOLATILITY PERSISTENCE — 2025 OOS PRE-FREEZE

Date frozen: 2026-09-24
Parent observation: `USOPEN-VOL-002 / USOV-POSTETF-2024-001`
Status: PRE_OOS_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Production impact: NONE
Live execution: FALSE

## Why this is a new lab

USOPEN-VOL-002 failed its exact 2024 replication because OPEN/POST did not clear the frozen gate, while OPEN/PRE remained near 2x across 6/6 symbols.

That outcome generated a new hypothesis: elevated realized variance may persist into 10:00–10:30 ET rather than being confined to 09:30–10:00.

Because this hypothesis was generated after seeing 2024, **2024 is contaminated for validation** and earns no promotion credit for this lab.

The first scientific test of the persistence hypothesis is therefore **2025 OOS only**.

## Frozen hypothesis

On regular U.S. cash-market trading days in 2025:

1. The 09:30–10:00 ET OPEN window remains elevated versus 09:00–09:30 ET PRE.
2. The 10:00–10:30 ET PERSIST window also remains materially elevated versus the same PRE window.

The persistence hypothesis survives only if both the opening anchor and the persistence window pass their frozen gates.

This MVE is non-directional. No PnL is computed.

## Frozen windows

- PRE: 09:00–09:30 ET
- OPEN: 09:30–10:00 ET
- PERSIST: 10:00–10:30 ET

Each window contains exactly six completed 5-minute bars.

Realized variance:
`sum(log(close_t / close_{t-1})^2)`

Universe:
BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT
on Binance USD-M Futures public monthly 5m archive.

## 2025 OOS gate

Minimum:
- 1,400 eligible symbol-days.

OPEN/PRE anchor:
- pooled median ratio >= 1.20;
- date-cluster bootstrap lower 95% > 1.05.

PERSIST/PRE primary:
- pooled median ratio >= 1.20;
- date-cluster bootstrap lower 95% > 1.05;
- at least 4/6 symbols have median PERSIST/PRE > 1.10.

If all pass:
`OOS_2025_PERSISTENCE_SURVIVES`

Otherwise:
`OOS_2025_PERSISTENCE_FAILS` or `INSUFFICIENT_SAMPLE`.

## Diagnostics only

Report, but do not gate:
- PERSIST/OPEN pooled median and bootstrap;
- per-symbol OPEN/PRE and PERSIST/PRE;
- volume PERSIST/PRE;
- descriptive 10:30–11:00 ET DECAY/PRE ratio.

The 10:30–11:00 window is **diagnostic only** and cannot rescue or promote the MVE.

## Source calendar

Use regular NYSE weekdays and exclude full-day closures, including the January 9, 2025 National Day of Mourning closure.

## Firewall

Forbidden:
- using 2024 for validation;
- opening 2026;
- changing window boundaries;
- changing thresholds after outcome access;
- selecting winners/assets;
- excluding macro days post hoc;
- directional return or PnL testing;
- adding ETF-flow/VWAP/volume filters;
- live trading;
- exchange mutation;
- merge to main.

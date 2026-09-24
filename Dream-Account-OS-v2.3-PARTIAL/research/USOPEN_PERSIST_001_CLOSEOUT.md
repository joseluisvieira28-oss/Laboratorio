# USOPEN-PERSIST-001 — 2025 OOS CLOSEOUT

Date: 2026-09-24  
Branch: `us-open-persistence-2025-v0.1`  
GitHub Actions run: `35956007393`  
Scientific verdict: **OOS_2025_PERSISTENCE_SURVIVES**  
Maturity: **M5 OOS/HOLDOUT — MECHANISM SURVIVES, NOT YET A TRADING EDGE**

## Frozen hypothesis

The 10:00–10:30 ET realized-variance window remains materially elevated relative to the 09:00–09:30 ET pre-open window on regular U.S. cash-market trading days in 2025, while the 09:30–10:00 ET opening window remains elevated as an anchor.

## OOS result

Sample:
- 250 eligible U.S. trading dates;
- 1,500 symbol-days;
- Binance USD-M Futures public 5m data;
- BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT.

Opening anchor:
- pooled median OPEN/PRE = **2.987932x**;
- date-cluster bootstrap 95% = **[2.646774, 3.382690]**.

Primary persistence:
- pooled median PERSIST/PRE = **2.582755x**;
- date-cluster bootstrap 95% = **[2.289480, 2.951848]**;
- 6/6 symbols have median PERSIST/PRE > 1.10.

Retention diagnostic:
- pooled median PERSIST/OPEN = **0.813823x**;
- bootstrap 95% = **[0.720210, 0.911288]**.

Per-symbol PERSIST/PRE:
- BTCUSDT 3.871587x
- ETHUSDT 3.142377x
- XRPUSDT 2.401510x
- DOGEUSDT 2.317478x
- BNBUSDT 2.281309x
- SOLUSDT 2.144248x

All frozen gates pass.

## Diagnostic-only observation

The pre-specified diagnostic 10:30–11:00 ET DECAY/PRE pooled median is **1.910276x**.

This value was not a gate and earns **zero promotion credit**. It may motivate a separate successor hypothesis, but must not be retroactively incorporated into USOPEN-PERSIST-001.

## Interpretation

The 2025 OOS result supports a durable intraday volatility regime around the U.S. cash open: elevated realized variance is not confined to 09:30–10:00 ET and remains strongly elevated during 10:00–10:30 ET.

This is a second-moment timing mechanism, not a directional return edge. No PnL was computed.

The result does not prove ETF causality. It is consistent with a New-York-clock institutional activity mechanism, but causality requires separate identification.

## Governance

- 2024 was hypothesis-generating and contributed no validation credit.
- 2025 was the one-shot untouched OOS for this lab.
- 2026 remains sealed.
- No directional PnL.
- No live trading.
- No exchange mutation.
- No merge to main.

Any monetization layer must be a new prospectively frozen lab. Any test of 10:30–11:00 persistence must also use a new LAB_ID and cannot claim the 2025 diagnostic as validation.

## Provenance

Source bundle SHA256:
`2871ccc7f0496f3fa206c2891a615dbf31cff311eec8624ccd40122bf0291478`

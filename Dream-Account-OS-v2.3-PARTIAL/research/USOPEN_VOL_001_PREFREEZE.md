# USOPEN-VOL-001 — U.S. CASH OPEN VOLATILITY SHOCK — PRE-FREEZE

Date frozen: 2026-09-23
MVE: `USOV-PREETF-001`
Status: PRE_DISCOVERY_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Production impact: NONE
Live execution: FALSE

## Scientific question

Before U.S. spot Bitcoin ETFs existed, did the 09:30 America/New_York U.S. equity core open already coincide with a reproducible, cross-asset crypto volatility shock relative to immediately adjacent 30-minute windows?

This MVE is deliberately **non-directional** and computes **no PnL**.

## Economic mechanism

The NYSE core open is a fixed external market-structure clock. Orders accumulated before the open are crossed in the 09:30 ET Core Open Auction and U.S. cash-session price discovery begins. If cross-asset institutional information/liquidity demand spills into continuously traded crypto, realized variance should rise specifically in the first 30 minutes after 09:30 ET.

NYSE authority confirms:
- 09:30 ET Core Open Auction;
- 09:30–16:00 ET Core Trading Session.

## Literature boundary

Recent 2026 research reports a first-30-minute Bitcoin volatility spike around U.S. ETF trading and a New-York-clock intraday pattern after ETF launch. Those papers are mechanism motivation only.

This exact MVE does **not** test the post-ETF regime because 2024/2025/2026 remain sealed. It asks only whether a comparable pre-ETF 2022–2023 U.S.-open volatility shock already existed.

Therefore:
- failure of USOV-PREETF-001 does not falsify a post-2024 ETF-specific mechanism;
- success does not prove ETF causality;
- no post-ETF inference may be imported into the 2022–2023 verdict.

## Anti-duplication

Nearest existing lineage:
- CRYPTO-INTRAWEEK-RV-001 / CIRV-HAR-DOW-BTCETH-001: one-day-ahead daily realized-variance forecasting using HAR + target-day weekday structure.

Material distinction:
- CIRV target = next UTC day's realized variance;
- USOV target = 30-minute intraday realized variance localized to an exogenous 09:30 ET event clock;
- CIRV uses rolling HAR forecasts;
- USOV uses same-day adjacent-window matched controls;
- USOV contains no directional return, PnL, options execution, leverage sizing, or weekday optimization.

USORB-001 is also distinct:
- USORB tested directional continuation after a 15-minute opening range and is CLOSED NO_EDGE;
- USOV tests only second-moment concentration at the market-open clock;
- USOV cannot inherit or rescue USORB directional outcomes.

## Frozen windows

For each regular U.S. cash-market trading day:
- PRE: 09:00–09:30 ET
- OPEN: 09:30–10:00 ET
- POST: 10:00–10:30 ET

Each window contains exactly six completed 5-minute bars.

Realized variance:
`sum(log(close_t / close_{t-1})^2)`

Primary contrasts:
- OPEN / PRE
- OPEN / POST

## Firewall

Allowed:
- public/free Binance source acquisition;
- source QA;
- 2022–2023 Discovery;
- immutable receipt;
- terminal closeout if frozen gates fail.

Forbidden:
- opening 2024, 2025 or 2026;
- directional returns or PnL;
- selecting only BTC after outcomes;
- changing 30-minute windows;
- shifting 09:30 clock;
- dropping POST or PRE control after seeing results;
- excluding macro days after outcomes;
- selecting weekdays/months;
- changing variance estimator after outcomes;
- merge to main;
- live trading;
- exchange mutation.

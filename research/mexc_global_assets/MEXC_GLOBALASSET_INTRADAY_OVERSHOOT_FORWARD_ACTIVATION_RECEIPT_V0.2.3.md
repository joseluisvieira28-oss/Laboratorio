# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — FORWARD ACTIVATION RECEIPT V0.2.3

Date: 2026-10-05
Status: PROSPECTIVE CAPTURE ACTIVATED — SCIENCE UNCHANGED

## Governing authority

This receipt does not amend scientific rules.

Authorities remain:
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_FREEZE_V1.0.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.1.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.2.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.3.md`

Historical state remains `ROBUST_API_FEE_SURVIVOR`.
Prospective execution state remains `EXECUTION_SHADOW_UNDERPOWERED` until the frozen evidence gate is met.

## First activated prospective segment

Trigger commit:
`90a4b7ebbc4a0b430fb79c6afa5db154b66a709b`

Workflow:
`MEXC Overshoot Shadow Capture V0.2.3`

Run:
`37312427508`

Trigger:
- UTC date: 2026-10-05
- start closed timestamp: 13:35 UTC
- end closed timestamp: 16:35 UTC
- segment: `segA_1335_1635`

At activation the workflow run was in progress and had successfully completed checkout, Python setup, dependency installation and trigger parsing; the capture step was active.

## Segmentation boundary

To respect GitHub-hosted runner duration constraints while preserving every frozen scan timestamp:

- segment A: 13:35–16:35 UTC inclusive
- segment B: 16:36–19:55 UTC inclusive

Together these cover exactly the frozen scan timestamp range 13:35–19:55 UTC with no scientific gap or overlap.

The existing final aggregator remains responsible for:
- deterministic cross-segment merge,
- frozen 10 minute global cooldown,
- duplicate/conflict checks,
- daily basket aggregation,
- notional-specific execution verdicts.

## Immutable scientific parameters

Unchanged:
- 35-asset frozen universe
- MEXC / Binance / Bitget identities
- 5 minute lookback
- Binance/Bitget dispersion <=10 bps
- abs MEXC 5m move >=40 bps
- abs MEXC excess >=35 bps
- same-sign rule
- FADE_MEXC_EXCESS
- +5 minute exit
- 10 minute global cooldown
- notionals 10/25/50/100 USDT
- primary 16 bps round-trip fees
- >=30 admitted prospective event baskets
- >=5 distinct session dates
- all PASS/FAIL/BLOCKED criteria

No orders, private endpoints, account reads, wallets, exchange mutation, live trading, main merge, retrospective backfill or post-outcome tuning are authorized.

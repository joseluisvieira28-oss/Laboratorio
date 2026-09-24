# WBTC-BTC-PEG-REVERSION-001 — PRE-SOURCE / PRE-DISCOVERY FREEZE

Date frozen: 2026-09-24
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Primary family: MR
Secondary family: RV
Research only: TRUE
Live execution: FALSE

## Economic mechanism

WBTC is designed as a BTC-backed wrapped asset with 1:1 backing and merchant/custodian mint-burn redemption machinery.

A sufficiently large secondary-market discount of WBTC versus BTC can therefore have a direct convergence anchor that is economically distinct from generic technical mean reversion.

This lab tests only the **discount side**. It does not infer a symmetric short-WBTC premium trade.

## Frozen data source

Binance Data Vision public Spot monthly klines:
- symbol: `WBTCBTC`
- interval: `1h`

Source gate checks archive availability only and must not parse price rows.

Discovery:
- 2022-01-01 through 2023-12-31

Protected OOS:
- 2024-01-01 through 2024-12-31

2025 and 2026:
- SEALED

## Frozen signal

A signal occurs when a completed 1h `WBTCBTC` bar:
- closes at or below **0.995 BTC per WBTC**;
- the previous completed bar closed above 0.995;
- signal bar trade count >= 3;
- signal bar quote volume >= 0.05 BTC.

This is a threshold-crossing episode rule, not a repeated every-bar signal.

## Frozen hypothetical implementation

After a signal:
- enter long WBTC / pay BTC at the **next 1h bar open**;
- require entry bar trade count >=3 and quote volume >=0.05 BTC;
- hold exactly 24 completed hourly bars;
- exit at the close of the 24th bar;
- require exit bar trade count >=3 and quote volume >=0.05 BTC;
- no overlapping positions.

Base research hurdle:
- subtract 20 bps round-trip from gross return.

Stress:
- subtract 30 bps round-trip from gross return.

These are conservative research hurdles, not a claim that exact historical fills or fee tiers are reconstructed.

## Frozen Discovery gate

Minimum:
- >=30 completed non-overlapping episodes total;
- >=8 completed episodes in each calendar year 2022 and 2023.

Survival requires all:
1. mean base-net return > 0;
2. iid episode bootstrap 95% lower bound of mean base-net > 0;
3. base profit factor >= 1.20;
4. one-sided exact sign-test p < 0.05 for base-net > 0;
5. mean base-net > 0 in 2022;
6. mean base-net > 0 in 2023;
7. mean stress-net > 0;
8. stress PF > 1.00;
9. largest positive episode <=25% of total positive PnL.

PASS:
`DISCOVERY_MECHANISM_SURVIVES`

FAIL:
`DISCOVERY_NO_EDGE`

If sample gate fails:
`DISCOVERY_INSUFFICIENT_SAMPLE`

## OOS firewall

Only if Discovery survives exactly as frozen may 2024 be opened under a separately committed OOS trigger.

No threshold change, no premium-side inversion, no 4h/12h/48h rescue, no volume-filter tuning, no fee reduction, no alternative venue, no synthetic cross-rate, no 2025/2026.

## Diagnostics only

- gross return;
- 4h, 12h and 48h markout from the entry price;
- entry discount;
- per-year counts;
- time-to-first touch of 0.999 if it occurs within 24h.

Diagnostics cannot rescue the frozen 24h implementation.

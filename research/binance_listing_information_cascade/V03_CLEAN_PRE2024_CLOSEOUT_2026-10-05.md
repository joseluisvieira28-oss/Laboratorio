# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.3 CLEAN PRE-2024 CLOSEOUT
Date: 2026-10-05
Status: SOURCE_BLOCKED — STRONG DESCRIPTIVE SIGNAL, NO EDGE CLAIM

## Authority
Pre-outcome freeze: V03_CLEAN_PRE2024_PRE_OUTCOME_FREEZE_2026-10-05.md
Freeze commit: 08b83cb2bbf10d3806425c833f648032fcaaee23
Discovery period: 2022-2023 only.
2024 V0.2 is quarantined and not used as confirmatory evidence.

## Technical remediation
Initial frozen runner produced n=8 because Bitget chunk boundaries skipped one minute per request chunk.
Source-only diagnostics proved this for LDO, PEPE and PENDLE. V0.3.1 changed only chunk overlap/deduplication; no asset, T0, venue binding, metric, threshold or gate changed.
STG remained non-evaluable for the frozen volume-shock ratio because its KuCoin T-24h..T-1h median 5m baseline volume is exactly zero. Venue shopping or redefining zero after outcomes is prohibited.

## Final frozen-gate result
Verdict: SOURCE_BLOCKED
n with all frozen metrics evaluable: 11 / required 12

- median R1: +15.4996%
- median R5: +18.6221%
- median R15: +19.5014%
- median R60: +14.4810%
- R15 positive hit-rate: 100%
- median evaluable 5m volume shock: 103.49x
- leave-one-out R15 sign stability: PASS
- largest positive R15 contribution: 23.11% (<35% gate)

All price-direction observations in the 12-asset frozen universe had positive R15, including STG; however STG cannot count toward the frozen all-metrics n because its volume-shock denominator is zero.

## Secondary delayed-entry diagnostics (11 all-metric-evaluable observations)
Entry is first full minute boundary at least 60 seconds after official T0.
- median gross +5m: +2.4021%
- +5m hit-rate: 72.73%
- median +5m excess vs venue-matched BTC: +1.9600%
- median gross +15m: +0.7283%
- +15m hit-rate: 54.55%
- median gross +60m: +0.1238%
- +60m hit-rate: 54.55%

These are descriptive only. V0.3 did not include costs/slippage and is not a tradability or live-trading authorization.

## Scientific conclusion
V0.3 does NOT earn SURVIVES because n=11 < 12 under the precommitted all-metrics gate.
It also does NOT support NO_EDGE: the direction/size evidence is unusually strong and the blocking condition is a precommitted metric-definition/source issue, not a failed price-effect gate.

Correct next experiment: untouched 2025 validation with a new freeze created before any 2025 price outcome is opened. The new protocol may remove the zero-denominator-prone volume ratio from the PRIMARY gate only if that change is frozen before 2025 outcomes; volume remains diagnostic.

Governance unchanged: research-only; no main merge; no live trading; no orders; no account/private endpoints; no wallets.

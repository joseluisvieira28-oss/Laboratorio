# REACTIVE-SHOCK-SCALP-005 — DISCOVERY REPLICATION R1 FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: FRESH DISCOVERY REPLICATION

## Purpose
Attempt to replicate the initial 8-event MVE survivor without changing the signal.

## Fresh event set
All 14 remaining eligible 2023 CPI/NFP releases after Bybit archive availability that were not used in the initial MVE.

- 7 CPI
- 7 NFP
- zero overlap with the initial MVE

Official BLS schedule authority.
No outcome-based event exclusions.

## Frozen signal — NO CHANGES
FLOWPRICE_W2 only.

At T0+2s:
1. compare entry mid with last valid pre-release mid;
2. direction = sign(entry_mid - pre_release_mid);
3. compute normalized aggressive trade flow using only T0 <= trade_time < T0+2s;
4. require flow nonzero and same-sign as price displacement;
5. enter at first BBO at/after T0+2s;
6. exit at first BBO at/after entry+60s.

No alternate variants.
No alternate exit horizons.
No thresholds.

## Economic proxy
Historical executable BBO is Bybit.

Report:
- directional mid return;
- Bybit taker/taker gross BBO return;
- MEXC fee-only proxy = gross - 16 bps;
- implementation-stress proxies = gross - 16 bps - extra buffer.

Predeclared extra total implementation buffers:
- 0 bps
- 5 bps
- 10 bps
- 20 bps

The buffer is not claimed to equal actual MEXC slippage. It is a stress test.

## Primary strict replication metric
Use the 10 bps extra implementation buffer:
stress10_net = taker_gross - 26 bps.

R1 = REPLICATION_SURVIVES only if ALL:
- resolved n >= 12;
- CPI resolved n >= 6;
- NFP resolved n >= 6;
- pooled mean stress10_net > 0;
- pooled median stress10_net > 0;
- CPI mean stress10_net > 0;
- NFP mean stress10_net > 0;
- positive stress10 events >= 8;
- deterministic 5,000-draw event bootstrap 95% CI lower bound for mean stress10_net > 0.

Otherwise:
REPLICATION_FAILS_STRICT_GATE.

## Governance
- still Discovery, not OOS;
- 2025 OOS locked;
- 2026 holdout locked;
- no MEXC execution claim;
- no live trading;
- no threshold/horizon rescue after outcomes.

# EXTREME-FLOW-HIGHVOL-REVERSION-2026-001 — Confirmatory Holdout V0.1

Status: FROZEN PRE-HOLDOUT / RESEARCH ONLY
Branch: extreme-flow-highvol-reversion-2026-v0.1

## Discovery origin
EXTREME-FLOW-REVERSION-OOS-001 passed on untouched 2025 data with a small broad extreme-flow reversal effect.
A post-OOS Discovery analysis of the already-open 2025 event ledger found a materially stronger, simple participation condition:

- retain the same extreme-flow event rule;
- require base_volume >= 2.0 * rolling q75 base_volume;
- fade aggressor direction;
- primary horizon = 240 minutes.

2025 Discovery observation for this new hypothesis:
- n = 246
- gross mean fade R240 = 16.5229 bps
- gross median fade R240 = 10.3531 bps
- hit rate = 59.7561%
- gross profit factor = 1.6999

These values are Discovery only. The confirmatory window below had not been accessed by this family when this protocol was frozen.

## Source
Official public Binance Vision BTCUSDT Spot 1m klines, checksum verified.
Warmup: December 2025.
Holdout: 2026-01-01 00:00 UTC through 2026-10-01 00:00 UTC.
Monthly archives are used where available; completed daily archives may be used for the final incomplete archive month. Source semantics may not change.

## Base 5m construction
Exactly five aligned 1m bars.
base_volume = sum 1m base volume.
taker_buy = sum 1m taker-buy base volume.
aggressive_sell = base_volume - taker_buy.
delta_pct = (taker_buy - aggressive_sell)/base_volume.
d = sign(delta_pct).

## Frozen event rule
Rolling baseline = prior 2,016 valid 5m bars.
Candidate requires:
- abs(delta_pct) >= rolling q95 prior abs(delta_pct)
- base_volume >= rolling q75 prior base_volume
- base_volume >= 2.0 * rolling q75 prior base_volume
- d != 0

The first q75 condition is subsumed by the 2.0x condition and is retained only to preserve lineage.

Accepted-event cooldown = 12 bars / 60 minutes.
No trend, session, volatility, path-efficiency, POC, news, side, or price filter.

Trade hypothesis direction = -d (fade aggressor flow).

## Frozen outcome
Primary gross fade return:
F240 = -d * (close_T+240m / close_T0 - 1) * 10000.

Secondary horizons have no rescue authority.

## Minimum evidence
- >=100 accepted events
- >=60 distinct UTC event dates
- >=99% valid 5m source coverage
- >=99% F240 outcome coverage
- zero unresolved conflicts

## Gross holdout gate
HOLDOUT_MECHANISM_SURVIVES requires ALL:
1. mean F240 > 0
2. median F240 > 0
3. deterministic bootstrap 95% CI for mean F240 has lower bound > 0
4. hit rate P(F240>0) > 50%
5. Wilson 95% lower bound of hit rate > 50%
6. at least 2 of 3 complete 2026 calendar quarters (Q1-Q3) have median F240 > 0

Bootstrap = 10,000 resamples, seed 20261001.

## Current automated execution cost model
For current viability only, apply the MEXC API Futures fee schedule published effective 2026-06-01:
- maker = 6 bps per side -> 12 bps round trip
- taker = 8 bps per side -> 16 bps round trip

Fee-only net:
NET12 = F240 - 12
NET16 = F240 - 16

Stress adds 2 bps round-trip implementation friction:
NET14 = F240 - 14
NET18 = F240 - 18

A cost model is ECONOMIC_SURVIVES only if:
- mean net > 0
- profit factor > 1
- bootstrap 95% CI lower bound of mean net > 0

This does not model maker fill probability, basis/funding, queue position, latency, or adverse selection. Therefore maker ECONOMIC_SURVIVES would authorize only a later execution-feasibility test, not live trading.

## Overall classification
- HOLDOUT_FAILED if gross gate fails.
- HOLDOUT_GROSS_SURVIVES_COST_BLOCKED if gross gate passes but NET12 fails.
- HOLDOUT_GROSS_SURVIVES_MAKER_ECONOMIC_SURVIVES if gross gate and NET12 pass.
- Taker viability is reported separately using NET16.

## Anti-rescue
After 2026 holdout opens:
- no threshold change
- no 2.0x participation change
- no horizon change
- no cost lowering
- no session/side/regime filter
- no event deletion
- no quarter deletion
- no lag shift
- no secondary-horizon rescue

Any change requires a new identity and untouched data.

## Authority
Research only.
No live trading.
No orders.
No exchange mutation.
No main merge.
Trading authority: NONE.

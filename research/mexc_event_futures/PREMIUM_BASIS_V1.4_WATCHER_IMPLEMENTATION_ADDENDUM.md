# PREMIUM BASIS V1.4 — FORWARD WATCHER IMPLEMENTATION ADDENDUM

Date: 2026-10-03
Status: TECHNICAL IMPLEMENTATION FREEZE / NO RETUNING

Parent scientific freeze:
`PREMIUM_BASIS_V1.4_FORWARD_FREEZE.md`

Immutable parent freeze commit:
`729c795e28b6e36af3496116352618b3dea0685d`

Immutable prospective boundary:
`2026-10-02T18:15:20Z`

This addendum changes no scientific parameter.

## Frozen implementation

Source:
- MEXC public standard-futures index-price Min5 for MUSTOCK_USDT;
- MEXC public standard-futures fair-price Min5 for MUSTOCK_USDT;
- unauthenticated GET only.

Mapped observable time:
raw Min5 timestamp `s` -> `s + 300 seconds`.

Feature reproduction is exactly the parent V1.3 logic:
- premium_bps = (fair-index)/index*10000;
- trailing 24h window;
- max 288 completed Min5 observations;
- min 240;
- sample standard deviation;
- current mapped observation included exactly as in V1.3;
- no interpolation or future carry.

Cells:
- PRIMARY: 10m, |z|>=1.0, FOLLOW_PREMIUM;
- diagnostics: 10m z1.5, 10m z2.0, 30m z1.5, 30m z2.0.

Alignment:
- 10m cells only evaluate mapped timestamps divisible by 600 seconds;
- 30m cells only evaluate mapped timestamps divisible by 1800 seconds.

Direction:
- z>0 => UP;
- z<0 => DOWN;
- z=0 => no signal.

Target:
- exact public index mapped timestamp `t + horizon`;
- no nearest-bar substitute.

## First-seen rule

At each polling iteration the watcher scans every eligible mapped timestamp after the immutable
freeze boundary that has not previously been journaled in the current batch.

For any qualifying signal:
- if first_seen_at < target timestamp => `PROSPECTIVE_INCLUDED_PENDING`;
- if first_seen_at >= target timestamp => `LATE_DISCOVERY_EXCLUDED`.

A late signal is permanently excluded. It may never be rescued.

When a pending target becomes available, resolve WIN/LOSS/TIE using the frozen direction.
No signal first observed after target can enter prospective statistics.

## Bounded batch

Initial bounded batch:
- maximum 3 hours;
- polling cadence 30 seconds;
- source-only directional shadow;
- no Event Futures order;
- no account/auth/private endpoint;
- no product-state substitution.

This batch does not claim continuous monitoring after it exits.

## Product-state distinction

Current Event Futures product state is not part of the directional outcome definition.
If MUSTOCK_USDT is PAUSE/OFFLINE, directional shadow evidence may still accumulate, but it is
NOT an exact eligible Event Futures decision and must not be called exact Event Futures PnL.

## Gate invariants

PRIMARY readiness remains exactly:
- >=500 resolved PROSPECTIVE_INCLUDED primary observations;
- >=14 calendar days span;
- accuracy >55.5555556%;
- Wilson95 lower >50%;
- illustrative EV80 >0;
- source integrity PASS;
- zero duplicate ids;
- zero rule deviations;
- zero unexplained missed-signal gaps.

No early survivor verdict.

# MEXC EVENT FUTURES LAB — PREMIUM BASIS V1.4 PROSPECTIVE SHADOW FREEZE

Date: 2026-10-02
Status: FROZEN PROSPECTIVE SHADOW / NO CAPITAL / FAIL-CLOSED

## Parent evidence

V1.2:
- exact five-cell MUUSDT FOLLOW_PREMIUM family survived final September holdout;
- 5/5 Holm-corrected survivors.

V1.3:
- INTEGRITY_PASS_ROBUSTNESS_REPORTED;
- exact September parent results reproduced;
- zero feature-forward violations;
- zero target timestamp violations;
- zero same-cell overlap violations;
- zero source missingness at aligned entries for all five cells;
- no October outcomes accessed.

## Prospective model-selection rule

The nested family contains multiple thresholds and two horizons. For prospective governance, one canonical PRIMARY is chosen using a structural anti-cherry-picking rule, not the best historical return:

**PRIMARY = least restrictive threshold at the shortest frozen horizon.**

Therefore:
- PRIMARY: MUUSDT / 10m / |z_premium| >= 1.0 / FOLLOW_PREMIUM.
- DIAGNOSTIC siblings:
  - 10m / |z| >= 1.5
  - 10m / |z| >= 2.0
  - 30m / |z| >= 1.5
  - 30m / |z| >= 2.0

The diagnostics cannot replace or rescue the PRIMARY.

## Forward boundary

No signal with model entry timestamp at or before the commit timestamp of THIS freeze document is eligible as prospective evidence.

The implementation addendum may record the immutable freeze commit SHA and its commit timestamp. That does not change this rule.

No retroactive inclusion:
- first observation of a new signal must occur before its frozen target timestamp;
- a signal first discovered after its target timestamp is recorded as LATE_DISCOVERY_EXCLUDED and cannot enter prospective statistics.

## Frozen source/model

Symbol:
`MUSTOCK_USDT`

Public index Min5:
`https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT`

Public fair-price Min5:
`https://contract.mexc.com/api/v1/contract/kline/fair_price/MUSTOCK_USDT`

Raw close timestamp `s` becomes observable at `s + 300 seconds`.

Feature:
- fair/index premium in bps;
- trailing 24h z-score;
- max 288 completed Min5 observations;
- minimum 240;
- sample standard deviation;
- no interpolation/future carry.

Signal:
- positive qualifying z => UP;
- negative qualifying z => DOWN.

Target:
- sign(index[t+H] - index[t]).

## Watcher requirements

The watcher runs read-only against public data.

For every first-seen signal persist:
- deterministic signal_id;
- cell_id;
- model entry timestamp;
- first_seen_at_utc;
- detection latency seconds;
- z-score;
- premium bps;
- signal direction;
- entry public index;
- frozen target timestamp;
- status.

When the target public index becomes available persist:
- resolution observed_at_utc;
- target public index;
- WIN / LOSS / TIE;
- resolution latency.

Never overwrite first_seen_at.

## Prospective evidence inclusion

A signal is `PROSPECTIVE_INCLUDED` only if:
- model entry > immutable freeze timestamp;
- first_seen_at < target timestamp;
- all frozen source/feature fields are available causally;
- no rule deviation.

Late first discovery remains in audit ledger but is excluded from performance statistics.

## Exact payout evidence

Directional shadow evidence and exact-product payout evidence remain distinct.

Current exact public DOM facts already observed:
- MUUSDT currently offers 10m / 30m / 1H / 4H;
- current MUUSDT Up/Down payout observed as 80% / 80% in repeated source snapshots.

The prospective directional watcher MUST NOT fabricate payout-at-entry.

A separate read-only payout observer may capture contemporaneous public DOM payout snapshots. Such a snapshot must carry its actual observation time and MUST NOT be relabeled as the exact payout at an earlier model timestamp.

## Prospective readiness gate — PRIMARY only

Minimum before any future execution review:
- >= 500 resolved PROSPECTIVE_INCLUDED PRIMARY observations;
- span >= 14 calendar days between first and latest PRIMARY entry;
- directional accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- illustrative EV at 80% > 0;
- zero rule deviations;
- zero duplicate signal_ids;
- zero missed-signal gaps that cannot be accounted for;
- source integrity PASS.

This gate only allows:
`MICRO_LIVE_PRODUCT_SEMANTICS_REVIEW_ELIGIBLE`

It does NOT authorize live Event Futures trading.

## Product semantics blockers still open

Before exact micro-live eligibility:
- exact expiry settlement tick/rounding must be established;
- contemporaneous payout-at-entry capture must be operationally trustworthy;
- execution path must be explicitly authorized and technically supported.

Official MEXC documentation currently says Event Futures API trading is unsupported.

## Hard prohibitions

- no Event Futures order;
- no Up/Down trading click;
- no account/balance request;
- no authenticated exchange request;
- no wallet/exchange mutation;
- no parameter tuning;
- no diagnostic sibling rescue;
- no backfill as prospective evidence;
- no merge to main.

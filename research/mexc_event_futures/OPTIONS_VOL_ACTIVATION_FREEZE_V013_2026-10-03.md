# OPTIONS-VOL-FWD-001 — pre-outcome activation freeze V0.1

Date: 2026-10-03 Europe/Zurich. FORWARD-ONLY / SHADOW.
Source gate: run 37073818293, commit a277123b29ab2e7028a7b2858845170f6f583ac6.
Artifact 11255507173, zip SHA256 9fd39ca56bbd4de1cfffafa1ba07e4b9b3b81905c4afa79a9019c6b7b73eb5f2.
36/36 preserved raw bodies passed independent SHA256 and byte-length verification.
BTC 3/3 and ETH 3/3 valid matched pairs; zero Event Futures outcomes opened.
The separate local transport had BTC 2/3 and ETH 3/3: PARTIAL_SOURCE, preserved
without replacing its failures with runner observations. The runner is the eligible runtime.

## Hypothesis, not an established edge

Directional risk-reversal imbalance may convey near-term demand for downside/upside
protection. Test FOLLOW_INSURANCE_SKEW, not FADE. Option IV is risk-neutral pricing,
not a proven physical directional probability; 7–30-day skew predicting a 10-minute
move is explicitly an untested hypothesis. No alternative direction/horizon is evaluated
on this version's outcomes. The 5 percentage-point threshold below is a fixed preregistered
hypothesis threshold, not fitted on outcomes or a claim of optimality.

## Immutable rule

Canonical parameters and rule hash: OPTIONS_VOL_RULE_V013_V01.json.
Allowed Event Futures symbols: BTC_USDT and ETH_USDT.
Source selection/validation: exactly the OPTIONS source gate algorithm and fields.
Nearest active expiry with 7–30 days remaining, two candidate strikes per side,
then closest valid actual delta to +/-0.25 (tiebreak instrument name); no interpolation.
Require both actual absolute deltas in [0.15,0.35], pair timestamp spread <=5s,
positive finite bid/ask IV, mark IV, quote amounts/prices and index/forward prices.

skew_pp = put mark_iv - call mark_iv, same expiry.
- skew_pp >= +5.0: DOWN.
- skew_pp <= -5.0: UP.
- otherwise NO_SIGNAL; no retrospective threshold relaxation.

Horizon: exactly 10 minutes (MINUTE=10). Missing cycle => BLOCKED, no fallback horizon.
Signal source time: max(call timestamp, put timestamp); condition time is after both
responses are received. Max signal age: 5 seconds at the shadow decision, with
future-clock tolerance at most 1 second. Source polling: one round per 60-second
UTC minute; no retry in that minute. Identical source hash pair deduplicated.
Signal ID = SHA256(family version + symbol + pair raw hashes + rule hash).
Within family/version/symbol/horizon, unresolved observation => SKIPPED_OVERLAP.

## V0.13 decision and expiry unchanged

Capture a NEW passive browser-generated exact product response after the condition
receipt. Do not actively fetch /event_contract/detail. First public index tick at or
after the fully received payout response; both server time ordering and local receive
ordering are required. Local payout/index join <=5 seconds. ONLINE product, exact
MINUTE=10 cycle, actual direction-specific q>0. No payout filter above q>0.
Persist raw product body, condition receipt, raw decision tick, source hashes and rule
hash before waiting for expiry. Return WIN=+q, LOSS=-1, TIE=0; p_BE=1/(1+q).
Expiry is the first valid public index tick at/after decision+10min, lateness <=5s;
missing/stale/gapped stream => BLOCKED, never candles/interpolation.
Public index remains a SHADOW decision index, never an executed order openPrice.

## Evidence and analysis boundary

Forward boundary is the GitHub commit timestamp of the FIRST commit containing this
freeze and the canonical rule JSON. All source times used for a signal must be after
that boundary. Earlier gate/calibration observations may not become shadow events.
Minimum N=100 per symbol cell. Direction policy is FOLLOW_INSURANCE_SKEW (UP and DOWN
signals share one cell per symbol); there are exactly two possible primary cells.
Freeze one evaluation batch at boundary+30 calendar days, with all eligible finalized
events from that window. Do not repeatedly peek/test significance as N crosses 100.
Before the batch date report only collection counts, blocked reasons and INSUFFICIENT_N
or AWAITING_FROZEN_BATCH, never survivor claims. No repeated stopping on significance.
At batch date, run unchanged V0.13 200000-null/20000-bootstrap/Holm/thirds gates,
passing the frozen family minimum 100 explicitly. September holdouts remain closed.

## Runtime boundary

Initial bounded push-triggered smoke run accepts signals for 120 seconds and, if
necessary, drains pending 10-minute expiries for at most 660 additional seconds.
It is not continuous collection. No main changes, cron, paid runtime or live trading.
Source-only preflight checks payout/index freshness without opening research outcomes.
If preflight fails, activation is FROZEN_RUNTIME_BLOCKED and outcomes remain closed.
If it passes, the bounded smoke may open forward shadow observations under this rule.
Runs after this smoke require a persisted ledger and pre-run continuity receipt; do not
silently start a second independent ledger or recreate pending observations after restart.

No rules may change after first outcome. New versions require new future data.

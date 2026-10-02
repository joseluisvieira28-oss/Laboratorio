# MEXC EVENT FUTURES LAB — EVENT-CONDITIONED EDGE V0.13 PRE-REGISTRATION

Date: 2026-10-03
Status: PRE-OUTCOME FREEZE / FORWARD-ONLY / SHADOW RESEARCH

## Upstream gates

V0.11.6: `EXACT_PAYOUT_FIELDS_FOUND`

V0.12: `PROSPECTIVE_SNAPSHOT_PASS`

V0.12.1: `PUBLIC_INDEX_STREAM_PASS`

These gates prove that the lab can observe current Event Futures payout configuration and a public index-price stream without login, private account access or orders.

## Critical terminology

V0.13 is **shadow Event Futures research**.

A shadow decision index is not an executed Event Futures `openPrice`.

The live order builder sends `symbol, amount, side, payRate, cycleAmount, cycleType`; `openPrice` is server-assigned. Therefore V0.13 must never describe its shadow entry as an exact executed order price.

No live order is required or authorized.

## Main research question

For a condition that is defined and timestamped before the decision snapshot, does the direction supplied by that condition produce a positive expected unit return after applying the **actual Event Futures payout observed at that decision time**?

For event i with direction-specific payout q_i:

- correct shadow outcome: return = q_i
- incorrect shadow outcome: return = -1
- tie: return = 0
- event-specific break-even probability: p_BE_i = 1 / (1 + q_i)

No fixed 80% payout assumption is permitted.

## Eligible product state

A shadow decision is eligible only when:

- product state is exactly `ONLINE`;
- the requested cycle exists in the exact product configuration;
- direction-specific payout is numeric and > 0;
- exact payout source body has a SHA-256;
- public index source is healthy.

PAUSE and OFFLINE products remain observable source data but are not eligible shadow decisions.

## Frozen data join

Each event condition must arrive as an immutable condition receipt containing:

- `family_id`
- `family_version`
- `signal_id`
- `signal_source`
- `signal_source_ts_utc`
- `signal_received_at_utc`
- `symbol`
- `direction` = UP or DOWN
- `horizon_minutes`
- `condition_payload_hash`
- `rule_hash`

A family activation freeze must specify its allowed symbols, direction rule, horizon(s), max signal age, deduplication rule and minimum N **before that family's first outcome is opened**.

V0.13 core must not infer direction or horizon from later price behavior.

## Decision snapshot protocol

For an eligible condition:

1. validate that the family/version is ACTIVE in the frozen registry;
2. validate signal provenance and source timestamp;
3. capture the exact Event Futures product/payout snapshot;
4. capture the first public `push.index.price` tick at or after the payout source-response time;
5. define `decision_ts` as that index tick's server timestamp;
6. require payout source-response time and decision index local receive time to be within 5 seconds;
7. select the payout for the condition's pre-frozen direction and cycle;
8. persist all source hashes before waiting for expiry.

If the 5-second source-join freshness gate is missed, the event is `BLOCKED_STALE_DECISION_JOIN`; it may not be rescued after outcome.

## Shadow expiry protocol

For a frozen horizon H:

- target expiry server timestamp = `decision_ts + H*60*1000`;
- expiry index = first valid `push.index.price` tick with server timestamp >= target;
- maximum allowed lateness = 5 seconds;
- if no valid tick is captured inside the lateness window, verdict = `BLOCKED_MISSING_EXPIRY_INDEX`;
- no interpolation and no later candle substitution.

Outcome:

- UP correct if expiry_index > decision_index;
- DOWN correct if expiry_index < decision_index;
- equality is TIE.

## Overlap / dependence control

Within the same `family_id + family_version + symbol + horizon_minutes`, only the first eligible signal may open a shadow observation while a prior observation in that cell is unresolved.

Later overlapping signals are recorded as `SKIPPED_OVERLAP` and are not evaluated.

This rule is frozen to reduce dependence and signal stacking.

## Scientific families

V0.13 core defines the protocol but activates **zero signal families** by itself.

The initial registry contains four economically distinct source-gated families:

- `MACRO-POSTRELEASE-FWD-001`
- `OPTIONS-VOL-FWD-001`
- `LIQUIDATION-FLOW-FWD-001`
- `IMPORTED-FROZEN-SIGNAL-FWD-001`

Each remains `SOURCE_GATE_REQUIRED` until a separate pre-outcome family freeze defines an immutable source and rule.

No family may be activated because its first observed outcomes look attractive.

## Statistics

Primary unit: one non-overlapping finalized shadow event.

For each frozen analysis cell (`family_id, family_version, symbol, horizon_minutes, direction_policy`):

- N total resolved non-blocked events;
- wins, losses, ties;
- empirical win rate excluding ties;
- total and mean unit return using each event's actual payout;
- mean observed payout;
- mean event-specific break-even probability;
- chronological-third unit returns.

### Break-even null

For event i, null success probability is the event-specific:

`p_i = 1/(1+q_i)`.

For the observed sequence of payouts, calculate a one-sided Monte Carlo null for total unit return:

- 200,000 simulations;
- independent Bernoulli draws with p_i;
- same q_i and return function as observed;
- RNG seed = 130313;
- p-value = (1 + simulated totals >= observed total) / (1 + simulations).

### Confidence interval

Mean unit return 95% percentile bootstrap:

- 20,000 resamples;
- RNG seed = 130314;
- ties remain return 0;
- no stratification or adaptive resampling.

### Multiplicity

All cells that reach their frozen minimum N in the same evaluation batch are corrected using Holm-Bonferroni family-wise alpha 0.05.

No unadjusted significance may be called a survivor.

## Minimum evidence

Absolute floor: no cell can be evaluated for survival below N=20.

A family activation freeze may set a higher minimum but never a lower one.

## Survivor gate

A cell can receive `SURVIVES_FORWARD_SHADOW_GATE` only when all are true:

- N >= frozen family minimum N;
- mean unit return > 0;
- 95% bootstrap lower bound of mean unit return > 0;
- Holm-adjusted p < 0.05;
- each chronological third has positive total unit return;
- zero source-integrity violations;
- zero post-outcome rule changes.

Otherwise the cell is `NO_SURVIVOR`, `INSUFFICIENT_N`, or `BLOCKED` as appropriate.

## Anti-tuning rules

Forbidden after a family's first outcome is opened:

- changing direction logic;
- changing horizon mapping;
- changing thresholds;
- changing payout filter;
- changing signal freshness;
- changing overlap/cooldown logic;
- lowering minimum N;
- changing statistical gate;
- deleting losing events;
- retroactively activating a family.

A failed family requires a new economically justified version and a new future boundary; it cannot rescue the old outcomes.

## Holdout

No September 2026 protected holdout from prior proxy labs may be opened or repurposed to tune V0.13.

V0.13 is a new forward-only program.

## Safety

- no login;
- no API keys for Event Futures;
- no private Event Futures endpoints;
- no orders;
- no live trading;
- no wallet/account mutation;
- no merge to main.

## Promotion language

Before exact executed Event Futures receipts exist, the strongest allowed language is:

`SURVIVES_FORWARD_SHADOW_GATE`

Never `LIVE EDGE`, `MICRO-LIVE GO`, `PROFITABLE LIVE STRATEGY` or equivalent.

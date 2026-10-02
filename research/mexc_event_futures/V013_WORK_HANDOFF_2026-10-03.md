# CRYPTO LAB — MEXC EVENT FUTURES CONTINUATION HANDOFF

Date: 2026-10-03
Branch: `mexc-event-futures-event-conditioned-v0.13-prereg-2026-10-03`

## Operator intent

Continue aggressively but scientifically. No fake promotion. Preserve all pre-outcome freezes and fail closed on source/timestamp ambiguity.

## Hard prohibitions

- no merge to main;
- no live Event Futures trading;
- no Event Futures orders;
- no private Event Futures endpoints;
- no account/balance/position reads;
- no API keys for Event Futures;
- no wallets or spending;
- no post-outcome tuning;
- no opening old protected September 2026 holdouts to rescue V0.13.

## Authoritative breakthroughs

### V0.11.6 — exact product/payout source

Verdict: `EXACT_PAYOUT_FIELDS_FOUND`

Authoritative run: 37070907487

The normal fresh unauthenticated Event Futures page passively returned HTTP 200 JSON from:

`https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail`

The response exposes exact current product configuration including `cycleConfigMap`, `upPayRate`, `downPayRate`, product state, contract id and min/max amounts.

Critical correction: Event Futures payout is NOT a fixed 80%.

The authoritative V0.11.6 snapshot simultaneously contained payout values 0.40, 0.70, 0.80, 0.85 and 0.87 depending on product/cycle.

### V0.12 — prospective exact-product collector

Verdict: `PROSPECTIVE_SNAPSHOT_PASS`

Authoritative hardened run: 37071442675

- 9 products
- 32 product-cycle rows
- exact source hash
- exact payout fields
- deterministic break-even fields
- NO_AUTH / NO_ORDERS / NO_MUTATION / NO_PRIVATE all PASS

The first attempt exposed a duplicate-response race. It was fixed so only a valid HTTP 200 JSON response with success=true and non-empty product data can become the authoritative detail capture.

### V0.12.1 — exact public index source for shadow research

Verdict: `PUBLIC_INDEX_STREAM_PASS`

Authoritative run: 37071859766

Public read-only websocket:

`wss://futures.mexc.com/edge`

Public subscriptions:

- `sub.index.price BTC_USDT`
- `sub.index.price ETH_USDT`

Both returned live `push.index.price` messages with server timestamps and raw SHA-256 evidence.

The public Event Futures web bundle independently uses the same `sub.index.price` / `push.index.price` channel for its Event Futures index state.

### V0.13 — preregistered event-conditioned shadow protocol

Current branch contains:

- `EVENT_CONDITIONED_EDGE_FREEZE_V0.13.md`
- `V013_FAMILY_REGISTRY_V0.1.json`
- `V013_SHADOW_EVENT_SCHEMA.json`
- `shadow_event_evaluator_v013.py`

Engine self-test run 37072254278: PASS.

Important: the self-test is synthetic mechanics validation only.

`RESEARCH_OUTCOMES_OPENED=0`

`ACTIVE_FAMILIES=0`

Do not quote the synthetic survivor as evidence of an edge.

## V0.13 frozen statistical gate

Each real shadow event uses the actual direction-specific payout observed at decision time.

For payout q:

`p_BE = 1/(1+q)`

Unit return:

- correct = +q
- incorrect = -1
- tie = 0

Survival requires:

- N >= frozen family minimum, never below 20;
- mean unit return > 0;
- 95% bootstrap lower bound > 0;
- break-even-null Monte Carlo p-value surviving Holm-Bonferroni alpha 0.05;
- positive total return in every chronological third;
- zero source-integrity violations;
- zero post-outcome rule changes.

## Critical execution limitation

The public index stream is a defensible **shadow decision index**.

It is NOT proven equal to a real Event Futures order `openPrice`.

Static order code sends:

`symbol, amount, side, payRate, cycleAmount, cycleType`

and does not send `openPrice`; the server assigns actual position openPrice.

Therefore all V0.13 outputs must remain SHADOW until exact execution receipts are legitimately available under a separate authority.

## Next mission

Do SOURCE-FIRST family activation work. Do not open outcomes before each family-specific freeze.

Priority source gates:

1. `LIQUIDATION-FLOW-FWD-001`
   - prove a free/public timestamped forced-liquidation source for BTC/ETH;
   - preserve raw messages and hashes;
   - if historical source is unavailable, use a forward calibration period before freezing thresholds;
   - do not choose FOLLOW vs FADE after seeing Event Futures outcomes.

2. `OPTIONS-VOL-FWD-001`
   - prove a public/free options IV/skew source with defensible timestamps;
   - source-gate the exact fields needed before defining a directional rule;
   - do not reuse invalid/stale IV observations from earlier labs.

3. `MACRO-POSTRELEASE-FWD-001`
   - scheduled CPI/NFP release times may be sourced from official releases;
   - prior News Shock V0.3 consensus hypothesis is SOURCE_BLOCKED and must not be revived;
   - any new rule must not require unproven historical consensus.

4. `IMPORTED-FROZEN-SIGNAL-FWD-001`
   - only accept signals whose exact rule/authority existed before V0.13 activation;
   - whitelist candidate IDs and horizon mapping before the first Event Futures shadow outcome.

For any source that passes, create a family-specific pre-outcome activation freeze containing direction rule, horizon mapping, max signal age, overlap rule, min N and rule hash. Only then begin forward shadow observations.

## Operational note

GitHub scheduled workflows execute from the repository default branch. Main is not authorized for merge/change here, so do not pretend a cron added only to this research branch is a durable forward collector. Use explicit/manual research runs or another operator-approved forward runtime without weakening governance.

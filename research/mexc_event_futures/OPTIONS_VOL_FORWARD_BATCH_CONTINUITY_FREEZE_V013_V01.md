# OPTIONS-VOL-FWD-001 — FORWARD BATCH CONTINUITY FREEZE V0.13.1

Date: 2026-10-03
Status: ACTIVE RULE / FORWARD SHADOW / BOUNDED CONTINUATION

## Immutable scientific authority

The scientific rule is unchanged:

- activation freeze: `OPTIONS_VOL_ACTIVATION_FREEZE_V013_2026-10-03.md`
- rule file: `OPTIONS_VOL_RULE_V013_V01.json`
- rule hash: `edd02c530398465cb35e481f96e336ebd0dcccc73235aaffe6c1d984c3986517`
- direction: FOLLOW_INSURANCE_SKEW
- threshold: absolute skew 5.0 percentage points
- horizon: 10 minutes
- max signal age: 5 seconds
- unresolved overlap: first only
- minimum N: 100 per symbol
- frozen batch horizon: 30 calendar days
- no significance peeking before frozen batch.

No threshold, direction, horizon, source selection or statistical rule changes are permitted here.

## Prior ledger anchor

Initial bounded smoke:

- run: `37074644170`
- job: `111061698944`
- artifact: `v013-options-frozen-forward-smoke`
- artifact id: `11255948065`
- artifact digest: `sha256:c4e5379eeebfc99a4109872d8e50005137e3b9377986791259a9a9dbb69b4ebe`
- rule hash: exact match
- runtime preflight: PASS
- resolved N: 0
- outcomes opened: 0
- pending observations at close: 0
- statistics run: false
- status: INSUFFICIENT_N

The smoke contained three polling minutes and no qualifying signal. It therefore contributes no resolved event, no pending event and no dedup identity to carry forward.

## Continuation batch

Run one bounded forward collection window after this freeze is committed:

- accept new source rounds for 10800 seconds maximum;
- poll once per 60-second UTC minute exactly as frozen;
- after acceptance closes, drain any already-open 10-minute shadow event for at most 660 seconds;
- preserve every source round, condition receipt, payout body, decision index, expiry index, blocked reason and finalized event;
- persist a new session receipt and artifact digest.

This is an operational collection-window extension only. It does not change event eligibility or the scientific rule.

## Continuity

The batch starts from the anchored empty prior event ledger above.

Any future batch after this one MUST explicitly anchor this batch's artifact digest and carry forward:

- resolved event identities;
- any pending observation state;
- signal dedup identities;
- blocked-reason ledger.

No second independent ledger is allowed.

## Interpretation

Before N reaches the frozen minimum and before the 30-day batch boundary, outputs are limited to:

- collection counts;
- signal counts;
- blocked reasons;
- resolved N;
- `INSUFFICIENT_N` or `AWAITING_FROZEN_BATCH`.

No survivor/no-edge significance verdict may be produced early.

## Safety

Shadow research only:

- no live Event Futures orders;
- no account/private endpoints;
- no login/API key;
- no wallet/account mutation;
- no merge to main.

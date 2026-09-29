# BTC-CONVEX V0.2 — causal blocker superseded — 2026-09-29

## Result

**PREVIOUS CAUSAL_INTEGRITY_BLOCKED CLASSIFICATION: SUPERSEDED / FALSE POSITIVE**

The append-only blocker receipt remains preserved:
- `V02_CAUSAL_BLOCKER_TRAILING_STOP_NONMONOTONIC_2026-09-29.md`
- blocker commit: `4042c075c305d3da5714b19933794321d39249ba`

It is not deleted or rewritten.

## Why the blocker was incorrect

The frozen V0.2 authority explicitly defines the exact Parent rule as:
- `original non-latched trail semantics`

The preserved causal replay closeout likewise states:
- `non-latched +5% close-based trail selection`

Therefore, under the frozen Parent V5 contract, the active trailing stop is selected from the current completed-bar close state and is **not sticky/latched across later bars**. If a later completed close falls back below the frozen +5% activation threshold, the active stop can revert to the initial 4% hard stop.

The observed SOLUSDT transition:
- peak unchanged at 124.99;
- prior active_stop 109.9912;
- later active_stop 108.57851136;

is therefore compatible with the frozen non-latched Parent V5 semantics and is **not** by itself a causal-integrity violation.

## Authority evidence

`PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE.md`, section 7:
- exact Parent = `original non-latched trail semantics`

`CAUSAL_1H_REPLAY_CLOSEOUT_V0.1.md`:
- preserved replay = `non-latched +5% close-based trail selection`

The sticky/latched trail is a separate child hypothesis and must not be imported into Parent V5.

## Restored operating state

- causal integrity: **PASS**
- source coverage: **PASS**, subject to each fresh snapshot
- V0.2 prospective observations remain creditable under the unchanged frozen contract
- no rule, threshold, timeframe, direction, cost, universe or execution semantic was changed
- no historical outcome was backfilled
- no promotion authority is created

Continue V0.2 forward collection and apply Checkpoints A/B/C exactly as frozen.

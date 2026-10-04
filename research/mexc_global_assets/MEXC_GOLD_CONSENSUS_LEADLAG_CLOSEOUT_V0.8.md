# MEXC-GOLD-CONSENSUS-LEADLAG-001 — DISCOVERY CLOSEOUT V0.8

Date: 2026-10-04
Run: 37212288486
Head: `f79cf30a65f6efe049b4942f181dc33dcfe55332`

## Provenance

- rule SHA256: `eafcb22720b6a747cb2580c2f614abb88652f6b0c342b13210967529173d38bf`
- source binding SHA256: `f824666b1a999b574bda7a26047315c2482c1019e01a7c34bf02a3959fb76864`
- artifact ZIP SHA256: `6eb6735c15d7689c4d2e805119eb2e911f631be04a29b4cb0d5b7fa561ed22a5`

Governance:
- discovery only;
- no 04 October outcomes;
- no retrospective OOS;
- no parameter rescue;
- no live trading authorization.

## Data coverage

- MEXC rows: 4,320
- Binance rows: 4,319
- Bitget rows: 4,314
- Bybit rows: 4,183
- exact common observable minutes: 4,178
- first common minute: 2026-10-01T00:01:00Z
- last common minute: 2026-10-03T23:59:00Z

## Frozen grid result

64 cells tested.

Result:
- pre-Holm eligible cells: 0
- Holm-selected cells: 0
- retrospective OOS opened: false

Frozen machine verdict:

`NO_GOLD_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V08_GATE`

## Why no cell qualified

The family was severely event-starved under the frozen thresholds.

Largest event count occurred at:
`shock=5 bps / gap=3 bps`

Only 3 non-overlapping events existed for each tested horizon.

Observed gross means:
- 1m: N=3, win rate 33.33%, mean +0.5477 bps
- 2m: N=3, win rate 33.33%, mean +2.6947 bps
- 5m: N=3, win rate 33.33%, mean -0.3841 bps
- 15m: N=3, win rate 0%, mean -13.0290 bps

The frozen minimum was N>=20.

Chronological-thirds stability also failed for the positive-mean 1m and 2m cells.

At `shock=5 / gap=5`, only one event existed.
All wider gap / larger shock combinations had zero events.

## Scientific classification

`UNDERPOWERED_NO_PROMOTION_AT_FROZEN_V08_GATE`

This is not evidence that a Gold cross-venue mechanism can never exist.
It is evidence that the frozen V0.8 event definition is too rare to establish a defensible discovery signal in this sample.

Do not lower thresholds or the N gate after observing these outcomes.

Any continuation must use a new economically distinct hypothesis or a pre-frozen future continuation sample.

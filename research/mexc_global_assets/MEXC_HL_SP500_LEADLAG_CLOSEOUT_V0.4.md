# MEXC-HL-SP500-LEADLAG-001 — DISCOVERY CLOSEOUT V0.4

Date: 2026-10-04
Run: 37192442631
Head: `b7fee4c13ac8b8989aa74c00a7f0739947231853`

## Provenance

- rule SHA256: `3620d3a1c0c615ad4ea67c84a5a22736ffb6f36cdf134d9afa7fdfa0f8609b01`
- source binding SHA256: `691aa29d85a435db79f00b3ff48485c568f7d0aecd7f20f94ffd3e9fa7c253ff`
- artifact ZIP SHA256: `ded7e017293629f56aca30afbac3239bd5cb89bb1f0ce67b15529e374207f142`

Governance:
- discovery only;
- no retrospective OOS;
- no data at or after 2026-10-04T09:00:00Z;
- no private endpoints/account reads/wallets/orders/mutation;
- no live trading.

## Coverage

Exact 1-minute clock overlap:
- expected minutes: 4,860
- exact overlap minutes: 4,860
- coverage ratio: 1.000

Source alignment therefore passed.

## Frozen result

36 cells were tested:
- Hyperliquid shock thresholds: 5 / 10 / 20 bps
- lag-gap thresholds: 3 / 5 / 10 bps
- MEXC horizons: 1 / 2 / 5 / 15 minutes
- direction: FOLLOW_HYPERLIQUID only.

Result:
- pre-Holm eligible cells: 0
- Holm-selected cells: 0
- verdict: `NO_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V04_GATE`

## Why the gate failed

The family was event-starved, not merely fee-blocked.

The widest cell family (5 bps Hyperliquid shock / 3 bps lag gap) produced only 4 non-overlapping events across the entire 4,860-minute window.

Observed gross means for those 4 events were:
- 1m: +1.417 bps
- 2m: +3.942 bps
- 5m: +2.915 bps
- 15m: +2.392 bps

But N=4 is far below the frozen minimum N=20, win-rate/statistical evidence was insufficient, and chronological stability was not consistently positive.

At 5 bps shock / 5 bps lag gap there was only 1 event.
All 10 bps and 20 bps shock cells had zero events.

## Scientific verdict

`NO_EDGE_AT_FROZEN_V04_GATE`

Do not rescue this SP500 family by lowering the frozen thresholds or altering direction/horizons after seeing outcomes.

## Next distinct mine

Move to a different economic family/asset rather than retuning SP500.

NAS100 is the next priority because MEXC public contract metadata independently reports:

`NAS100_USDT indexOrigin = ["HYPERLIQUID"]`

This allows a fresh source-binding gate and a separate pre-outcome NAS100 cross-venue family.

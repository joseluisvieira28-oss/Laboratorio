# MEXC-HL-NAS100-DISLOCATION-001 — SOURCE-VALID PRE-OUTCOME FREEZE V0.7

Date: 2026-10-04
Status: FROZEN BEFORE ANY NAS100 OUTCOME SCORING

## Why V0.7 exists

V0.6 failed closed on source coverage before scoring.

Proven source availability:
- Hyperliquid `xyz:XYZ100` first exact overlap with MEXC: `2026-09-30T19:09:00Z`;
- V0.6 printed `SCORING_NOT_YET_STARTED=true`;
- no threshold/horizon/direction outcome was opened.

Therefore V0.7 changes ONLY the historical window.

## Scientific parameters preserved exactly from V0.6

- MEXC symbol: `NAS100_USDT`
- Hyperliquid coin: `xyz:XYZ100`
- signal mode: `FADE_LEVEL_DISLOCATION`
- gap formula: `10000*(mexc_contract_close/hl_close-1)`
- thresholds: 10 / 20 / 40 / 80 bps
- entry delay: 1 minute
- horizons: 1 / 2 / 5 / 15 minutes
- per-cell cooldown until frozen exit
- Discovery minimum N = 30
- chronological thirds must all be positive
- Holm-Bonferroni FWER = 0.05
- OOS minimum N = 15
- OOS exact one-sided binomial p < 0.05
- both OOS halves non-negative
- cost reporting: 0 / 2 / 5 / 10 / 12 / 14 / 16 / 20 bps
- no parameter rescue.

## Source-valid windows

Discovery:
`2026-10-01T00:00:00Z <= signal t < 2026-10-03T00:00:00Z`

Retrospective OOS:
`2026-10-03T00:00:00Z <= signal t < 2026-10-04T09:00:00Z`

Hard fetch boundary:
`2026-10-04T09:00:00Z`

No data at or after 09:00 UTC on 4 October may enter V0.7.

The source-only proof at ~10:04 UTC on 4 October did not score historical outcomes.

## Execution interpretation

Scientific signal survival and economic executability remain separate.

Published standard MEXC API fee-only hurdle:
- maker-maker: approximately 12 bps round-trip;
- maker-taker: approximately 14 bps;
- taker-taker: approximately 16 bps.

V0.7 reports whether OOS gross mean clears these fee-only hurdles, but fees do not alter the scientific statistical gate.

## Promotion ceiling

OOS PASS => `NAS100_CROSSVENUE_OOS_SIGNAL_CANDIDATE`

Even a PASS does not authorize live trading.

Any final future-forward test requires a new freeze after this closeout.

No account reads, wallets, private endpoints, orders or exchange mutation.

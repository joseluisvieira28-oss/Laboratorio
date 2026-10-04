# GLOBAL-ASSET-INDEX-BASIS-001 — V0.1.1 SCIENTIFIC CLOSEOUT

Date: 2026-10-04
Run ID: 37191410719
Branch: `mexc-global-assets-index-basis-v0.1.1-boundary-safe-2026-10-04`
Run head: `a04a1c83bc2e5128738709a80424df6af052f23c`

## Governance

- Source gate: PASS
- Rule SHA256: `2e2579ff13ac96dd2a42363bf24f66cdd65925345c577ddbc53c86fabf2ab943`
- Source receipt SHA256: `3e12f2966ea0b2587e94e86c765ba8b5ff8fa9042c75c3836335dbd6cecfbc5c`
- Scientific artifact ZIP SHA256: `67d86a85a8fb5e17ce540e4ccf1f4ac0bd907d20dbc9aebd5df895ba09263d23`
- no September 2026 or later fetched;
- no private endpoints;
- no account reads;
- no orders / exchange mutation;
- no live trading authorization.

## Coverage

Each of NAS100, SP500, GOLD and NVIDIA had:

- 26,496 contract Min5 rows;
- 26,496 index Min5 rows;
- 26,496 exact timestamp overlaps;
- first observable row: 2026-06-01T00:00:00Z;
- last observable row: 2026-08-31T23:55:00Z.

## Discovery

- 31 cells met the pre-Holm discovery eligibility gate.
- 6 cells survived Holm-Bonferroni.

Holm-selected cells:
1. GOLD — 5 bps — 5 min — p=1.1393578800895665e-06
2. NVIDIA — 5 bps — 15 min — p=1.5484136407638179e-06
3. NVIDIA — 5 bps — 5 min — p=0.0002160660567999635
4. NVIDIA — 5 bps — 30 min — p=0.00032883958289893977
5. NVIDIA — 10 bps — 15 min — p=0.0012307606412410134
6. SP500 — 5 bps — 15 min — p=0.0017273880560550855

NVIDIA retrospective OOS was not opened because the pre-registered contamination firewall classified NVIDIA as future-forward only.

## August OOS

### GOLD — 5 bps / 5 min

Verdict: OOS_FAIL

- N: 1,669
- wins: 854
- win rate: 51.1684%
- mean gross: -0.0147825 bps
- p-value vs 50%: 0.176147
- half means: -0.0489751 / +0.0193692 bps

### SP500 — 5 bps / 15 min

Verdict: OOS_PASS

- N: 809
- wins: 430
- losses: 379
- win rate: 53.1520%
- mean gross: +0.4601053 bps
- exact one-sided binomial p-value: 0.0393495
- chronological half means: +0.2458289 / +0.6738525 bps
- convergence rate: 53.5229%
- median absolute entry basis: 14.3211 bps

Illustrative mean net after fixed round-trip cost:
- 0 bps cost: +0.4601053 bps
- 2 bps cost: -1.5398947 bps
- 5 bps cost: -4.5398947 bps
- 10 bps cost: -9.5398947 bps
- 20 bps cost: -19.5398947 bps

Costs were NOT used to determine scientific survival.

## Frozen verdict

`GLOBAL_ASSET_SIGNAL_CANDIDATES_SURVIVE_OOS`

Survivor:
`SP500 / FADE_BASIS / threshold=5bps / horizon=15m`

Classification:
`SCIENTIFIC_SIGNAL_SURVIVOR__EXECUTION_FEASIBILITY_UNPROVEN`

This is not a diamond and not a live-trading authorization.

## Next legitimate gate

Before opening September 2026, freeze a single-cell holdout:
SP500 / 5 bps / 15 min / FADE_BASIS, no retuning.

If that untouched holdout fails, do not rescue with a nearby threshold or horizon.

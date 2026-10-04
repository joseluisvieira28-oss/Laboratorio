# MEXC NVIDIA CASH-CLOSE DISCOVERY CLOSEOUT V0.3

Date: 2026-10-04
Run: 37227143241
Branch: `mexc-nvidia-cashclose-v0.3-prereg-2026-10-04`

## Provenance

- source gate run: `37227015100`
- source gate verdict: `NVIDIA_CASHCLOSE_SOURCE_PASS`
- discovery artifact ZIP SHA256: `3162570b6d8bf3f9e5ed789eb759b8ec051114ba79c4afc35643dd77bf8d66ca`

17 frozen sessions were available with complete signal data.

## Frozen verdict

`NO_NVIDIA_CASHCLOSE_DISCOVERY_CANDIDATE_AT_FROZEN_V03_GATE`

No retrospective OOS was opened.
No parameter rescue is authorized.

## Family A — cash-close basis fade

Pre-Holm eligible cells: 0
Holm-selected cells: 0

The four horizons did not show a defensible basis-fade edge.

Best gross mean was the 30m cell:
- N=16
- wins=8
- win rate=50.0%
- mean gross=+3.6866 bps
- median=+1.5509 bps
- p=0.598190
- illustrative net after 12 bps=-8.3134 bps

## Family B — cash-close external momentum follow

Pre-Holm eligible cells: 1
Holm-selected cells: 0

5m:
- N=17
- wins=13
- win rate=76.47%
- mean gross=+3.8361 bps
- median=+3.6036 bps
- half means=+5.1011 / +2.7117 bps
- one-sided binomial p=0.024521
- Holm first-step cutoff=0.0125
- illustrative net after 12 bps=-8.1639 bps

The 5m cell is statistically suggestive before multiplicity correction but fails the frozen Holm gate and is too small economically under conservative cost scenarios.

## Scientific classification

`NO_PROMOTION__CASHCLOSE_WEAK_OR_COST_FRAGILE_V03`

This does not authorize selection of the 5m horizon for a new test on already-opened data.

A prospective future study could reuse the exact rule only after a new pre-outcome freeze.

The regular-session intraday lead-lag hypothesis is economically distinct and requires its own source gate and freeze.

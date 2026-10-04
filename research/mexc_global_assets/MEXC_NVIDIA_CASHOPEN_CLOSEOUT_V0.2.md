# MEXC NVIDIA CASH-OPEN DISCOVERY CLOSEOUT V0.2

Date: 2026-10-04
Run: 37226789633
Branch: `mexc-nvidia-cashopen-v0.2-prereg-2026-10-04`

## Provenance

- rule SHA256: `1191037885c4eecfcce32a744c57f03110b62bba6704189a3b103d6db65a6334`
- source binding SHA256: `2e569c608d6f1816a0f6362caf682d7df36b812a8fd51a9b24e7b0dd1146d02e`
- artifact ZIP SHA256: `30d835416fae4f31994ff5609e46becbbf0dff325f628d4ba028bcff337912f5`

18 frozen sessions were available with complete signal data.

## Frozen verdict

`NO_NVIDIA_CASHOPEN_DISCOVERY_CANDIDATE_AT_FROZEN_V02_GATE`

No retrospective OOS was opened.
No parameter rescue is authorized.

## Family A — cash-open basis fade

Pre-Holm eligible cells: 2
Holm-selected cells: 0

15m:
- N=17
- wins=11
- win rate=64.71%
- mean gross=+17.7636 bps
- median gross=+21.0228 bps
- half means=+4.7657 / +29.3173 bps
- one-sided binomial p=0.166153
- illustrative net after 12 bps=+5.7636 bps

30m:
- N=17
- wins=12
- win rate=70.59%
- mean gross=+19.0806 bps
- median gross=+12.7277 bps
- half means=+3.4238 / +32.9978 bps
- one-sided binomial p=0.071732
- Holm first-step cutoff=0.0125
- illustrative net after 12 bps=+7.0806 bps

The 30m cell is directionally/economically interesting but does not pass multiplicity-controlled significance.

## Family B — cash-open external momentum follow

Pre-Holm eligible cells: 2
Holm-selected cells: 0

15m:
- N=18
- wins=11
- win rate=61.11%
- mean gross=+18.4747 bps
- median gross=+13.8843 bps
- half means=+11.9071 / +25.0423 bps
- p=0.240341
- illustrative net after 12 bps=+6.4747 bps

30m:
- N=18
- wins=10
- win rate=55.56%
- mean gross=+18.3549 bps
- median gross=+5.8015 bps
- half means=+10.4589 / +26.2510 bps
- p=0.407265
- illustrative net after 12 bps=+6.3549 bps

## Scientific classification

`DIRECTIONALLY_INTERESTING__STATISTICALLY_NOT_PROMOTED_V02`

The correct action is not to lower gates or choose 15m/30m after seeing outcomes.

Any future continuation of these exact rules must be frozen prospectively before new sessions.

A separate cash-close hypothesis is economically distinct and may be tested only after its own pre-outcome freeze.

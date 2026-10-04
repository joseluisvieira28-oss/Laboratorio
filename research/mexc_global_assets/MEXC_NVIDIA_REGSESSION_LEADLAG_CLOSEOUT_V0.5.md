# MEXC NVIDIA REGULAR-SESSION LEAD-LAG — DISCOVERY CLOSEOUT V0.5

Date: 2026-10-04
Run: 37227465919
Branch: `mexc-nvidia-regsession-leadlag-v0.5-prereg-2026-10-04`

## Provenance

- rule SHA256: `efc5dfa98209b3a03a85c923f6d95195a0f1d1fc1927e6f85a1761804b71479e`
- source binding SHA256: `715d5a565479f1cdc340e35e9d3c0d93226fd402982b407138efa3b18fd62f53`
- discovery artifact ZIP SHA256: `17d714a09661d58d18fe7163c0ddaecdd6791a5bbde8bd86bde55a3d3d5951b4`

17 frozen sessions were used.
Exact common 1-minute observations across downloaded regular-session windows: 4,573.

## Frozen machine verdict

`NVIDIA_REGSESSION_DISCOVERY_CANDIDATES_FOUND`

Pre-Holm eligible cells: 8.
Holm-selected cells: 1.

## Sole multiplicity-controlled survivor

Family:
`MEXC-NVIDIA-REGSESSION-LEADLAG-001`

Frozen cell:
- external shock threshold: 5 bps
- lag-gap threshold: 3 bps
- horizon: 1 minute
- direction: FOLLOW_EXTERNAL_CONSENSUS
- external return: arithmetic mean of Binance and Bitget 1-minute returns

Result:
- N = 92
- wins = 64
- losses/zero = 28
- win rate = 69.5652%
- mean gross signed return = +3.758750 bps
- median gross signed return = +4.297843 bps
- exact one-sided binomial p = 0.0001112506
- Holm rank = 1
- Holm cutoff = 0.00078125
- Holm reject = true

Chronological-third mean gross returns:
- first third = +3.817834 bps
- second third = +4.254712 bps
- third third = +3.205612 bps

Mean absolute external shock:
- 8.923983 bps

Mean absolute lag gap:
- 4.408618 bps

Illustrative mean net after round-trip costs:
- 0 bps cost: +3.758750 bps
- 2 bps cost: +1.758750 bps
- 5 bps cost: -1.241250 bps
- 10 bps cost: -6.241250 bps
- 12 bps cost: -8.241250 bps
- 14 bps cost: -10.241250 bps
- 16 bps cost: -12.241250 bps
- 20 bps cost: -16.241250 bps

## Scientific classification

`NVIDIA_REGSESSION_DISCOVERY_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

This is a genuine discovery survivor under the frozen multiple-testing procedure.

It is not:
- retrospective OOS validation;
- a production edge;
- execution-feasible proof;
- live-trading authority.

V0.5 explicitly did not authorize retrospective OOS.

The sole legitimate next scientific step for this exact cell is prospective forward validation under a new freeze created before future outcomes.

No parameter rescue, alternate threshold selection, alternate horizon selection, private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.

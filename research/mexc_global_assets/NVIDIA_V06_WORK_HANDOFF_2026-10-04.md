# NVIDIA V0.6 WORK HANDOFF — OFFICIAL CONTINUATION SOURCE
Date: 2026-10-04

## Current scientific state

The first multiplicity-controlled NVIDIA discovery survivor exists.

Discovery branch:
`mexc-nvidia-regsession-leadlag-v0.5-prereg-2026-10-04`

Discovery run:
`37227465919`

Discovery verdict:
`NVIDIA_REGSESSION_DISCOVERY_CANDIDATES_FOUND`

Sole Holm survivor:
- family: MEXC-NVIDIA-REGSESSION-LEADLAG-001
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- direction FOLLOW_EXTERNAL_CONSENSUS
- external = mean of Binance NVDAUSDT and Bitget NVDAUSDT 1m returns
- N=92
- wins=64
- win rate=69.5652%
- mean gross=+3.758750 bps
- median gross=+4.297843 bps
- exact p=0.0001112506
- Holm cutoff=0.00078125
- chronological thirds=+3.817834 / +4.254712 / +3.205612 bps

Classification:
`NVIDIA_REGSESSION_DISCOVERY_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

## Forward authority

Current branch:
`mexc-nvidia-regsession-v0.6-forward-freeze-2026-10-04`

Read before any forward evaluation:
- MEXC_NVIDIA_REGSESSION_FORWARD_BINDING_V0.6.json
- MEXC_NVIDIA_REGSESSION_FORWARD_RULE_V0.6.json
- MEXC_NVIDIA_REGSESSION_FORWARD_FREEZE_V0.6.md

Prospective window:
- 2026-10-05 through 2026-10-30
- 20 fixed weekday sessions
- signal window 14:31–18:44 UTC
- no interim promotion
- evaluate only after the full window ends

Forward PASS gate:
- N>=50
- at least 15 distinct signal sessions
- mean gross >0
- median gross >0
- win rate >50%
- both chronological halves mean >0
- exact one-sided binomial p<0.05

No threshold/horizon/direction/source changes are allowed.

## Execution feasibility

Public MEXC contract metadata says NVIDIA_USDT is currently zero-fee on the symbol UI and apiAllowed=true.

However the official API Futures fee authority effective 2026-06-01 says:
- maker 0.06% per side
- taker 0.08% per side
- API fee structure overrides web/app promotional zero fees
- applies to all Futures pairs except Innovation Zone

Therefore current execution classification is:
`EXECUTION_FEE_BLOCKED_STANDARD_MEXC_API`

Fee-only round trip:
- maker-maker 12 bps
- maker-taker 14 bps
- taker-taker 16 bps

Discovery mean gross is only +3.758750 bps.

Also read:
- MEXC_NVIDIA_EXECUTION_FEE_AUTHORITY_V0.1.md
- MEXC_NVIDIA_AUTOMATED_EXECUTION_ROUTE_SURVEY_V0.1.md

No proven automated non-API route currently reproduces the exact frozen multi-venue signal at sub-edge cost.

## Operational rule

Do NOT merge to main.
Do NOT trade.
Do NOT place orders.
Do NOT read account state.
Do NOT use private endpoints or wallets.
Do NOT tune after outcomes.

The final evaluator is:
`research/mexc_global_assets/mexc_nvidia_regsession_forward_v06.py`

The workflow is manual dispatch only because GitHub scheduled workflows run from the default branch and main is intentionally untouched:
`.github/workflows/mexc-nvidia-regsession-v06-forward-final.yml`

Do not execute the final evaluator before 2026-10-31 UTC.

If forward PASS:
classify `FORWARD_VALIDATED_SIGNAL__EXECUTION_FEASIBILITY_SEPARATE`.

If N/session coverage insufficient:
classify `FORWARD_UNDERPOWERED`.

If adequately powered but gates fail:
classify `FORWARD_VALIDATION_FAIL`.

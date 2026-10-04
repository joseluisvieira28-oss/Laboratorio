# MEXC MSTR REGULAR-SESSION V0.2 — CLOSEOUT

Date: 2026-10-04
Run: 37230082471
Branch: `mexc-mstr-regsession-v0.2-prereg-2026-10-04`

## Provenance

Source gate run:
`37229992553`

Source verdict:
`MSTR_REGSESSION_PUBLIC_CORE_SOURCE_PASS`

Source artifact SHA256:
`4ad6f86abb30c1948da6a13d30da06520dac19b4aeef411590671282afd57649`

Discovery artifact SHA256:
`1812e8dc7512769575985d42f197f3ced96160f4b8d2880e240255065d1a76b1`

17 frozen sessions.
Exact common 1-minute observations: 4,573.

## Confirmatory multi-asset transfer

Exact rule already surviving NVIDIA, TESLA and COINBASE:
- shock >=5 bps
- lag gap >=3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS

MSTR result:
- N=801
- signals on 17/17 sessions
- wins=457
- win rate=57.0537%
- mean gross=+3.058257 bps
- median gross=+2.945508 bps
- thirds=+4.654442 / +2.161990 / +2.358339 bps
- p=3.694426e-5
- alpha=0.025
- PASS=true

Classification:
`FOUR_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

The exact 5/3/1m FOLLOW mechanism has now independently survived NVIDIA, TESLA, COINBASE and MSTR.

## Exploratory MSTR grid

Pre-Holm eligible cells:
23

Holm-selected cells:
6

Selected cells:
- 5/3/1m: mean +3.058257 bps
- 5/3/2m: mean +4.477495 bps
- 5/5/1m: mean +4.790739 bps
- 5/5/2m: mean +4.822157 bps
- 5/10/1m: mean +9.574416 bps
- 10/10/1m: mean +7.907293 bps

No Holm-selected MSTR cell exceeds the 12 bps standard API maker-maker fee-only round-trip reference.

## Overall classification

`MSTR_FOUR_ASSET_REPLICATION_SURVIVOR__STANDARD_API_FEE_BLOCKED`

MSTR strengthens the scientific evidence that the regular-session lead-lag mechanism is cross-asset.

It does not improve execution economics enough to displace the COINBASE discovery-selected 20/10/5m candidate.

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.

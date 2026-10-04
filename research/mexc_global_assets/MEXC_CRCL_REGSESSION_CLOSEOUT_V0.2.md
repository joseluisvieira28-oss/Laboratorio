# MEXC CRCL REGULAR-SESSION V0.2 — CLOSEOUT

Date: 2026-10-04
Run: 37230316498
Branch: `mexc-crcl-regsession-v0.2-prereg-2026-10-04`

## Provenance

Source gate run: `37230232528`
Source verdict: `CRCL_REGSESSION_PUBLIC_CORE_SOURCE_PASS`
Source artifact SHA256: `30981deb88541c2a37ad03654f87f0c7daa8ec07b7ad62de0d76edaee46f43f0`
Discovery artifact SHA256: `abc06d8d0e90a8b27f0df98f6e6f37300d2f3c30686ae67b32cd78639eb10e19`

17 frozen sessions.
Exact common 1-minute observations: 4,573.

## Confirmatory transfer

Exact 5/3/1m FOLLOW rule:
- N=932
- signals on 17/17 sessions
- wins=547
- win rate=58.6910%
- mean gross=+3.979436 bps
- median gross=+3.287673 bps
- thirds=+4.395015 / +3.198715 / +4.345914 bps
- p=6.233539e-8
- alpha=0.025
- PASS=true

Classification:
`FIVE_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

The exact mechanism has now independently survived NVIDIA, TESLA, COINBASE, MSTR and CRCL.

## Exploratory grid

Pre-Holm eligible cells: 31.

Holm-selected cells include:
- 5/3/1m: +3.979436 bps
- 5/3/2m: +4.728106 bps
- 5/5/1m: +4.884520 bps
- 5/5/2m: +6.136132 bps
- 5/10/1m: +7.503700 bps
- 5/10/2m: +11.820161 bps
- 10/3/2m: +4.512329 bps
- 10/10/1m: +8.084299 bps
- 10/10/2m: +11.527848 bps
- 20/3/1m: +5.530676 bps

No Holm-selected CRCL cell exceeded the 12 bps standard API maker-maker fee-only reference.

## Overall classification

`CRCL_FIVE_ASSET_REPLICATION_SURVIVOR__STANDARD_API_FEE_BLOCKED`

CRCL strengthens the general cross-asset mechanism but does not displace COINBASE as the current execution-economics leader.

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.

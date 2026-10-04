# MEXC COINBASE REGULAR-SESSION V0.2 — CLOSEOUT

Date: 2026-10-04
Run: 37229633051
Branch: `mexc-coinbase-regsession-v0.2-prereg-2026-10-04`

## Provenance

Source gate run:
`37229510016`

Source verdict:
`COINBASE_REGSESSION_PUBLIC_CORE_SOURCE_PASS`

Source artifact SHA256:
`5899ed4f10c246ca4dbd71fdb5e0ce604432edae0593f79a0218258ce0a25684`

Discovery artifact SHA256:
`e4902f2b8594464597ca4a22d1b9d6b94d1a992fbc3ca4e85366e350c10a4ed4`

17 frozen sessions.
Exact common 1-minute observations: 4,573.

## Confirmatory transfer

Family:
`MEXC-COINBASE-NVDA-TSLA-RULE-TRANSFER-001`

Exact previously replicated rule:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS

Result:
- N=1,101
- signals on 17/17 sessions
- wins=757
- win rate=68.7557%
- mean gross=+5.640436 bps
- median gross=+4.753103 bps
- thirds=+5.933369 / +5.175269 / +5.812672 bps
- p=1.575462e-36
- alpha=0.025
- PASS=true

Classification:
`THREE_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

The exact 5/3/1m FOLLOW mechanism has now independently survived NVIDIA, TESLA and COINBASE.

## Exploratory COINBASE grid

Alpha budget:
`0.025`

Pre-Holm eligible cells:
42

Holm-selected cells:
34

Several selected cells are descriptively above the previously established standard MEXC API fee-only round-trip floor.

### Operationally strongest discovery-selected cell

A post-discovery selection rule is declared explicitly here and is NOT claimed to have been preregistered:

Among Holm-selected cells:
1. require signals on all 17 discovery sessions;
2. require mean gross >16 bps, the taker-taker fee-only round-trip reference;
3. among remaining cells, maximize mean gross minus 16 bps.

This rule leaves two cells:

- shock=20 / gap=10 / horizon=2m
  - N=94
  - mean gross=+17.040345 bps
  - fee-only net after 16 bps=+1.040345 bps

- shock=20 / gap=10 / horizon=5m
  - N=85
  - mean gross=+18.979356 bps
  - fee-only net after 16 bps=+2.979356 bps

The selected forward candidate is therefore:

`shock=20 bps / gap=10 bps / horizon=5m / FOLLOW_EXTERNAL_CONSENSUS`

Discovery result:
- N=85
- wins=65
- win rate=76.4706%
- mean gross=+18.979356 bps
- median gross=+17.936214 bps
- thirds=+14.968761 / +19.530940 / +22.319089 bps
- p=5.149437e-7
- Holm-selected=true
- signals on 17/17 sessions
- illustrative fee-only net:
  - 12 bps: +6.979356 bps
  - 14 bps: +4.979356 bps
  - 16 bps: +2.979356 bps
  - 20 bps: -1.020644 bps

This is a discovery-selected candidate, not a validated executable edge.

## Other high-gross selected cells

The largest Holm-selected gross mean was:
- shock=10 / gap=20 / horizon=5m
- N=27
- wins=24
- win rate=88.8889%
- mean gross=+28.234425 bps
- median=+18.222523 bps
- thirds=+32.361308 / +24.559824 / +27.782144 bps
- p=2.461672e-5
- signals on 11 sessions

It was not chosen for forward because the explicit operational selection rule requires presence on all 17 discovery sessions.

## Overall frozen classification

`COINBASE_THREE_ASSET_REPLICATION_SURVIVOR__FEE_SURVIVING_DISCOVERY_CANDIDATE_FOUND`

Scientific replication is real.
Fee survival is descriptive only.

Spread, slippage, latency, adverse selection, funding and fill probability remain unmodeled.

The selected 20/10/5m cell requires prospective forward validation under a new freeze before any execution claim.

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.

# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-16

## Canonical gate

- Source gate: `DVOL-TS-SOURCE-001`
- Canonical runner: `source_gate_v02_protectedfix.py`
- Canonical GitHub Actions run: `35086850572`
- Job: `104763580228`
- Head SHA: `d8c7db04dc4bdc1a02378f63ba1445209651bd3a`
- Artifact: `btc-dvol-futures-source-v02-35086850572-1`
- Artifact ID: `10442716337`
- Artifact ZIP SHA-256: `28abe28ace7391df98319cef583e40ba880e7ef066e7432e399c0d60cdf7d632`

## Classification

`SOURCE_DATA_INSUFFICIENT_OR_BLOCKED`

This is **NOT `NO_EDGE`** and is not an economic verdict. No basis, convergence return, strategy return, PnL, or 2025/2026 outcome was opened.

## Frozen-gate result

The gate required all four frozen 3-hour probe windows to contain at least one BTCDVOL futures trade, aggregate BTCDVOL trades >= 12, at least one unique BTCDVOL futures instrument per window, core trade-field coverage 100%, auxiliary field coverage >= 90%, and exact instrument metadata success 100%.

Canonical result:

- aggregate BTCDVOL trades = 12 — PASS
- core trade-field coverage = 100% — PASS
- auxiliary trade-field coverage = 100% across observed BTCDVOL records — PASS
- exact metadata = 100% for discovered instruments — PASS
- all four frozen windows non-empty — FAIL
- at least one BTCDVOL instrument in every frozen window — FAIL

Window source counts only:

- 2023-06-14 07:00–10:00 UTC: 5 BTCDVOL trades; `BTCDVOL_USDC-28JUN23`
- 2023-09-13 07:00–10:00 UTC: 2 BTCDVOL trades; `BTCDVOL_USDC-27SEP23`
- 2024-03-13 07:00–10:00 UTC: 5 BTCDVOL trades; `BTCDVOL_USDC-27MAR24`
- 2024-09-11 07:00–10:00 UTC: 0 BTCDVOL trades

## Governance

The exact fixed-window gate is closed as specified. It may not be rescued by changing the empty window, widening its clock window, lowering the aggregate threshold, lowering field-coverage requirements, or replacing the instrument filter under the same source-gate ID.

The prior V0.1 run `35086441402` is VOID / NON-CANONICAL because unbounded current index/delivery requests exposed protected-period timestamps. Its scientific classification is inadmissible. The V0.2 canonical rerun accessed only bounded 2023–2024 historical trade windows and exact archived metadata; `access_2025=false`, `access_2026=false`.

## Authorized next scientific question

A materially different source-feasibility study may test **full contract-life liquidity**, using a new source-gate ID and a prospective authority frozen before acquisition. This is not a rescue of `DVOL-TS-SOURCE-001`; it asks whether the monthly DVOL futures population, across complete listed lifetimes rather than four intraday snapshots, contains enough independent contracts and active trading days to justify a later Discovery design.

No Discovery MVE is authorized by this closeout.

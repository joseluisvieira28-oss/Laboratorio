# DEFI-LIQUIDATION-SHOCK-001 — KAMINO SOURCE REMEDIATION IMPLEMENTATION FREEZE V0.2

Date: 2026-09-18  
Branch: `defi-liquidation-shock-v0.1`  
Posture: `SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

## Purpose

Freeze the corrected Kamino source-remediation path before any new corrected BigQuery candidate result is opened.

This does not authorize market prices, returns, PnL, future direction, tuning, live trading, exchange mutation, wallets, alerts/webhooks or merge to main.

## Historical error preserved

Retired wrong discriminator:

`b1479acce2854a37`

Correct discriminator:

`b1479abce2854a37`

The earlier wrong-prefix zero-candidate observations remain preserved as audit history but are invalid for Kamino inference.

## Frozen V0.2 implementation

- `source/protocol_registry_v0_2.json`
  - blob: `5e49dae7c4e3bc7b504dfe12b4f0d1d61133e0e9`
- `source/collect_protocol_history_v0_2.py`
  - blob: `c2cd49b17ab3faccc4d332b48e80b4a778746415`
- `source/BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_2.sql`
  - blob: `b933b986ffd038be286ad6abf0b02fc3994ac33f`
- `source/adjudicate_kamino_corrected_smoke_v0_2.py`
  - blob: `1989b2e7212d32485a2a1a55b52a1e015dcf1bc7`
- `source/test_source_registry_v0_2.py`
  - blob: `32eee91e1bb8ce9ae0d47620d78b0be1a31b85ef`
- `source/test_bigquery_verifier_synthetic_v0_2.py`
  - blob: `23d83cefd60d26da53c77a42dfd7174ae44ecc7a`
- `source/test_adjudicate_kamino_corrected_smoke_v0_2.py`
  - blob: `cc1244347f1d523e69eba65c1cea694ec9d80f45`
- `.github/workflows/defi-liquidation-source-v02-synthetic-qa.yml`
  - blob: `a9f35e53d64b2f0c1f4a03fd121f1698d81a3072`

Synthetic QA:
- run: `35349082272`
- conclusion: **SUCCESS**
- market prices opened: false
- returns computed: false
- PnL computed: false

## Frozen next execution

Run only:

`source/BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_2.sql`

Window:

`[2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)`

Before execution:
- inspect estimated BigQuery bytes;
- hard stop if >100 GB;
- do not alter date/program/discriminator after seeing any result.

Export the result unchanged as CSV.

Then run:

`adjudicate_kamino_corrected_smoke_v0_2.py`

The adjudicator must route rows into:
- successful reference candidates requiring RAW validation;
- failed attempts not realized;
- source anomalies fail-closed.

Successful rows are emitted directly in the schema required by the existing RAW verifier.

## Scientific routing

If corrected Kamino smoke test returns successful reference candidates:
- perform RAW archival verification;
- do not count them as authoritative realized events until RAW and historical interval applicability pass.

If it returns failed attempts only:
- retain them as attempts;
- do not count realized forced flow;
- this is not NO_EDGE.

If it returns zero corrected candidates:
- the 2024-12-15 smoke day has no corrected reference candidate;
- this is not proof of no Kamino liquidation history;
- continue source-only first-success boundary search prospectively.

If any source anomaly occurs:
- fail closed;
- no SOURCE_DATA_PASS.

## Current state

`SOURCE_GATE_ACTIVE`

`SOURCE_DATA_PASS = false`

No economic outcome access is authorized.

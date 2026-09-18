# DEFI-LIQUIDATION-SHOCK-001 — SOURCE PREFLIGHT V0.1 SUPERSESSION NOTICE

Date: 2026-09-18

The workflow `.github/workflows/defi-liquidation-source-preflight-v01.yml` is historical audit infrastructure.

It is superseded for future source execution by:

- `.github/workflows/defi-liquidation-source-v02-synthetic-qa.yml`
- `source/protocol_registry_v0_2.json`
- `source/collect_protocol_history_v0_2.py`
- `source/BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_2.sql`
- `source/adjudicate_kamino_corrected_smoke_v0_2.py`
- `KAMINO_SOURCE_REMEDIATION_IMPLEMENTATION_FREEZE_V0.2.md`
- `MANIFEST_V0.4.json`

Reason:

V0.1 contains the retired Kamino discriminator `b1479acce2854a37` in its historical registry/test path. The corrected value is `b1479abce2854a37`.

Historical V0.1 workflow runs remain valid evidence of what the V0.1 implementation tested at the time, but a V0.1 green check MUST NOT be interpreted as validation of the corrected Kamino path.

Future source-route CI authority is V0.2, synthetic QA run `35349082272` = SUCCESS.

This supersession changes no market result and opens no outcomes.

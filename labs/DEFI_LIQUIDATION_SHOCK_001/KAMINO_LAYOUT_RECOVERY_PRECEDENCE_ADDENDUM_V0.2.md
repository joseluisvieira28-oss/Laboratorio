# DEFI-LIQUIDATION-SHOCK-001 — KAMINO LAYOUT RECOVERY PRECEDENCE ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Reason

Original V0.1 Kamino population enrichment assumed one exact 16-account layout across the full interval.
Official Kamino source proves Release 1.6.0 changed the fixed layout to 20 accounts plus remaining_accounts.

Therefore V0.1 receipts are authoritative only where they PASS under the legacy layout.
For the mixed/new-layout period, V0.2 recovery receipts are mandatory.

## Frozen partition precedence

### Kamino field + unit metadata

Original V0.1 receipts are selected for:
- kamino-202311
- kamino-202312
- kamino-202401
- kamino-202402
- kamino-202403
- kamino-202404
- kamino-202405

V0.2 historical-layout recovery receipts are selected for:
- kamino-202406
- kamino-202407
- kamino-202408
- kamino-202409
- kamino-202410
- kamino-202411
- kamino-202412

An original V0.1 receipt for any recovery-selected partition is explicitly superseded and MUST NOT participate in aggregate errors/counts.

### Save11

All six Save11 partitions remain V0.1:
- save11-202407 through save11-202412

## Selection independence

This precedence is selected from protocol source history and the known ABI change, not from PASS/FAIL outcome.

V0.2 cannot rescue a mismatch in canonical event identities:
- missing must remain 0
- extra must remain 0
- duplicates must remain 0
- source semantic/layout conflicts must remain 0

## Final receipts

Field:
KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS

Unit metadata:
KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS

Both V0.2 aggregate receipts must preserve exact population totals:
- Kamino 60,699
- Save11 13,300

## Firewall

prices=false
returns=false
pnl=false
economic_outcomes=false
token_amounts=false
protected_2025_2026_market_outcomes=false
post_outcome_tuning=false
live_trading=false
merge_main=false

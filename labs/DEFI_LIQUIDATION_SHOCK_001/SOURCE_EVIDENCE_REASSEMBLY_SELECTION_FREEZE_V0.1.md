# DEFI-LIQUIDATION-SHOCK-001 — SOURCE EVIDENCE REASSEMBLY SELECTION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN TECHNICAL EVIDENCE-SELECTION RULE / SOURCE-ONLY / OUTCOME-BLIND

## Problem

Long monthly SQD jobs can be terminated by the GitHub Actions runtime ceiling after producing partial transport files. Complete replacement shards are then executed for the exact cancelled date ranges.

A final authority reassembly MUST NOT treat a cancelled/incomplete monthly artifact as a scientific contradiction when an exact, complete replacement exists. It also MUST NOT silently merge partial evidence with replacement evidence.

## Frozen admissibility rule

### Drift MANIFEST evidence
Admit a Drift evidence directory only when its `MANIFEST.json` has:
- `protocol == "drift"`
- `classification == "PARTITION_COMPLETE"`

For each admitted manifest:
- verify every declared chunk file exists;
- verify every declared SHA256;
- require each chunk `classification == "SOURCE_CHUNK_PASS"`;
- require `stream_complete == true`;
- require `anomaly_count == 0`.

A manifest not classified `PARTITION_COMPLETE` is:
`NON_AUTHORITATIVE_PARTIAL_TRANSPORT_EVIDENCE_EXCLUDED`

Its chunks MUST NOT enter the reconstructed census.

### Replacement rule
A cancelled/incomplete original date range is considered repaired only if admitted complete evidence from recovery shards reconstructs the exact scientific interval with:
- no gap;
- no overlap;
- no duplicate slice;
- no hash conflict;
- no anomaly.

No preference is given merely because an artifact is “original” or “recovery”; admissibility depends only on complete frozen evidence plus exact chronology.

### Fail-closed
After excluding non-authoritative partials, any remaining scientific gap or overlap blocks final source authority.

This correction does not alter:
- protocol/program identities;
- discriminators/tags;
- source windows;
- success/failure semantics;
- event population;
- sampling;
- RAW authority;
- any economic rule.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false

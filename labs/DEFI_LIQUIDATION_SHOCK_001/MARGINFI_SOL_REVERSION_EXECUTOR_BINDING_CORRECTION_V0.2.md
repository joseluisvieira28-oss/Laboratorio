# DLS — MARGINFI SOL REVERSION EXECUTOR BINDING CORRECTION V0.2

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: OPERATIONAL CORRECTION BEFORE MARKET OUTCOMES

Parent scientific freeze:
MARGINFI_SOL_POST_CASCADE_REVERSION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md

Canonical source binding:
MARGINFI_SOL_POST_CASCADE_REVERSION_SOURCE_BINDING_ADDENDUM_V0.2.md

Observed operational failure:
run 36611871210 used run_marginfi_sol_post_cascade_reversion_dev_v0_1.py.
That executor expects the broad-source receipt filenames:
- MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_RECEIPT_V0.1.json
- MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_ROWS_V0.1.ndjson

The canonical authorized source prerequisite is the SOL-only V0.2 artifact ID 11053637340,
whose filenames are:
- MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json
- MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson

Run 36611871210 therefore terminated:
MARGINFI_SOL_REVERSION_DEVELOPMENT_SOURCE_BLOCKED
stage=source_authority
market data unopened.

Correction:
use existing run_marginfi_sol_post_cascade_reversion_dev_v0_2.py, which differs only in binding to the
authorized SOL-only receipt/rows and preserves all return-side rules unchanged.

Run 36612031985 (V0.5 Windows) was queued using the same incorrect V0.1 executor and is superseded before
execution for scientific adjudication. It must not be treated as canonical even if it later runs.

Canonical next executor:
run_marginfi_sol_post_cascade_reversion_dev_v0_2.py

No changes to:
cascade linkage, side, entry, hold, costs, funding firewall, folds, bootstrap, gates or future boundaries.

Firewall:
market_outcomes_opened=false
post_outcome_tuning=false
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false

# MARGINFI ORCA IMPACT V0.1 — JUL-SEP OUTCOME CONTAMINATION QUARANTINE

Date: 2026-10-01
Branch: dls-marginfi-route-migration-v01

A pre-launch implementation audit found two defects in the prepared Jul-Sep Development executor:
- SHORT return/execution signs were inverted;
- PREOUTCOME_READY was not explicitly bound into the workflow.

Corrections were committed without inspecting any Development outcome:
- 13601ba96b54eb9502491951e92e8273c21fb833
- 9f670e4c2909332eee3a34d74511659c34a7e036
- 28d1d741ff398e78814ead540a8396958cf48616

However, workflow run 36816846032 had already been triggered at head
fcfdaf9badff8aa1cd762d017ff6445cbd73a2ce before those corrections and completed while the audit was
in progress.

At quarantine time, its scientific receipt, ledger, metrics, gross return, net return, folds and
bootstrap results had NOT been inspected.

Decision:
- DO NOT inspect or use run 36816846032 for scientific inference.
- Jul-Sep 2024 is quarantined for this family because market outcomes were mechanically opened by an
  implementation that did not match the frozen SHORT rule.
- Do not use Jul-Sep to tune, select, reverse, filter or modify the corrected rule.
- Any corrected market test must use an untouched period with a newly frozen source authority and
  pre-outcome gate.

The corrected SHORT implementation itself was derived solely from the original written freeze and
standard execution sign logic, not from observed outcomes.

Next clean candidate:
Oct-Dec 2024, subject to source authority and a new pre-outcome sample gate before any market outcome.

2025/2026 remain protected.

Firewall:
inspect_run_36816846032_outcomes=false
jul_sep_scientific_adjudication=false
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

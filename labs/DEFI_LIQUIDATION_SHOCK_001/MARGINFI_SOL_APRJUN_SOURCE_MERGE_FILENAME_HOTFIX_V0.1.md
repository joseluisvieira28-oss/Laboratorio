# DLS — MARGINFI SOL APR-JUN SOURCE MERGE FILENAME HOTFIX V0.1

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01
Status: OPERATIONAL CORRECTION / SOURCE-ONLY

Canonical monthly source run:
36686194844

Immutable monthly artifacts:
- April: artifact 11084591611, dls-marginfi-sol-aprjun-source-202404-v01
- May: artifact 11083783717, dls-marginfi-sol-aprjun-source-202405-v01
- June: artifact 11084090889, dls-marginfi-sol-aprjun-source-202406-v01

Observed merge failure:
the merge script searched for MARGINFI_SOL_FEBMAR_POPULATION_<month>_V0.1.ndjson instead of the
actual Apr-Jun filename MARGINFI_SOL_APRJUN_POPULATION_<month>_V0.1.ndjson.

This produced file_count errors before any global source adjudication.

Correction:
change only that filename prefix in the merge reader.
No monthly artifact, source identity, route semantics, direction semantics, threshold, or market rule changes.

No Apr-Jun market outcome has been opened.

Firewall:
prices=false
returns=false
pnl=false
apr_jun_market_outcomes_opened=false
jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

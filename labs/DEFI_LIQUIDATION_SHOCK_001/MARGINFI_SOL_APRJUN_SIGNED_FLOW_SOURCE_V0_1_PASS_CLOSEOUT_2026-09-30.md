# MARGINFI SOL APR-JUN SIGNED-FLOW SOURCE V0.1 — PASS CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01

Canonical monthly source run:
36686194844

Canonical merge-only hotfix run:
36688264174

Canonical terminal source artifact:
dls-marginfi-sol-aprjun-signed-flow-source-v01-hotfix
artifact ID 11083994743
digest sha256:1d71290fff88c66423e46f1a4b17cb82e58d815feaf47de5ef30c1870103def5

Classification:
MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_PASS

Global source result:
- SOL population: 10,164
- Jupiter route members: 2,893
- source-complete: 2,888
- source completeness: 0.9982716902868994
- direction proven: 2,888
- direction ambiguous: 0
- contradictions: 0
- population duplicates: 0
- route duplicates: 0
- global errors: 0

Incomplete route evidence:
- 5 route members were SOURCE_EVIDENCE_INCOMPLETE due duplicate_swap_pair
- these are excluded from DIRECTION_PROVEN eligibility by the frozen rule
- they do not breach the >=95% source-complete gate

Monthly immutable source artifacts:
- April: 11084591611
- May: 11083783717
- June: 11084090889

The original merge in run 36686194844 was operationally blocked only because the merge reader looked
for a legacy FEBMAR population filename. The monthly artifacts were not changed.
The merge-only hotfix changed only that filename and returned PASS.

Consequence:
Apr-Jun Development for DLS-MARGINFI-SOL-FLOW-TURNOVER-IMPACT-001 is source-authorized, conditional on
the already-frozen feature calibration PASS.

Firewall:
apr_jun_market_outcomes_opened=false
jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

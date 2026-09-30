# DLS — MARGINFI SOL FLOW-TURNOVER DEVELOPMENT SOURCE-BINDING CORRECTION V0.1

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01
Status: OPERATIONAL CORRECTION BEFORE APR-JUN MARKET OUTCOMES

Parent freeze:
MARGINFI_SOL_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

Canonical feature calibration:
- run 36686002313
- artifact ID 11083738178
- classification MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS
- frozen Q90 = 1.0307255992127644e-05

Canonical Apr-Jun source authority:
- merge-hotfix run 36688264174
- artifact ID 11083994743
- digest sha256:1d71290fff88c66423e46f1a4b17cb82e58d815feaf47de5ef30c1870103def5
- classification MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_PASS

Observed operational failure:
run 36688377641 downloaded the terminal artifact by name from original monthly source run 36686194844.
That artifact preserved the pre-hotfix blocked merge state.

The Development executor stopped at:
MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_SOURCE_BLOCKED
stage=source_authority

No Apr-Jun market data, returns or PnL were opened by that run.

Correction:
bind the Development workflow by exact canonical source artifact ID 11083994743 from run 36688264174.

No scientific field changes:
- Q90 unchanged
- feature unchanged
- 5-minute cascade unchanged
- 5-minute pre-entry turnover denominator unchanged
- side SHORT unchanged
- hold 1 minute unchanged
- costs unchanged
- folds unchanged
- bootstrap unchanged
- gates unchanged
- future boundary unchanged

Firewall:
apr_jun_market_outcomes_opened=false_before_corrected_run
jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false

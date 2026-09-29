# DLS — MARGINFI SOL REVERSION DEVELOPMENT RUNNER PORTABILITY ADDENDUM V0.1

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN OPERATIONAL ADDENDUM BEFORE FEB-MAR MARKET OUTCOMES

Parent:
- MARGINFI_SOL_POST_CASCADE_REVERSION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md
- MARGINFI_SOL_POST_CASCADE_REVERSION_SOURCE_BINDING_ADDENDUM_V0.2.md

Reason:
Linux GitHub-hosted runners are saturated by source-only audit/fallback jobs after the canonical SOL
Feb-Mar source prerequisite already reached PASS.

This addendum authorizes execution of the exact same frozen Python Development executor on a
GitHub-hosted Windows runner solely to avoid runner-pool queueing.

Unchanged:
- exact canonical source artifact ID 11053637340;
- executor source file and commit contents;
- SOL-only source events;
- 5-minute source-only cascade linkage;
- LONG side;
- first full minute after cascade end entry;
- 15-minute hold;
- funding exclusion;
- Binance public checksum-verified 1m market-data authority;
- 8 bps taker fee/side;
- 2 bps nominal slippage/side;
- stress 5 bps slippage/side;
- temporal folds;
- bootstrap seed and replicates;
- all Development gates;
- future boundaries and firewalls.

Cross-platform reproducibility requirement:
If the Linux run later completes too, its receipt/ledger hashes or numerical results must reconcile
within ordinary floating-point serialization tolerance. Any material discrepancy fails closed.

The first successfully completed valid runner may adjudicate Development, subject to that later
cross-check.

No market outcome has been opened before this addendum.

Firewall:
post_outcome_tuning=false
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false

# LICP-001 operational recovery — 2026-10-08

Science unchanged. No economic verdict declared.

Verified baseline run 37311668666: FORWARD_OBSERVATION, live_trading=false, config LICP-001-TRIGGER-V0.1, SHA256 f86534bdb2d7692fa02773e0545d8cb9d204a8ffa572263bbb4b25d3dfe80907. Source acknowledgements true; malformed, crossed BBO, version regressions and OI errors zero. Eight records; six independent BTC_CONFIRMED on UTC 2026-10-05. Frozen aggregator returns FORWARD_INSUFFICIENT, 6/20 and 1/3 dates.

V03 run 37733650222 attempt 1 incorrectly rejected the entire baseline because legacy ALT_SECOND_WAVE records 1 and 3 lack ignition-derived IDs. It reported LEDGER_OK despite a rejected mandatory receipt and zero credited baseline episodes. That aggregate is not authoritative evidence of zero episodes.

Operational fix afac9e915e8f30f0eb6e798b3cec9b902d9d3ed5 reconstructs secondary-only metadata IDs from canonical content, retains all original secondary/primary outcomes, preserves primary ignition-based identity, and fails closed when any receipt is rejected. Baseline replay accepts all eight records without conflict; unchanged frozen aggregator credits the same six primary episodes. Existing ledger self-test passed locally.

Continuation commit 59ea0c5c0455c5c572b3d81a5cf08772195e2c94 launched new V03 run 37746822222, pending at verification. Run 37733650222 attempt 2 was accepted by GitHub and queued, but uses old code; retain its immutable current receipt and revalidate with corrected ledger. Preserve prior attempts/artifacts; do not trust its old baseline-rejecting aggregate. No integration execution rejection occurred in this recovery.

Frozen thresholds, source rules, target, horizon, direction, costs, cooldown and gates unchanged. No orders, exchange authentication, wallets, capital or main merge.

# BREAKOUT-ACCEPTANCE-001 — RED TEAM PLAN V0.1

Date: 2026-09-27
Status: FROZEN PRE-OUTCOME

Mandatory attacks once sufficient forward evidence exists:
1. LOOKAHEAD / BAR-CLOSE AUDIT — prove range, ATR and volume thresholds use strictly prior completed bars.
2. ENTRY-TIMING AUDIT — acceptance is known only after the second acceptance close; test whether next-open observation is operationally observable without hindsight.
3. RANDOM-TIME PLACEBO — matched prospective random timestamps with the same horizon.
4. TIME-SHIFT PLACEBO — shift the accepted-break state by -1/+1 and -3/+3 completed 4H bars.
5. VOLUME-ONLY PLACEBO — participation alone must not substitute for acceptance.
6. BREAKOUT-ONLY PLACEBO — raw breakout alone must not substitute for the joint state.
7. ACCEPTANCE-ONLY PLACEBO — two closes above range without high-volume breakout must not be treated as the same mechanism.
8. REMOVE-BEST-1 / REMOVE-BEST-3 / REMOVE-BEST-5.
9. SYMBOL CONCENTRATION — report each symbol separately and leave-one-symbol-out.
10. PERIOD STABILITY — chronological splits when maturity permits.
11. COST STRESS X2 / X3 as diagnostics in addition to frozen BASE/STRESS.
12. OVERLAP / CLUSTER ATTACK — verify ignored same-symbol overlaps do not manufacture independence.
13. COMMON-CRYPTO-BETA — compare cross-sectional breadth and market-wide breakout clustering.
14. EXECUTION REALISM — distinguish theoretical next-open measurement from any executable live entry.
15. BOUNDARY ATTACK — zero pre-2026-09-28 entries.

Fatal process failures: lookahead, boundary breach, protected PBR access, post-outcome scientific rule edits, fabricated/missing source evidence.

A Red challenge is not automatically a falsification. Report SURVIVES / CHALLENGED / FALSIFIED / BLOCKED.

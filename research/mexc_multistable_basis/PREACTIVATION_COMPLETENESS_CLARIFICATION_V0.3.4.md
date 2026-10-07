# MEXC-MULTI-STABLE-BASIS-001 — PRE-ACTIVATION COMPLETENESS IMPLEMENTATION CLARIFICATION V0.3.4

Date: 2026-10-07
Status: FROZEN BEFORE FIRST AUTHORIZED FORWARD SIGNAL CLOSE

Authority timing:
- threshold receipt commit: 2026-10-07T15:44:50Z
- first trigger run launched: 37647073714
- that run was configured to begin at 2026-10-07T16:00:00Z
- this clarification is committed before 16:00:00Z and before any authorized economic signal close.

Problem:
The V0.3 freeze requires >=95% complete timing-qualified executable evidence for pre-cooldown triggered underlying trades, but the first collector implementation did not capture entry/exit books for signals suppressed by the 15-minute cooldown.

Frozen implementation:
- execution-completeness denominator = all FUNDING-ELIGIBLE raw underlying triggers before cooldown;
- funding-window-ineligible triggers are excluded by the already-frozen deterministic funding rule and are not trades;
- cooldown-suppressed funding-eligible triggers MUST still receive shadow entry/exit executable-book capture;
- cooldown-suppressed observations are NEVER included in economic event-basket returns;
- only non-suppressed events enter the >=40 event economic sample.

Run 37647073714 and trigger commit 33f2c9aaf813820d78117bb762bfc782d41ade26 are designated:
`PRE_ACTIVATION_SUPERSEDED__NOT_ADMISSIBLE`

No output from that run may enter V0.3 science, even if it completes successfully.

A new activation trigger must begin strictly after this clarification commit. No backfill of the superseded interval.

No threshold, direction, horizon, cooldown, fee, asset, notional or economic gate changes.

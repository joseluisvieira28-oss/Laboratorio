# REACTIVE-SHOCK-SCALP-005 — SOURCE REMEDIATION V0.1

Date: 2026-09-26
Status: TECHNICAL SOURCE REMEDIATION ONLY — SCIENCE UNCHANGED

The first CI run failed before market outcomes because BLS returned HTTP 403 to the GitHub Actions runner.

A second implementation defect was identified before rerun: the code did not enforce the already-frozen rule that selected events must occur on/after Bybit historical L2 availability (2023-01-18).

Remediation:
- persist an official-BLS-derived 2023 selected-event manifest in the branch;
- retain official BLS URLs as provenance;
- enforce event_date >= 2023-01-18;
- validate 8 selected events = 4 CPI + 4 NFP + one of each per quarter;
- compute 08:30 America/New_York -> UTC at runtime using zoneinfo.

Frozen scientific rules are unchanged:
- no consensus;
- same event-selection rule;
- same W1/W2/W5 observation windows;
- same four reactive variants;
- same future horizons;
- same fee overlays;
- same survival rule;
- 2025 OOS locked;
- 2026 holdout locked.

No market outcome was opened by the failed run.

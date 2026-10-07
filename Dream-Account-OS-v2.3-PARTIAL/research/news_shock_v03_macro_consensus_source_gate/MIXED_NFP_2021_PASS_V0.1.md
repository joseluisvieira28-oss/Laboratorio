# News Shock Lab V0.3 — Mixed NFP 2021 Source Census PASS

Date: 2026-10-07

**Verdict: MIXED_NFP_SOURCE_CENSUS_PASS**

The prospectively frozen mixed-source NFP design completed **12/12** frozen 2021 Employment Situation events against a gate of **>=10/12**.

All four required consensus fields were recovered for every event:
- NFP change
- unemployment rate
- average hourly earnings MoM
- average hourly earnings YoY

TeleTrade supplied the first three fields under the frozen same-day pre-T0 GMT rule. The Baker Group supplied AHE YoY from issue-specific pre-T0 PDFs.

The earlier 0/12 runs are not scientific coverage failures: they were invalidated by confirmed parser defects and preserved as technical history. The final rerun corrected only parsing/transport mechanics; source families, fields, event universe, fallback rule and gate were unchanged.

Canonical run: `37682361249`  
Artifact: `11510330785`  
Artifact SHA256: `a5488e0951fc9ed8b19644dd85b31d63c3d0301fbf2f743086aa8a6129ff483d`

No market outcome was opened.

**NFP source gate is closed PASS.**

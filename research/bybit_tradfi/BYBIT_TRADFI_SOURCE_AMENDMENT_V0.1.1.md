# BYBIT TRADFI SOURCE GATE V0.1.1 — TECHNICAL AMENDMENT

Date: 2026-10-05

The first source-only run used Bybit V5 category=linear with exact symbols but omitted the documented `symbolType=stock` filter. The Bybit V5 changelog explicitly added `stock` as a linear symbolType in April 2026.

This amendment changes only transport discovery:
- adds `symbolType=stock` to Get Instruments Info;
- records retCode/retMsg/symbolType for audit.

It does NOT change:
- candidate universe;
- burned verification date;
- verification window;
- source thresholds;
- outcome rule;
- any scientific gate.

No Bybit target outcomes have been opened.

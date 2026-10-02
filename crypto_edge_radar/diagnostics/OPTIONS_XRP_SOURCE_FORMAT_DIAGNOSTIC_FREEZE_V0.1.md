# OPTIONS XRP — SOURCE FORMAT DIAGNOSTIC FREEZE V0.1

Date: 2026-10-02
Status: OUTCOME-BLIND TECHNICAL DIAGNOSTIC

Purpose: explain the high instrument-name parse failure observed after the corrected USDC source routing.

Authorized source bytes:
- Deribit historical public trade stream only
- currency=USDC
- kind=option
- one UTC day: 2024-03-12
- retain only rows whose instrument_name starts with XRP_USDC-

The diagnostic may emit:
- unique instrument names;
- split tokens / character representation;
- structural counts.

Forbidden:
- skew;
- signal;
- forward return;
- underlying outcome price series;
- PnL;
- ranking;
- 2025+ data.

This diagnostic can justify only a technical parser amendment. It cannot alter scientific rules or produce an edge verdict.

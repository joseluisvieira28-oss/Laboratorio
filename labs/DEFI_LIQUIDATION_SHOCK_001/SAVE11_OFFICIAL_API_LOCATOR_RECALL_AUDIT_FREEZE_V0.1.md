# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 OFFICIAL API LOCATOR RECALL AUDIT FREEZE V0.1

Date: 2026-09-23
Status: FROZEN BEFORE RAW CENSUS COMPLETION / SOURCE-ONLY / OUTCOME-BLIND

Purpose:
Calibrate the Save/Solend official `/history-v2/liquidation-attempts` API as a SECONDARY locator against the independently frozen and exhaustively RAW-adjudicated Save 0x11 first census chunk.

Frozen window:
`[2024-07-19T19:30:52Z, 2024-07-20T00:00:00Z)`

Authoritative reference set:
union of:
- `SAVE11_EVENT_CENSUS_EVENTS_V0.1.jsonl`
- `SAVE11_EVENT_CENSUS_FAILED_ATTEMPTS_V0.1.jsonl`

Only exact program + native tag `0x11` RAW matches from the completed census enter the authoritative reference set.

Secondary locator set:
`SAVE11_OFFICIAL_API_LOCATOR_V0.1.json`, retaining only signature/slot/success/timestamp.

## Frozen metrics

- `raw_reference_signatures`
- `locator_signatures`
- `raw_found_in_locator`
- `raw_missing_from_locator`
- `locator_recall = raw_found_in_locator / raw_reference_signatures`
- exact boundary signature presence
- slot/timestamp agreement for matched rows

No precision claim is made because the official API may legitimately include other Save/Solend liquidation classes. Extra locator signatures are NOT false positives unless RAW class adjudication says so.

## PASS condition

`SAVE11_OFFICIAL_API_LOCATOR_RECALL_CALIBRATION_PASS` requires:
1. completed canonical Save11 first-chunk receipt is `SAVE11_EVENT_CENSUS_FIRST_CHUNK_PASS`;
2. locator receipt is `SAVE11_OFFICIAL_API_LOCATOR_CHUNK_PASS`;
3. every authoritative RAW Save11 event/failed-attempt signature is present in the locator;
4. every matched signature has exact slot and timestamp agreement;
5. frozen first-success boundary is included.

Any missing/mismatched authoritative signature:
`SAVE11_OFFICIAL_API_LOCATOR_RECALL_CALIBRATION_FAIL`.

## Interpretation

Even PASS does NOT authorize the API as a complete historical authority or allow replacement of exhaustive census coverage across the full 2024 window.

It only proves 100% locator recall for this one prospectively frozen calibration chunk. Any expanded operational use requires a separately frozen multi-window completeness policy.

No prices, amounts, balances, returns, PnL, direction, market outcomes, threshold tuning, live trading, orders, wallets, exchange mutation, paid access, account creation or main merge.

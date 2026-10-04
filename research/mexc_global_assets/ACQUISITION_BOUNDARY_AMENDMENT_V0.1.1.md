# GLOBAL-ASSET-INDEX-BASIS-001 — ACQUISITION BOUNDARY AMENDMENT V0.1.1

Date: 2026-10-04
Status: PRE-SCORING TECHNICAL CORRECTION / SCIENTIFIC RULE UNCHANGED

## Incident

Runs 37191038079 and 37191173277 did not produce a scientific closeout.

Run 37191038079 stopped before historical acquisition due an overly strict exclusive-end guard.

Run 37191173277 passed the source gate and began acquisition, but stopped before scoring when the raw 23:55 UTC Min5 bucket mapped to observable time 00:00 UTC on 2026-09-01.

No discovery matrix, Holm selection, OOS result, survivor, PnL verdict or directional performance statistic was produced before this amendment.

## Root cause

The frozen model treats a Min5 bucket with raw start `s` as observable only at `s + 300 seconds`.

For an exclusive observable-time boundary of:

`2026-09-01T00:00:00Z`

the raw bucket starting at 2026-08-31T23:55:00Z is NOT eligible because it becomes observable exactly at the protected boundary.

Therefore the latest permissible raw bucket start is:

`2026-08-31T23:50:00Z`

which becomes observable at 23:55:00Z.

MEXC documentation states that K-line `start` and `end` are timestamps in seconds and that a request may return up to 2000 rows.

## Technical correction

The acquisition layer now:

1. permits a function-level exclusive end equal to the hard boundary;
2. computes `last_raw_start = end - 2*STEP`;
3. never requests a raw bucket later than that value;
4. checks the returned raw timestamp against the exact request range before parsing the associated price;
5. fails closed if the API returns any timestamp outside the requested raw interval;
6. fails closed if any mapped observable timestamp reaches the protected boundary.

## Scientific invariants unchanged

UNCHANGED:
- assets;
- FADE_BASIS_ONLY direction;
- basis formula;
- 5/10/20/40 bps thresholds;
- 5/15/30/60 minute horizons;
- non-overlap rule;
- discovery/OOS windows;
- NVIDIA contamination firewall;
- discovery gate;
- Holm-Bonferroni family-wise alpha 0.05;
- OOS gate;
- illustrative cost reporting;
- promotion ceiling;
- no live trading / no private endpoint / no account read / no mutation.

This is a transport/boundary correction, not a parameter rescue.

## Protected-period status

The failed runner parsed no performance statistic from September 2026 and emitted no September price value to logs or artifacts.

V0.1.1 nevertheless starts on a distinct branch and requires a fresh source gate and a fresh immutable run receipt.

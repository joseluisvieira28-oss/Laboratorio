# TV Sensor Anomaly Sentinel V0.1

Operational integrity sentinel for `TV-FOOTPRINT-CALIBRATION-001 / MM-V1`.

It does **not** search for edge, compute PnL, open outcomes, or change calibration thresholds.

## Purpose

Detect silent sensor/schema drift before it contaminates the calibration corpus.

States:

- `PASS`: all observed unique receipts satisfy the frozen integrity checks.
- `DEGRADED`: transport or lower-timeframe completeness is imperfect; affected bars are not calibration-eligible.
- `FAIL_CLOSED`: schema, identity, hash, arithmetic, timestamp, or footprint-structure integrity failed.

## Frozen invariants

- exact lab/sensor/symbol/timeframe identity;
- exact payload schema fingerprint;
- payload SHA256 must recompute exactly;
- exact 5-minute UTC alignment;
- buy + sell volume ~= total volume;
- buy - sell volume ~= delta;
- delta / total ~= delta_pct;
- VAL <= POC <= VAH;
- imbalance counts cannot exceed footprint rows;
- path efficiency in [0,1];
- LTF intrabar count expected to equal 5 on a complete bar;
- same evidence key with different payload hash is a hard conflict;
- no data repair, interpolation, backfill, or imputation.

The Sentinel has **no calibration authority and no trading authority**.

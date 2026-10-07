# MEXC-MULTI-STABLE-BASIS-001 — FORWARD SOURCE COMPLETENESS AMENDMENT V0.3.3

Date: 2026-10-07
Status: PRE-OUTCOME DATA-QUALITY HARDENING

No prospective economic outcome has been opened.

Reason:
A missing scan minute cannot be safely treated as a no-signal minute because the frozen predictor is unknown at that timestamp.

Additional frozen gate:
- every scheduled collector segment records the expected signal-close timestamps;
- a scan minute is COMPLETE only when all six perpetual closed candles plus USDCUSDT and USD1USDT exact closed candles are present;
- no forward fill/interpolation/nearest-neighbor/backfill;
- final V0.3 adjudication requires >=99% complete scheduled scan minutes across the prospective epoch used for adjudication;
- missing scan minutes are explicit source gaps and never inferred as no-signal.

If the economic sample count is otherwise sufficient but scheduled scan completeness is <99%:
`BLOCKED_DATA_QUALITY`, not NO_EDGE.

This amendment does not change thresholds, direction, horizon, cooldown, assets, execution, fees or economic PASS/FAIL gates.

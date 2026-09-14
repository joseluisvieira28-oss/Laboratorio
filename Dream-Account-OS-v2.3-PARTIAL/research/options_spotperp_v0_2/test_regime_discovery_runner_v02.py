#!/usr/bin/env python3
import datetime as dt, math
from regime_discovery_runner_v02 import regime_for_day, VOL_THRESHOLD

start = dt.date(2024,1,1)
# Deterministic synthetic upward low-vol path.
btc = {}
for i in range(60):
    d = start + dt.timedelta(days=i)
    btc[d] = 40000.0 * math.exp(0.001 * i)

day = start + dt.timedelta(days=40)
r = regime_for_day(day, btc)
assert r is not None
label, mom30, rv30 = r
assert label == 'UP_LOW', (label, mom30, rv30, VOL_THRESHOLD)
assert mom30 > 0
assert rv30 < VOL_THRESHOLD

# Synthetic downward low-vol path.
btc2 = {}
for i in range(60):
    d = start + dt.timedelta(days=i)
    btc2[d] = 40000.0 * math.exp(-0.001 * i)
r2 = regime_for_day(day, btc2)
assert r2 is not None
assert r2[0] == 'DOWN_LOW', r2

# Missing 30-day history must fail closed as unevaluable.
assert regime_for_day(start + dt.timedelta(days=10), btc) is None

print('OPTIONS_SPOTPERP_002_SYNTHETIC_REGIME_TESTS_PASS')
print('NO REAL MARKET OUTCOMES / NO 2025 / NO 2026')

#!/usr/bin/env python3
import datetime as dt
import math
from risk_scaling_v21_runner import causal_weights, metrics, MIN_RV_HISTORY

# Weight is causal, capped at 1, and unavailable before the exact warmup.
start=dt.date(2021,1,1)
rv={start+dt.timedelta(days=i): 0.02 for i in range(MIN_RV_HISTORY+3)}
w=causal_weights(rv)
assert len(w)==4, len(w)
assert all(abs(x-1.0)<1e-12 for x in w.values())

# High current volatility is scaled down using history available through t.
rv2={start+dt.timedelta(days=i): 0.02 for i in range(MIN_RV_HISTORY)}
rv2[start+dt.timedelta(days=MIN_RV_HISTORY)]=0.04
w2=causal_weights(rv2)
last=w2[start+dt.timedelta(days=MIN_RV_HISTORY)]
assert 0.49 <= last <= 0.51, last

# Metric costs scale linearly with notional and no leverage is introduced.
rows=[]
for i in range(10):
    rows.append({"signal_date":dt.date(2022,1,1)+dt.timedelta(days=i),"position":1,"weight":0.5,"aligned_unscaled_gross_bps":30.0})
m=metrics(rows,10.0)
assert m["entered_scaled_trades"]==10
assert abs(m["average_executed_notional"]-0.5)<1e-12
assert abs(m["net_mean_bps_per_parent_opportunity"]-10.0)<1e-12
assert m["profit_factor"]==float("inf")
assert m["max_drawdown"]==0.0
assert all(0 < r["weight"] <= 1 for r in rows)

print("OPTIONS_RISK_SCALING_V21_SYNTHETIC_TESTS_PASS")
print("NO NETWORK / NO REAL MARKET OUTCOMES / NO 2025 / NO 2026")

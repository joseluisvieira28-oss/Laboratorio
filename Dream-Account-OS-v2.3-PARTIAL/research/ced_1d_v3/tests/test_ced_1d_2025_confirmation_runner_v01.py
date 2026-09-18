#!/usr/bin/env python3
import importlib.util,math,tempfile
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"ced_1d_2025_confirmation_runner_v01.py"
spec=importlib.util.spec_from_file_location("r",RUNNER)
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

assert r.complete_signal_week(date(2025,1,6))
assert r.complete_signal_week(date(2025,12,28))
assert not r.complete_signal_week(date(2025,1,5))
assert not r.complete_signal_week(date(2025,12,29))
assert set(r.CELLS)=={"CED1D-0031","CED1D-0033","CED1D-0041","CED1D-0241","CED1D-0243","CED1D-0251","CED1D-0253","CED1D-0261"}
assert tuple(r.TARGETS)==("CED1D-0031","CED1D-0241","CED1D-0251")

# Holm must be monotone in sorted raw p-values and retain all eight cells.
p={f"x{i}":v for i,v in enumerate([.001,.01,.02,.03,.04,.2,.5,1.0])}
h=r.holm(p)
assert len(h)==8
ordered=sorted(p,key=p.get)
assert all(h[ordered[i]]<=h[ordered[i+1]]+1e-15 for i in range(7))
assert math.isclose(h["x0"],.008,rel_tol=0,abs_tol=1e-12)

# Funding bounds must contain every point mark price between low/high.
event={"status":"TRADE","entry_day":"2025-01-02","exit_day":"2025-01-03","entry_open":100.0,
       "direction":1,"signed_return":.01}
bindings=[{"fundingTime":1735776000015+8*3600*1000,"fundingRate":"0.0001","markLow":95.0,"markHigh":105.0}]
x=r.add_funding_bounds(event,"AVAXUSDT",{"AVAXUSDT":bindings})
assert x["funding_lower_bps"]<=x["funding_upper_bps"]
for mark in (95.0,100.0,105.0):
    exact=-1*.0001*(mark/100.0)*10000
    assert x["funding_lower_bps"]-1e-12<=exact<=x["funding_upper_bps"]+1e-12

# Original V0.3 package and hypotheses module must pass exact hashes.
v03=ROOT/"recovered_authority"/"CED-1D-V1-RUNNER-FREEZE-V0.3.zip"
with tempfile.TemporaryDirectory() as td:
    hyp=r.load_original_hypotheses(v03,Path(td))
    assert hyp.sgn(2)==1 and hyp.sgn(-2)==-1 and hyp.sgn(0)==0

print("CED1D_2025_CONFIRMATION_SYNTHETIC_QA_PASS")

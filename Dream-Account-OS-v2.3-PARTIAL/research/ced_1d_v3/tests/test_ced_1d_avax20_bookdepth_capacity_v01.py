#!/usr/bin/env python3
import csv,io,importlib.util,zipfile
from datetime import date,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"ced_1d_avax20_bookdepth_capacity_v01.py"
spec=importlib.util.spec_from_file_location("m",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

assert m.parse_ts("2025-01-06 00:00:30")==1736121630000
assert m.parse_ts("1736121630000")==1736121630000

buf=io.BytesIO()
with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
    s=io.StringIO(); w=csv.writer(s,lineterminator="\n")
    w.writerow(["timestamp","percentage","depth","notional"])
    for ts in ["2025-01-06 00:00:00","2025-01-06 00:00:30"]:
        for p in [-5,-4,-3,-2,-1,1,2,3,4,5]:
            w.writerow([ts,p,10+abs(p),1000+100*abs(p)])
    z.writestr("AVAXUSDT-bookDepth-2025-01-06.csv",s.getvalue())
target=int(datetime(2025,1,6,0,1,tzinfo=timezone.utc).timestamp()*1000)
r=m.scan_bookdepth_zip(buf.getvalue(),date(2025,1,6),target)
assert r["best_ts"]==1736121630000
assert r["bands"][1.0]["notional"]==1100.0
assert r["bands"][-1.0]["notional"]==1100.0
assert r["rows"]==20
assert r["snapshots"]==2

# Future snapshot must not be selected.
buf2=io.BytesIO()
with zipfile.ZipFile(buf2,"w",compression=zipfile.ZIP_DEFLATED) as z:
    s=io.StringIO(); w=csv.writer(s,lineterminator="\n")
    w.writerow(["timestamp","percentage","depth","notional"])
    for ts in ["2025-01-06 00:00:30","2025-01-06 00:01:30"]:
        for p in [-1,1]: w.writerow([ts,p,1,500])
    z.writestr("x.csv",s.getvalue())
r2=m.scan_bookdepth_zip(buf2.getvalue(),date(2025,1,6),target)
assert r2["best_ts"]==1736121630000

print("CED1D_AVAX20_BOOKDEPTH_SYNTHETIC_QA_PASS")

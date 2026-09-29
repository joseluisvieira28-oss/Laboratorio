#!/usr/bin/env python3
import csv,datetime as dt,io,json,urllib.request,zipfile

BASE="https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m/"
DATES=["2023-05-18","2023-07-01","2023-10-23"]

def probe(ds):
    url=f"{BASE}BTCUSDT-1m-{ds}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SpotSource/0.1"})
    with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1: raise RuntimeError("unexpected zip members")
        rows=[]
        with z.open(names[0]) as fh:
            reader=csv.reader(io.TextIOWrapper(fh,encoding="utf-8",newline=""))
            for row in reader:
                if row: rows.append(row)
    times=[]
    has_08=False
    bad=0
    for row in rows:
        if len(row)<7:
            bad+=1; continue
        try:
            t=int(row[0])
            # 2023 archives use millisecond timestamps.
            sec=t/1000 if t>10_000_000_000 else t
            d=dt.datetime.fromtimestamp(sec,dt.timezone.utc)
            times.append(sec)
            if d.hour==8 and d.minute==0: has_08=True
        except Exception:
            bad+=1
    monotonic=all(b>a for a,b in zip(times,times[1:]))
    return {
        "date":ds,
        "download_bytes":len(raw),
        "row_count":len(rows),
        "min_column_count":min((len(r) for r in rows),default=0),
        "max_column_count":max((len(r) for r in rows),default=0),
        "timestamp_parse_count":len(times),
        "bad_structure_rows":bad,
        "open_times_strictly_increasing":monotonic,
        "contains_08utc_bar":has_08,
        "prices_emitted":False
    }

samples=[]
errors=[]
for d in DATES:
    try:samples.append(probe(d))
    except Exception as e:errors.append({"date":d,"error_type":type(e).__name__,"error":str(e)[:300]})

passed=(not errors and len(samples)==3 and all(
    x["row_count"]>=1430 and x["min_column_count"]>=6 and
    x["open_times_strictly_increasing"] and x["contains_08utc_bar"]
    for x in samples
))
classification="BINANCE_SPOT1M_SOURCE_FEASIBLE" if passed else ("BINANCE_SPOT1M_SOURCE_PARTIAL" if samples else "BINANCE_SPOT1M_SOURCE_ACQUISITION_FAILURE")
out={
 "source_probe_id":"BOVRP-BINANCE-SPOT1M-SOURCE-001",
 "classification":classification,
 "samples":samples,
 "errors":errors,
 "prices_emitted":False,
 "returns_computed":False,
 "realized_variance_computed":False,
 "vrp_computed":False,
 "pnl_computed":False
}
open("binance_spot1m_source_receipt_v01.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"samples":[{"date":x["date"],"rows":x["row_count"],"contains_08utc_bar":x["contains_08utc_bar"]} for x in samples],"error_count":len(errors)},sort_keys=True))
raise SystemExit(0 if passed else 2)

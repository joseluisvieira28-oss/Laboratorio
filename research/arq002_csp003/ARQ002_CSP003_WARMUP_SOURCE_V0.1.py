#!/usr/bin/env python3
"""ARQ-002-CSP-003 2021-12 boundary warm-up source gate — outcome blind."""
from __future__ import annotations
import csv,hashlib,io,json,math,re,time,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
BASE="https://data.binance.vision/data/futures/um";S="BTCUSDT";UTC=timezone.utc
UA="Crypto-Lab-ARQ002-CSP003-Warmup/0.1"
class E(RuntimeError):pass
def req(u,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=90) as x:return x.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(1.5*(i+1))
    raise E(f"DOWNLOAD:{u}:{last}")
def cs(u):
    x=req(u+".CHECKSUM").decode("utf-8","replace");m=re.search(r"(?i)\b([0-9a-f]{64})\b",x)
    if not m:raise E("CHECKSUM_PARSE")
    return m.group(1).lower()
def ver(u):
    raw=req(u);pub=cs(u);act=hashlib.sha256(raw).hexdigest()
    if act!=pub:raise E(f"CHECKSUM:{u}")
    return raw,act
def rr(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip():raise E("ZIP_CRC")
        ns=[n for n in z.namelist() if n.endswith(".csv")]
        if len(ns)!=1:raise E("CSV_COUNT")
        txt=z.read(ns[0]).decode("utf-8-sig")
    return [r for r in csv.reader(io.StringIO(txt)) if r]
def ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except:pass
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=UTC)
    return int(d.timestamp()*1000)
def main():
    rec={"lab_id":"ARQ-002-CSP-003","gate":"WARMUP_BOUNDARY_2021_12_V0.1","classification":"RUNNING",
         "economic_values_opened":False,"outcomes_opened":False,"errors":[]}
    try:
        ds="2021-12-31"
        ku=f"{BASE}/daily/klines/{S}/1m/{S}-1m-{ds}.zip";raw,ksha=ver(ku);rows=rr(raw);body=rows
        try:ms(rows[0][0])
        except:body=rows[1:]
        ts=[ms(r[0]) for r in body];lo=ms(ds+"T00:00:00Z")
        if ts!=[lo+i*60000 for i in range(1440)]:raise E(f"KLINE_GRID:{len(ts)}")
        mu=f"{BASE}/daily/metrics/{S}/{S}-metrics-{ds}.zip";raw,msha=ver(mu);rows=rr(raw)
        h=[x.strip() for x in rows[0]];ti=h.index("create_time");oi=h.index("sum_open_interest")
        groups={}
        for r in rows[1:]:groups.setdefault(ms(r[ti]),[]).append(r)
        invalid=[];conflicts=0
        for t,rs in groups.items():
            if len({tuple(x) for x in rs})!=1:conflicts+=1;continue
            try:
                v=float(rs[0][oi]);valid=math.isfinite(v) and v>0
            except:valid=False
            if not valid:invalid.append(t)
        if conflicts:raise E(f"MET_CONFLICT:{conflicts}")
        fu=f"{BASE}/monthly/fundingRate/{S}/{S}-fundingRate-2021-12.zip";raw,fsha=ver(fu);rows=rr(raw)
        h=[x.strip() for x in rows[0]]
        ti=next(h.index(a) for a in ("calc_time","fundingTime","funding_time") if a in h)
        tsf=sorted(ms(r[ti]) for r in rows[1:])
        if len(tsf)!=len(set(tsf)):raise E("FUND_DUP")
        gaps=[b-a for a,b in zip(tsf,tsf[1:])]
        if gaps and max(gaps)>12*3600*1000:raise E(f"FUND_GAP:{max(gaps)}")
        rec.update({"classification":"SOURCE_WARMUP_PASS","kline_sha256":ksha,"metrics_sha256":msha,"funding_sha256":fsha,
                    "metrics_slots":len(groups),"metrics_invalid_slots":len(invalid),
                    "funding_rows":len(tsf),"funding_max_gap_ms":max(gaps) if gaps else None})
    except Exception as e:
        rec["classification"]="SOURCE_WARMUP_FAIL_CLOSED";rec["errors"].append(f"{type(e).__name__}:{e}")
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path("ARQ002_CSP003_WARMUP_SOURCE_2021_12_V0.1.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,sort_keys=True))
    return 0 if rec["classification"]=="SOURCE_WARMUP_PASS" else 1
if __name__=="__main__":raise SystemExit(main())

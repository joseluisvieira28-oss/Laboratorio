#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json,math,random,shutil,tempfile,time,urllib.request,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

LAB="PERP-LAUNCH-POSTLAUNCH-SHORT-001"
SRC=Path("Dream-Account-OS-v2.3-PARTIAL/research/perpetual_launch_shock_001/source_evidence/PLS_SOURCE_DATA_GATE_V01.json")
OUT=Path("labs/PERP_LAUNCH_POSTLAUNCH_SHORT_001/run_output")
DV="https://data.binance.vision/data/futures/um/daily/klines"
M=60000;BASE=60.0;STRESS=160.0;BOOT=10000;SEED=20261001
MIN_E=60;MIN_D=40

def ms(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def fetch(url,p):
    last=None
    for i in range(5):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PLPS/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r,open(p,"wb") as w:shutil.copyfileobj(r,w,1024*1024)
            return
        except Exception as e:last=e;time.sleep(min(2**i,8))
    raise RuntimeError(f"download failed {url}: {last}")

def days_between(a,b):
    d=a.date();out=[]
    while d<=b.date():out.append(d.isoformat());d+=timedelta(days=1)
    return out

def load_day(symbol,day,tmp,cache,prov):
    k=(symbol,day)
    if k in cache:return cache[k]
    name=f"{symbol}-1m-{day}.zip";url=f"{DV}/{symbol}/1m/{name}"
    z=tmp/(symbol+"_"+day+".zip");c=tmp/(symbol+"_"+day+".CHECKSUM")
    fetch(url,z);fetch(url+".CHECKSUM",c)
    exp=c.read_text().strip().split()[0].lower();act=sha(z)
    if act!=exp:raise RuntimeError(f"checksum mismatch {symbol} {day}")
    rows={}
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError("archive members")
        with zz.open(names[0]) as raw:
            rd=csv.reader((x.decode() for x in raw))
            for r in rd:
                if not r or not str(r[0]).strip().lstrip("-").isdigit():continue
                t=int(float(r[0]));t=t if t>10**11 else t*1000
                rows[t]=float(r[1])
    cache[k]=rows;prov.append({"symbol":symbol,"day":day,"url":url,"sha256":act})
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    return rows

def event_row(e,tmp,cache,prov):
    t0=ms(e["event_timestamp_utc"]);entry=t0+60*M;exit_=t0+1500*M
    startdt=datetime.fromtimestamp(t0/1000,tz=timezone.utc);enddt=datetime.fromtimestamp(exit_/1000,tz=timezone.utc)
    tok=e["symbol"];ts=tok+"USDT"
    tr={};br={}
    for d in days_between(startdt,enddt):
        tr.update(load_day(ts,d,tmp,cache,prov))
        br.update(load_day("BTCUSDT",d,tmp,cache,prov))
    need=range(t0,exit_+M,M)
    if any(t not in tr for t in need) or any(t not in br for t in need):
        return None,"INCOMPLETE_CONTIGUOUS_1M_WINDOW"
    te=tr[entry];tx=tr[exit_];be=br[entry];bx=br[exit_]
    if min(te,tx,be,bx)<=0:return None,"NONPOSITIVE_PRICE"
    gross=10000*(math.log(bx/be)-math.log(tx/te))
    dt=datetime.fromtimestamp(t0/1000,tz=timezone.utc)
    return {"symbol":tok,"event_timestamp_utc":e["event_timestamp_utc"],
      "launch_date_utc":dt.date().isoformat(),"quarter":f"{dt.year}-Q{(dt.month-1)//3+1}",
      "entry_timestamp_utc":datetime.fromtimestamp(entry/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "exit_timestamp_utc":datetime.fromtimestamp(exit_/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "token_entry":te,"token_exit":tx,"btc_entry":be,"btc_exit":bx,
      "gross_pair_bps":gross,"base_net_bps":gross-BASE,"stress_net_bps":gross-STRESS,
      "trading_authority":"NONE"},None

def med(v):
    a=sorted(v);n=len(a)
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2
def pf(v):
    p=sum(x for x in v if x>0);n=-sum(x for x in v if x<0)
    return p/n if n>0 else (math.inf if p>0 else 0)
def boot(rows):
    cl=defaultdict(list)
    for r in rows:cl[r["launch_date_utc"]].append(r["stress_net_bps"])
    keys=sorted(cl);rng=random.Random(SEED);means=[]
    for _ in range(BOOT):
        z=[]
        for __ in keys:z.extend(cl[keys[rng.randrange(len(keys))]])
        means.append(sum(z)/len(z))
    means.sort()
    def q(p):
        x=(len(means)-1)*p;i=int(x);j=math.ceil(x);w=x-i
        return means[i]*(1-w)+means[j]*w
    return [q(.025),q(.975)]

def phase(year,events):
    rows=[];rej=[];prov=[];cache={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for i,e in enumerate(events,1):
            print(f"{year} {i}/{len(events)} {e['symbol']} {e['event_timestamp_utc']}",flush=True)
            try:
                r,why=event_row(e,tmp,cache,prov)
                if r:rows.append(r)
                else:rej.append({"symbol":e["symbol"],"event_timestamp_utc":e["event_timestamp_utc"],"reason":why})
            except Exception as ex:
                rej.append({"symbol":e["symbol"],"event_timestamp_utc":e["event_timestamp_utc"],"reason":"SOURCE_ERROR","detail":str(ex)})
    vals=[r["stress_net_bps"] for r in rows];base=[r["base_net_bps"] for r in rows]
    qs={}
    for q in [f"{year}-Q1",f"{year}-Q2",f"{year}-Q3",f"{year}-Q4"]:
        z=[r["stress_net_bps"] for r in rows if r["quarter"]==q]
        qs[q]={"n":len(z),"median_stress_net_bps":med(z) if z else None}
    rep={"lab_id":LAB,"year":year,"source_qualified_events":len(events),"eligible_events":len(rows),
      "distinct_launch_dates":len({r["launch_date_utc"] for r in rows}),"rejected_events":len(rej),
      "mean_gross_bps":sum(r["gross_pair_bps"] for r in rows)/len(rows) if rows else None,
      "median_gross_bps":med([r["gross_pair_bps"] for r in rows]) if rows else None,
      "mean_base_net_bps":sum(base)/len(base) if base else None,
      "mean_stress_net_bps":sum(vals)/len(vals) if vals else None,
      "median_stress_net_bps":med(vals) if vals else None,
      "stress_hit_rate":sum(x>0 for x in vals)/len(vals) if vals else None,
      "stress_profit_factor":pf(vals) if vals else None,
      "bootstrap95_mean_stress_bps":boot(rows) if rows else None,
      "quarterly":qs,"trading_authority":"NONE"}
    if len(rows)<MIN_E or len({r["launch_date_utc"] for r in rows})<MIN_D:
        rep["classification"]="INSUFFICIENT_DISCOVERY_SAMPLE" if year==2023 else "INSUFFICIENT_OOS_SAMPLE"
    else:
        posq=sum(1 for x in qs.values() if x["median_stress_net_bps"] is not None and x["median_stress_net_bps"]>0)
        gates={"mean_stress_gt_zero":rep["mean_stress_net_bps"]>0,
          "bootstrap_lower_gt_zero":rep["bootstrap95_mean_stress_bps"][0]>0,
          "median_stress_gt_zero":rep["median_stress_net_bps"]>0,
          "stress_hit_rate_ge_0_52":rep["stress_hit_rate"]>=.52,
          "stress_pf_ge_1_20":rep["stress_profit_factor"]>=1.2,
          "mean_base_gt_zero":rep["mean_base_net_bps"]>0,
          "positive_median_quarters_ge_3":posq>=3}
        rep["gate_checks"]=gates;rep["positive_median_quarters"]=posq
        ok=all(gates.values())
        rep["classification"]=("POSTLAUNCH_SHORT_SURVIVES_DISCOVERY" if ok else "NO_POSTLAUNCH_SHORT_EDGE") if year==2023 else ("OOS_POSTLAUNCH_SHORT_SURVIVES" if ok else "NO_EXECUTABLE_OOS_EDGE")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/f"{year}_REPORT.json").write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/f"{year}_REJECTED.json").write_text(json.dumps(rej,indent=2,sort_keys=True)+"\n")
    (OUT/f"{year}_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")
    fields=list(rows[0].keys()) if rows else ["symbol"]
    with (OUT/f"{year}_EVENTS.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps(rep,indent=2,sort_keys=True),flush=True)
    return rep

def main():
    src=json.loads(SRC.read_text());events=src["qualified_events"]
    e23=[e for e in events if e["event_timestamp_utc"].startswith("2023-")]
    e24=[e for e in events if e["event_timestamp_utc"].startswith("2024-")]
    assert len(e23)==83 and len(e24)==87
    d=phase(2023,e23)
    term={"lab_id":LAB,"discovery":d,"oos_opened":False,"trading_authority":"NONE"}
    if d["classification"]=="POSTLAUNCH_SHORT_SURVIVES_DISCOVERY":
        o=phase(2024,e24);term["oos_opened"]=True;term["oos"]=o;term["classification"]=o["classification"]
    else:term["classification"]="DISCOVERY_"+d["classification"]
    (OUT/"TERMINAL_REPORT.json").write_text(json.dumps(term,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("TERMINAL",json.dumps(term,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":main()

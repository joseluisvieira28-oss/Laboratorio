#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json,math,random,shutil,tempfile,time,urllib.request,zipfile
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

LAB_ID="PERP-LAUNCH-IMPULSE-REVERSION-001"
SOURCE_PATH=Path("Dream-Account-OS-v2.3-PARTIAL/research/perpetual_launch_shock_001/source_evidence/PLS_SOURCE_DATA_GATE_V01.json")
OUT=Path("labs/PERP_LAUNCH_IMPULSE_REVERSION_001/run_output")
BASE_URL="https://data.binance.vision/data/futures/um/daily/klines"
M=60000
OBS=15
HOLD=360
BASE_COST=60.0
STRESS_COST=160.0
MIN_ELIGIBLE=60
MIN_EXECUTED=50
BOOT_N=10000
BOOT_SEED=20261001

def parse_ms(v):
    x=int(float(v));a=abs(x)
    if a<10**11:return x*1000
    if a<10**14:return x
    if a<10**17:return x//1000
    return x//1_000_000

def iso_ms(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()

def fetch(url,path):
    last=None
    for n in range(5):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PLIR/0.1"})
            with urllib.request.urlopen(req,timeout=60) as r,open(path,"wb") as w:shutil.copyfileobj(r,w,1024*1024)
            return
        except Exception as e:last=e;time.sleep(min(2**n,8))
    raise RuntimeError(f"download failed {url}: {last}")

def load_day(symbol,day,tmp,prov,cache):
    key=(symbol,day)
    if key in cache:return cache[key]
    name=f"{symbol}-1m-{day}.zip";url=f"{BASE_URL}/{symbol}/1m/{name}"
    z=tmp/name;c=tmp/(name+".CHECKSUM")
    fetch(url,z);fetch(url+".CHECKSUM",c)
    expected=c.read_text().strip().split()[0].lower();actual=sha256_file(z)
    if actual!=expected:raise RuntimeError(f"checksum mismatch {symbol} {day}")
    prov.append({"symbol":symbol,"day":day,"url":url,"sha256":actual})
    rows={}
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError(f"unexpected archive members {symbol} {day}")
        with zz.open(names[0],"r") as raw:
            rd=csv.reader((line.decode("utf-8") for line in raw))
            for row in rd:
                if not row or not str(row[0]).strip().lstrip("-").isdigit():continue
                ot=parse_ms(row[0])
                rows[ot]={"open":float(row[1]),"close":float(row[4])}
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    cache[key]=rows
    return rows

def event_window(e,tmp,prov,cache):
    sym=e["symbol"];t0=iso_ms(e["event_timestamp_utc"])
    exit_open=t0+(OBS-1+HOLD)*M
    d0=datetime.fromtimestamp(t0/1000,tz=timezone.utc).date()
    d1=datetime.fromtimestamp(exit_open/1000,tz=timezone.utc).date()
    days=[d0] if d0==d1 else [d0,d1]
    tok={};btc={}
    for d in days:
        ds=d.isoformat()
        tok.update(load_day(sym,ds,tmp,prov,cache))
        btc.update(load_day("BTCUSDT",ds,tmp,prov,cache))
    need=[t0+k*M for k in range(OBS+HOLD)]
    mt=[x for x in need if x not in tok];mb=[x for x in need if x not in btc]
    if mt or mb:return None,{"reason":"INCOMPLETE_OR_NONCONTIGUOUS_1M_WINDOW","missing_token":len(mt),"missing_btc":len(mb)}
    first=t0;entry=t0+(OBS-1)*M;exit_t=t0+(OBS-1+HOLD)*M
    to=tok[first]["open"];bo=btc[first]["open"];te=tok[entry]["close"];be=btc[entry]["close"];tx=tok[exit_t]["close"];bx=btc[exit_t]["close"]
    if min(to,bo,te,be,tx,bx)<=0:return None,{"reason":"NONPOSITIVE_PRICE"}
    impulse=math.log(te/to)-math.log(be/bo)
    if impulse>0:d=-1
    elif impulse<0:d=1
    else:d=0
    gross=d*10000.0*(math.log(tx/te)-math.log(bx/be)) if d else 0.0
    entry_close_ms=t0+OBS*M
    exit_close_ms=entry_close_ms+HOLD*M
    return {
      "lab_id":LAB_ID,"symbol":sym,"event_timestamp_utc":e["event_timestamp_utc"],
      "entry_date_utc":datetime.fromtimestamp(entry_close_ms/1000,tz=timezone.utc).date().isoformat(),
      "entry_timestamp_utc":datetime.fromtimestamp(entry_close_ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "exit_timestamp_utc":datetime.fromtimestamp(exit_close_ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "excess_impulse_bps":impulse*10000.0,"direction":d,"executed":d!=0,
      "token_entry":te,"btc_entry":be,"token_exit":tx,"btc_exit":bx,
      "gross_pair_bps":gross,
      "base_net_bps":gross-BASE_COST if d else 0.0,
      "stress_net_bps":gross-STRESS_COST if d else 0.0,
      "trading_authority":"NONE"
    },None

def median(v):
    a=sorted(v);n=len(a)
    if not n:return math.nan
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def pf(v):
    pos=sum(x for x in v if x>0);neg=-sum(x for x in v if x<0)
    return pos/neg if neg>0 else (math.inf if pos>0 else 0.0)

def cluster_bootstrap(rows):
    c=defaultdict(list)
    for r in rows:c[r["entry_date_utc"]].append(r["stress_net_bps"])
    keys=sorted(c);rng=random.Random(BOOT_SEED);means=[]
    for _ in range(BOOT_N):
        vals=[]
        for __ in range(len(keys)):vals.extend(c[keys[rng.randrange(len(keys))]])
        means.append(sum(vals)/len(vals))
    means.sort()
    def q(p):
        x=(len(means)-1)*p;lo=int(math.floor(x));hi=int(math.ceil(x))
        if lo==hi:return means[lo]
        w=x-lo;return means[lo]*(1-w)+means[hi]*w
    return [q(.025),q(.975)]

def phase(year,events):
    prov=[];rows=[];rej=[];cache={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for i,e in enumerate(events,1):
            print(f"{year} {i}/{len(events)} {e['symbol']} {e['event_timestamp_utc']}",flush=True)
            try:
                r,err=event_window(e,tmp,prov,cache)
                if r:rows.append(r)
                else:rej.append({"symbol":e["symbol"],"event_timestamp_utc":e["event_timestamp_utc"],**err})
            except Exception as ex:
                rej.append({"symbol":e["symbol"],"event_timestamp_utc":e["event_timestamp_utc"],"reason":"SOURCE_ERROR","detail":str(ex)})
    exe=[r for r in rows if r["executed"]]
    stress=[r["stress_net_bps"] for r in exe];gross=[r["gross_pair_bps"] for r in exe]
    report={
      "lab_id":LAB_ID,"year":year,"source_qualified_events":len(events),"eligible_events":len(rows),
      "executed_trades":len(exe),"rejected_events":len(rej),
      "mean_abs_excess_impulse_bps":sum(abs(r["excess_impulse_bps"]) for r in exe)/len(exe) if exe else None,
      "median_abs_excess_impulse_bps":median([abs(r["excess_impulse_bps"]) for r in exe]) if exe else None,
      "mean_gross_executed_bps":sum(gross)/len(gross) if gross else None,
      "median_gross_executed_bps":median(gross) if gross else None,
      "mean_base_net_all_eligible_bps":sum(r["base_net_bps"] for r in rows)/len(rows) if rows else None,
      "mean_stress_net_all_eligible_bps":sum(r["stress_net_bps"] for r in rows)/len(rows) if rows else None,
      "median_stress_net_executed_bps":median(stress) if stress else None,
      "stress_hit_rate_executed":sum(x>0 for x in stress)/len(stress) if stress else None,
      "stress_profit_factor_executed":pf(stress) if stress else None,
      "bootstrap95_mean_stress_all_eligible_bps":cluster_bootstrap(rows) if rows else None,
      "trading_authority":"NONE"
    }
    if len(rows)<MIN_ELIGIBLE or len(exe)<MIN_EXECUTED:
        report["classification"]="INSUFFICIENT_SAMPLE"
    else:
        gates={
          "mean_stress_all_eligible_gt_zero":report["mean_stress_net_all_eligible_bps"]>0,
          "bootstrap_stress_ci95_lower_gt_zero":report["bootstrap95_mean_stress_all_eligible_bps"][0]>0,
          "median_stress_executed_gt_zero":report["median_stress_net_executed_bps"]>0,
          "stress_hit_rate_ge_0_52":report["stress_hit_rate_executed"]>=.52,
          "stress_pf_ge_1_20":report["stress_profit_factor_executed"]>=1.2,
          "mean_base_all_eligible_gt_zero":report["mean_base_net_all_eligible_bps"]>0
        }
        report["gate_checks"]=gates
        if year==2023:report["classification"]="IMPULSE_REVERSION_SURVIVES_DISCOVERY" if all(gates.values()) else "NO_IMPULSE_REVERSION_EDGE"
        else:report["classification"]="OOS_IMPULSE_REVERSION_SURVIVES" if all(gates.values()) else "NO_EXECUTABLE_OOS_EDGE"
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/f"{year}_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/f"{year}_REJECTED.json").write_text(json.dumps(rej,indent=2,sort_keys=True)+"\n")
    (OUT/f"{year}_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")
    fields=["lab_id","symbol","event_timestamp_utc","entry_date_utc","entry_timestamp_utc","exit_timestamp_utc","excess_impulse_bps","direction","executed","token_entry","btc_entry","token_exit","btc_exit","gross_pair_bps","base_net_bps","stress_net_bps","trading_authority"]
    with (OUT/f"{year}_EVENTS.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    return report

def main():
    src=json.loads(SOURCE_PATH.read_text());events=src["qualified_events"]
    e23=[e for e in events if e["event_timestamp_utc"].startswith("2023-")]
    e24=[e for e in events if e["event_timestamp_utc"].startswith("2024-")]
    assert len(e23)==83 and len(e24)==87
    disc=phase(2023,e23)
    terminal={"lab_id":LAB_ID,"discovery":disc,"oos_opened":False,"trading_authority":"NONE"}
    if disc["classification"]=="IMPULSE_REVERSION_SURVIVES_DISCOVERY":
        oos=phase(2024,e24);terminal["oos_opened"]=True;terminal["oos"]=oos;terminal["classification"]=oos["classification"]
    else:terminal["classification"]="DISCOVERY_"+disc["classification"]
    (OUT/"TERMINAL_REPORT.json").write_text(json.dumps(terminal,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("TERMINAL",json.dumps(terminal,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":main()

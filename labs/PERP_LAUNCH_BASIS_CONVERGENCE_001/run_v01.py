#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, math, random, shutil, tempfile, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

LAB_ID="PERP-LAUNCH-BASIS-CONVERGENCE-001"
SOURCE_PATH=Path("Dream-Account-OS-v2.3-PARTIAL/research/perpetual_launch_shock_001/source_evidence/PLS_SOURCE_DATA_GATE_V01.json")
OUT=Path("labs/PERP_LAUNCH_BASIS_CONVERGENCE_001/run_output")
SPOT_BASE="https://data.binance.vision/data/spot/daily/klines"
FUT_BASE="https://data.binance.vision/data/futures/um/daily/klines"
MINUTE_MS=60000
BASE_COST=60.0
STRESS_COST=160.0
BOOT_N=10000
BOOT_SEED=20261001
MIN_ELIGIBLE=60
MIN_EXECUTED=25

def parse_ms(v):
    x=int(float(v)); a=abs(x)
    if a<10**11:return x*1000
    if a<10**14:return x
    if a<10**17:return x//1000
    return x//1_000_000

def iso_ms(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()

def fetch(url,path):
    last=None
    for n in range(5):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PLBC/0.1"})
            with urllib.request.urlopen(req,timeout=60) as r,open(path,"wb") as w:
                shutil.copyfileobj(r,w,1024*1024)
            return
        except Exception as e:
            last=e;time.sleep(min(2**n,8))
    raise RuntimeError(f"download failed {url}: {last}")

def load_daily(symbol,day,venue,tmp,prov):
    base=SPOT_BASE if venue=="spot" else FUT_BASE
    name=f"{symbol}-1m-{day}.zip"
    url=f"{base}/{symbol}/1m/{name}"
    z=tmp/f"{venue}_{name}"; c=tmp/f"{venue}_{name}.CHECKSUM"
    fetch(url,z);fetch(url+".CHECKSUM",c)
    expected=c.read_text().strip().split()[0].lower();actual=sha256_file(z)
    if actual!=expected:raise RuntimeError(f"checksum mismatch {venue} {symbol} {day}")
    prov.append({"venue":venue,"symbol":symbol,"day":day,"url":url,"sha256":actual})
    rows={}
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError(f"unexpected archive members {venue} {symbol} {day}")
        with zz.open(names[0],"r") as raw:
            rd=csv.reader((line.decode("utf-8") for line in raw))
            for row in rd:
                if not row or not str(row[0]).strip().lstrip("-").isdigit():continue
                ot=parse_ms(row[0])
                if ot%MINUTE_MS:raise RuntimeError(f"unaligned minute {venue} {symbol} {ot}")
                rows[ot]={"open":float(row[1]),"high":float(row[2]),"low":float(row[3]),"close":float(row[4]),"volume":float(row[5])}
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    return rows

def get_window(event,tmp,prov):
    symbol=event["symbol"]; t0=iso_ms(event["event_timestamp_utc"])
    end=t0+64*MINUTE_MS
    d0=datetime.fromtimestamp(t0/1000,tz=timezone.utc).date()
    d1=datetime.fromtimestamp(end/1000,tz=timezone.utc).date()
    days=[d0] if d0==d1 else [d0,d1]
    spot={};fut={}
    for d in days:
        ds=d.isoformat()
        spot.update(load_daily(symbol,ds,"spot",tmp,prov))
        fut.update(load_daily(symbol,ds,"futures",tmp,prov))
    need=[t0+k*MINUTE_MS for k in range(65)]
    missing_spot=[t for t in need if t not in spot]
    missing_fut=[t for t in need if t not in fut]
    if missing_spot or missing_fut:
        return None,{"reason":"INCOMPLETE_PAIRED_1M_WINDOW","missing_spot":len(missing_spot),"missing_futures":len(missing_fut)}
    entry_open=t0+4*MINUTE_MS
    exit_open=t0+64*MINUTE_MS
    se=spot[entry_open]["close"];fe=fut[entry_open]["close"]
    sx=spot[exit_open]["close"];fx=fut[exit_open]["close"]
    if min(se,fe,sx,fx)<=0:return None,{"reason":"NONPOSITIVE_PRICE"}
    basis=10000.0*math.log(fe/se)
    executed=basis>0
    gross=10000.0*(math.log(sx/se)-math.log(fx/fe)) if executed else 0.0
    return {
        "lab_id":LAB_ID,
        "symbol":symbol,
        "event_timestamp_utc":event["event_timestamp_utc"],
        "launch_date_utc":event["event_timestamp_utc"][:10],
        "entry_timestamp_utc":datetime.fromtimestamp((t0+5*MINUTE_MS)/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
        "exit_timestamp_utc":datetime.fromtimestamp((t0+65*MINUTE_MS)/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
        "spot_entry":se,"perp_entry":fe,"spot_exit":sx,"perp_exit":fx,
        "basis_entry_bps":basis,
        "executed":executed,
        "gross_pair_bps":gross,
        "base_net_bps":gross-BASE_COST if executed else 0.0,
        "stress_net_bps":gross-STRESS_COST if executed else 0.0,
        "trading_authority":"NONE"
    },None

def median(v):
    a=sorted(v);n=len(a)
    if not n:return math.nan
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def pf(v):
    pos=sum(x for x in v if x>0);neg=-sum(x for x in v if x<0)
    if neg==0:return math.inf if pos>0 else 0.0
    return pos/neg

def cluster_bootstrap(rows,key="launch_date_utc"):
    clusters=defaultdict(list)
    for r in rows:clusters[r[key]].append(r["stress_net_bps"])
    keys=sorted(clusters)
    rng=random.Random(BOOT_SEED);means=[]
    for _ in range(BOOT_N):
        vals=[]
        for __ in range(len(keys)):
            k=keys[rng.randrange(len(keys))]
            vals.extend(clusters[k])
        means.append(sum(vals)/len(vals))
    means.sort()
    def q(p):
        x=(len(means)-1)*p;lo=int(math.floor(x));hi=int(math.ceil(x))
        if lo==hi:return means[lo]
        w=x-lo
        return means[lo]*(1-w)+means[hi]*w
    return [q(.025),q(.975)]

def phase(year,events):
    prov=[];rows=[];rejected=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for i,e in enumerate(events,1):
            print(f"{year} {i}/{len(events)} {e['symbol']} {e['event_timestamp_utc']}",flush=True)
            try:
                r,err=get_window(e,tmp,prov)
                if r:rows.append(r)
                else:rejected.append({"symbol":e["symbol"],"event_timestamp_utc":e["event_timestamp_utc"],**err})
            except Exception as ex:
                rejected.append({"symbol":e["symbol"],"event_timestamp_utc":e["event_timestamp_utc"],"reason":"SOURCE_ERROR","detail":str(ex)})
    executed=[r for r in rows if r["executed"]]
    stress=[r["stress_net_bps"] for r in executed]
    base=[r["base_net_bps"] for r in executed]
    all_stress=[r["stress_net_bps"] for r in rows]
    all_base=[r["base_net_bps"] for r in rows]
    report={
        "lab_id":LAB_ID,"year":year,
        "source_qualified_events":len(events),
        "eligible_events":len(rows),
        "executed_trades":len(executed),
        "no_trade_events":len(rows)-len(executed),
        "rejected_events":len(rejected),
        "mean_entry_basis_bps_executed":sum(r["basis_entry_bps"] for r in executed)/len(executed) if executed else None,
        "median_entry_basis_bps_executed":median([r["basis_entry_bps"] for r in executed]) if executed else None,
        "mean_gross_executed_bps":sum(r["gross_pair_bps"] for r in executed)/len(executed) if executed else None,
        "median_gross_executed_bps":median([r["gross_pair_bps"] for r in executed]) if executed else None,
        "mean_base_net_all_eligible_bps":sum(all_base)/len(rows) if rows else None,
        "mean_stress_net_all_eligible_bps":sum(all_stress)/len(rows) if rows else None,
        "median_stress_net_executed_bps":median(stress) if stress else None,
        "stress_hit_rate_executed":sum(x>0 for x in stress)/len(stress) if stress else None,
        "stress_profit_factor_executed":pf(stress) if stress else None,
        "bootstrap95_mean_stress_all_eligible_bps":cluster_bootstrap(rows) if rows else None,
        "trading_authority":"NONE"
    }
    if len(rows)<MIN_ELIGIBLE or len(executed)<MIN_EXECUTED:
        report["classification"]="INSUFFICIENT_SAMPLE"
    else:
        lo=report["bootstrap95_mean_stress_all_eligible_bps"][0]
        gates={
          "mean_stress_all_eligible_gt_zero":report["mean_stress_net_all_eligible_bps"]>0,
          "bootstrap_stress_ci95_lower_gt_zero":lo>0,
          "median_stress_executed_gt_zero":report["median_stress_net_executed_bps"]>0,
          "stress_hit_rate_ge_0_52":report["stress_hit_rate_executed"]>=0.52,
          "stress_pf_ge_1_20":report["stress_profit_factor_executed"]>=1.20,
          "mean_base_all_eligible_gt_zero":report["mean_base_net_all_eligible_bps"]>0
        }
        report["gate_checks"]=gates
        report["classification"]="BASIS_CONVERGENCE_SURVIVES_DISCOVERY" if year==2023 and all(gates.values()) else ("OOS_BASIS_CONVERGENCE_SURVIVES" if year==2024 and all(gates.values()) else ("NO_BASIS_CONVERGENCE_EDGE" if year==2023 else "NO_EXECUTABLE_OOS_EDGE"))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/f"{year}_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/f"{year}_REJECTED.json").write_text(json.dumps(rejected,indent=2,sort_keys=True)+"\n")
    (OUT/f"{year}_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")
    fields=["symbol","event_timestamp_utc","launch_date_utc","entry_timestamp_utc","exit_timestamp_utc","spot_entry","perp_entry","spot_exit","perp_exit","basis_entry_bps","executed","gross_pair_bps","base_net_bps","stress_net_bps","trading_authority"]
    with (OUT/f"{year}_EVENTS.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    return report

def main():
    src=json.loads(SOURCE_PATH.read_text())
    events=src["qualified_events"]
    e23=[e for e in events if e["event_timestamp_utc"].startswith("2023-")]
    e24=[e for e in events if e["event_timestamp_utc"].startswith("2024-")]
    assert len(e23)==83 and len(e24)==87
    disc=phase(2023,e23)
    terminal={"lab_id":LAB_ID,"discovery":disc,"oos_opened":False,"trading_authority":"NONE"}
    if disc["classification"]=="BASIS_CONVERGENCE_SURVIVES_DISCOVERY":
        oos=phase(2024,e24)
        terminal["oos_opened"]=True;terminal["oos"]=oos
        terminal["classification"]=oos["classification"]
    else:
        terminal["classification"]="DISCOVERY_"+disc["classification"]
    (OUT/"TERMINAL_REPORT.json").write_text(json.dumps(terminal,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("TERMINAL",json.dumps(terminal,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":
    main()

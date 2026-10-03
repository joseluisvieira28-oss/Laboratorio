#!/usr/bin/env python3
"""Premium Basis V1.4 bounded prospective watcher. Public directional shadow only."""
import argparse, hashlib, json, math, os, time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://contract.mexc.com"
SYMBOL="MUSTOCK_USDT"
STEP=300
ROLL_SEC=24*3600
ROLL_MAX=288
ROLL_MIN=240
FREEZE_BOUNDARY=int(datetime(2026,10,2,18,15,20,tzinfo=timezone.utc).timestamp())
CELLS=[
    {"id":"MU_10_Z1.0_FOLLOW","h":10,"th":1.0,"primary":True},
    {"id":"MU_10_Z1.5_FOLLOW","h":10,"th":1.5,"primary":False},
    {"id":"MU_10_Z2.0_FOLLOW","h":10,"th":2.0,"primary":False},
    {"id":"MU_30_Z1.5_FOLLOW","h":30,"th":1.5,"primary":False},
    {"id":"MU_30_Z2.0_FOLLOW","h":30,"th":2.0,"primary":False},
]

def utc(sec):
    return datetime.fromtimestamp(sec,tz=timezone.utc).isoformat().replace("+00:00","Z")

def sha(b):
    return hashlib.sha256(b).hexdigest()

class Evidence:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.entries=[]
    def save(self,name,raw,**meta):
        if isinstance(raw,str): raw=raw.encode()
        p=self.root/name;p.write_bytes(raw)
        row={"path":name,"sha256":sha(raw),"bytes":len(raw),**meta}
        self.entries.append(row);return row
    def journal(self,name,row):
        p=self.root/name
        with p.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
            f.flush();os.fsync(f.fileno())
    def finish(self,receipt):
        for p in sorted(self.root.glob("*.jsonl")):
            self.entries.append({"path":p.name,"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size})
        receipt["evidence"]=sorted(self.entries,key=lambda x:x["path"])
        (self.root/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:v for k,v in receipt.items() if k!="evidence"},indent=2,sort_keys=True),flush=True)

def fetch(kind,start,end,evidence,seq):
    route="index_price" if kind=="index" else "fair_price"
    url=f"{BASE}/api/v1/contract/kline/{route}/{SYMBOL}"
    params={"interval":"Min5","start":start,"end":end}
    r=requests.get(url,params=params,timeout=20)
    raw=r.content
    ref=evidence.save(f"{kind}-{seq:05d}.json",raw,source_url=r.url,http_status=r.status_code,received_at_utc=datetime.now(timezone.utc).isoformat())
    r.raise_for_status()
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise ValueError(f"{kind.upper()}_NON_SUCCESS")
    d=j.get("data") or {}
    out={}
    for s,p in zip(d.get("time") or [],d.get("close") or []):
        try:s=int(s);p=float(p)
        except Exception:continue
        mapped=s+STEP
        if mapped<=end and p>0 and math.isfinite(p):
            out[mapped]=p
    return out,ref

def build_z(index,fair):
    premium={}
    for t in sorted(set(index).intersection(fair)):
        ip=index[t];fp=fair[t]
        if ip>0 and math.isfinite(ip) and math.isfinite(fp):
            premium[t]=(fp-ip)/ip*10000.0
    z={};q=deque();s=ss=0.0
    for t in sorted(premium):
        x=premium[t];q.append((t,x));s+=x;ss+=x*x
        cutoff=t-ROLL_SEC+STEP
        while q and q[0][0]<cutoff:
            _,old=q.popleft();s-=old;ss-=old*old
        while len(q)>ROLL_MAX:
            _,old=q.popleft();s-=old;ss-=old*old
        n=len(q)
        if n<ROLL_MIN:continue
        mean=s/n
        var=(ss-n*mean*mean)/(n-1) if n>1 else 0.0
        if var<=0 or not math.isfinite(var):continue
        z[t]=(x-mean)/math.sqrt(var)
    return premium,z

def qualifies(cell,t,zv):
    return t>FREEZE_BOUNDARY and t%(cell["h"]*60)==0 and abs(zv)>=cell["th"] and zv!=0

def signal_id(cell,t):
    return hashlib.sha256(f'{cell["id"]}|{t}'.encode()).hexdigest()

def outcome(direction,entry,target):
    if target==entry:return "TIE"
    if direction=="UP":return "WIN" if target>entry else "LOSS"
    return "WIN" if target<entry else "LOSS"

def wilson_lower(w,l):
    n=w+l
    if n==0:return None
    p=w/n;z=1.959963984540054;z2=z*z
    return (p+z2/(2*n)-z*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def summarize(rows):
    resolved=[r for r in rows if r.get("status")=="RESOLVED_PROSPECTIVE_INCLUDED"]
    w=sum(r["outcome"]=="WIN" for r in resolved);l=sum(r["outcome"]=="LOSS" for r in resolved);ties=sum(r["outcome"]=="TIE" for r in resolved)
    n=w+l
    return {"resolved_included":len(resolved),"wins":w,"losses":l,"ties":ties,
            "accuracy":w/n if n else None,"wilson95_lower":wilson_lower(w,l),
            "ev80":((w*.8-l)/(w+l+ties)) if (w+l+ties) else None}

def run(duration,poll,output):
    if duration<=0 or duration>10800:raise SystemExit("duration outside frozen initial batch")
    ev=Evidence(output);started=time.time();deadline=time.monotonic()+duration
    seen={};source_errors=[];polls=0;rule_deviations=0
    first_included=None;latest_included=None

    while True:
        now=time.time()
        # enough warmup for exact 24h state plus margin; no outcome relevance before boundary
        start=int(now)-31*3600
        end=int(now)
        polls+=1
        try:
            index,iref=fetch("index",start,end,ev,polls)
            fair,fref=fetch("fair",start,end,ev,polls)
            premium,z=build_z(index,fair)
            common=sorted(set(index).intersection(fair))
            latest=max(common) if common else None
            ev.journal("polls.jsonl",{"poll":polls,"observed_at_utc":datetime.now(timezone.utc).isoformat(),
                "index_rows":len(index),"fair_rows":len(fair),"z_rows":len(z),"latest_mapped_ts":latest,
                "index_sha256":iref["sha256"],"fair_sha256":fref["sha256"]})

            first_seen=time.time()
            for cell in CELLS:
                for t,zv in sorted(z.items()):
                    if not qualifies(cell,t,zv):continue
                    sid=signal_id(cell,t)
                    if sid in seen:continue
                    target=t+cell["h"]*60
                    direction="UP" if zv>0 else "DOWN"
                    row={"signal_id":sid,"cell_id":cell["id"],"primary":cell["primary"],
                         "model_entry_ts":t,"model_entry_utc":utc(t),
                         "first_seen_at_ts":first_seen,"first_seen_at_utc":utc(first_seen),
                         "detection_latency_seconds":first_seen-t,
                         "z_score":zv,"premium_bps":premium[t],"direction":direction,
                         "entry_public_index":index[t],"target_ts":target,"target_utc":utc(target),
                         "source_index_sha256":iref["sha256"],"source_fair_sha256":fref["sha256"]}
                    if first_seen>=target:
                        row["status"]="LATE_DISCOVERY_EXCLUDED"
                    else:
                        row["status"]="PROSPECTIVE_INCLUDED_PENDING"
                        first_included=t if first_included is None else min(first_included,t)
                        latest_included=t if latest_included is None else max(latest_included,t)
                    seen[sid]=row;ev.journal("signal_ledger.jsonl",{"event":"FIRST_SEEN",**row})

            for sid,row in list(seen.items()):
                if row["status"]!="PROSPECTIVE_INCLUDED_PENDING":continue
                target=row["target_ts"]
                if target not in index:continue
                out=outcome(row["direction"],row["entry_public_index"],index[target])
                row.update(status="RESOLVED_PROSPECTIVE_INCLUDED",outcome=out,target_public_index=index[target],
                           resolution_observed_at_ts=time.time(),resolution_observed_at_utc=datetime.now(timezone.utc).isoformat(),
                           resolution_latency_seconds=time.time()-target,
                           resolution_index_source_sha256=iref["sha256"])
                ev.journal("signal_ledger.jsonl",{"event":"RESOLVED",**row})
        except Exception as exc:
            err={"poll":polls,"observed_at_utc":datetime.now(timezone.utc).isoformat(),
                 "type":type(exc).__name__,"error":str(exc)}
            source_errors.append(err);ev.journal("source_errors.jsonl",err)

        if time.monotonic()>=deadline:break
        time.sleep(min(poll,max(0,deadline-time.monotonic())))

    rows=list(seen.values())
    primary=[r for r in rows if r["primary"]]
    primary_summary=summarize(primary)
    included=[r for r in primary if r["status"] in ("PROSPECTIVE_INCLUDED_PENDING","RESOLVED_PROSPECTIVE_INCLUDED")]
    span_days=((max(r["model_entry_ts"] for r in included)-min(r["model_entry_ts"] for r in included))/86400) if len(included)>=2 else 0.0
    readiness=bool(
        primary_summary["resolved_included"]>=500 and span_days>=14
        and primary_summary["accuracy"] is not None and primary_summary["accuracy"]>1/1.8
        and primary_summary["wilson95_lower"] is not None and primary_summary["wilson95_lower"]>0.5
        and primary_summary["ev80"] is not None and primary_summary["ev80"]>0
        and not source_errors and rule_deviations==0
    )
    receipt={
      "lab":"MEXC_EVENT_FUTURES_PREMIUM_BASIS_V1.4_FORWARD",
      "freeze_boundary_utc":"2026-10-02T18:15:20Z",
      "duration_seconds":duration,"poll_seconds":poll,"polls":polls,
      "signals_first_seen":len(rows),
      "late_discovery_excluded":sum(r["status"]=="LATE_DISCOVERY_EXCLUDED" for r in rows),
      "prospective_included_pending":sum(r["status"]=="PROSPECTIVE_INCLUDED_PENDING" for r in rows),
      "prospective_included_resolved":sum(r["status"]=="RESOLVED_PROSPECTIVE_INCLUDED" for r in rows),
      "primary":primary_summary,"primary_span_days":span_days,
      "source_errors":source_errors,"rule_deviations":rule_deviations,
      "readiness_gate_pass":readiness,
      "verdict":"MICRO_LIVE_PRODUCT_SEMANTICS_REVIEW_ELIGIBLE" if readiness else "FORWARD_EVIDENCE_ACCUMULATING",
      "event_futures_orders":0,"authenticated_calls":0,"account_reads":0,"live_trading":0,
      "exact_event_futures_outcomes_opened":0,
      "directional_public_index_shadow_only":True
    }
    ev.finish(receipt)

def selftest():
    idx={};fair={}
    start=1_800_000_000
    for i in range(300):
        t=start+i*STEP
        idx[t]=100.0
        fair[t]=100.0+(i%17)/1000
    premium,z=build_z(idx,fair)
    assert len(z)>0
    cell=CELLS[0]
    t=next(iter(sorted(z)))
    assert signal_id(cell,t)==signal_id(cell,t)
    assert outcome("UP",100,101)=="WIN" and outcome("DOWN",100,99)=="WIN"
    print("PREMIUM_BASIS_V14_WATCHER_SELFTEST_PASS; SYNTHETIC_ONLY")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--duration-seconds",type=int)
    ap.add_argument("--poll-seconds",type=int,default=30)
    ap.add_argument("--output")
    a=ap.parse_args()
    if a.self_test:selftest()
    else:
        if not a.duration_seconds or not a.output:ap.error("--duration-seconds and --output required")
        run(a.duration_seconds,a.poll_seconds,a.output)

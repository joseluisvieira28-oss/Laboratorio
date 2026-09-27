#!/usr/bin/env python3
import csv, hashlib, io, json, math, os, re, statistics, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timedelta, timezone

UTC=timezone.utc
UA="CryptoLab-CMM-MECH-001/0.1 diagnostic-only"
BASE=os.path.dirname(__file__)
OUT=os.path.join(BASE,"mech001_results")
os.makedirs(OUT,exist_ok=True)

RM_PATH=os.path.join(BASE,"resolution_map_results","CMM_RM_001_EVENT_RESOLUTION_LEDGER_V01.csv")
DRV_PATH=os.path.join(BASE,"drv001_results","CMM_DRV_001_2025_CYCLE_IDENTITY_LEDGER_V01.csv")
RM_BLOB="349a4227f67c316853057771784763f48a88a8fe"
DRV_BLOB="9414176be46ee967b63b3cc8952b53e3db4eb3bc"

def git_blob(b):
    return hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()

def get_bytes(url,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read(),r.status
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(0.5*(i+1))
    raise last

def parse_checksum(b):
    t=b.decode("utf-8","replace").strip()
    x=t.split()[0].lower() if t else ""
    return x if re.fullmatch(r"[0-9a-f]{64}",x) else None

def download_zip(url):
    b,s=get_bytes(url); cb,cs=get_bytes(url+".CHECKSUM")
    exp=parse_checksum(cb); act=hashlib.sha256(b).hexdigest()
    if s!=200 or cs!=200 or exp!=act:
        raise RuntimeError(f"CHECKSUM_FAIL {url}")
    z=zipfile.ZipFile(io.BytesIO(b))
    if z.testzip() is not None: raise RuntimeError(f"CRC_FAIL {url}")
    return z,{"url":url,"sha256":act}

def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        if m==12:y,m=y+1,1
        else:m+=1

def frac(xs):
    xs=list(xs)
    return sum(bool(x) for x in xs)/len(xs) if xs else None

def avg(xs):
    xs=[x for x in xs if x is not None and math.isfinite(x)]
    return statistics.fmean(xs) if xs else None

def med(xs):
    xs=[x for x in xs if x is not None and math.isfinite(x)]
    return statistics.median(xs) if xs else None

# Bind immutable identity ledgers.
with open(RM_PATH,"rb") as f: rm_b=f.read()
with open(DRV_PATH,"rb") as f: drv_b=f.read()
if git_blob(rm_b)!=RM_BLOB: raise SystemExit("RM_LEDGER_BLOB_MISMATCH")
if git_blob(drv_b)!=DRV_BLOB: raise SystemExit("DRV_LEDGER_BLOB_MISMATCH")

rm=list(csv.DictReader(io.StringIO(rm_b.decode("utf-8"))))
drv=list(csv.DictReader(io.StringIO(drv_b.decode("utf-8"))))

# Official 17:00 price source, including d-7 history.
spot={}
receipts=[]
errors=[]

def fetch_month(ym):
    y,m=ym; stamp=f"{y:04d}-{m:02d}"
    url=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{stamp}.zip"
    z,rec=download_zip(url)
    out=[]
    for member in z.namelist():
        if member.endswith("/"): continue
        raw=z.read(member).decode("utf-8-sig","replace")
        for row in csv.reader(io.StringIO(raw)):
            if len(row)<2: continue
            try:
                ts=int(row[0])
                if ts>10**14: ts//=1000
                dt=datetime.fromtimestamp(ts/1000,UTC)
                if dt.hour==17 and dt.minute==0:
                    out.append((dt.date(),float(row[1])))
            except Exception: pass
    return rec,out

start=date(2020,12,1); end=date(2025,12,31)
with ThreadPoolExecutor(max_workers=8) as ex:
    futs={ex.submit(fetch_month,ym):ym for ym in months(start,end)}
    for fut in as_completed(futs):
        ym=futs[fut]
        try:
            rec,pts=fut.result(); receipts.append(rec)
            for d,p in pts: spot[d]=p
        except Exception as e:
            errors.append({"month":f"{ym[0]:04d}-{ym[1]:02d}","error":repr(e)})

expected_months=61
source_pass=(len(receipts)==expected_months and not errors)
if not source_pass:
    out={"status":"SOURCE_FAILURE","receipts":len(receipts),"expected":expected_months,"errors":errors}
    with open(os.path.join(OUT,"CMM_MECH_001_RESULT_V01.json"),"w") as f: json.dump(out,f,indent=2)
    raise SystemExit(2)

def decomp(d,h,g0):
    s=1 if g0>0 else -1
    keys=(d,d+timedelta(days=h),d-timedelta(days=7),d-timedelta(days=7)+timedelta(days=h))
    if any(k not in spot for k in keys): return None
    p0,ph,pold0,poldh=(spot[k] for k in keys)
    r_new=math.log(ph/p0)
    r_roll=math.log(poldh/pold0)
    actual=-s*r_new
    roll=s*r_roll
    return {
        "actual_price_closure":actual,
        "rolloff_closure":roll,
        "raw_state_closure":actual+roll,
        "actual_return_bps":r_new*10000,
        "rolloff_segment_bps":r_roll*10000,
        "rolloff_abs_gt_actual_abs":abs(roll)>abs(actual),
        "actual_supports_closure":actual>0,
        "rolloff_supports_closure":roll>0,
    }

# Parent resolution-map decomposition.
parent_rows=[]
for r in rm:
    if str(r.get("available","")).lower()!="true": continue
    d=date.fromisoformat(r["event_date"]); h=int(r["horizon_days"]); g0=float(r["G0"])
    x=decomp(d,h,g0)
    if x is None: continue
    parent_rows.append({
        "event_date":r["event_date"],"block":r["block"],"horizon_days":h,
        "orientation":r["orientation"],"gap_shrank":str(r["gap_shrank"]).lower()=="true",
        "leader_if_shrank":r.get("leader_if_shrank") or "",
        **x
    })

def summarize(rows):
    if not rows:return {"n":0}
    return {
        "n":len(rows),
        "actual_price_support_rate":frac(r["actual_supports_closure"] for r in rows),
        "rolloff_support_rate":frac(r["rolloff_supports_closure"] for r in rows),
        "rolloff_abs_gt_actual_abs_rate":frac(r["rolloff_abs_gt_actual_abs"] for r in rows),
        "raw_state_closure_positive_rate":frac(r["raw_state_closure"]>0 for r in rows),
        "actual_price_closure_mean":avg(r["actual_price_closure"] for r in rows),
        "rolloff_closure_mean":avg(r["rolloff_closure"] for r in rows),
        "actual_return_bps_mean":avg(r["actual_return_bps"] for r in rows),
    }

parent_summary={}
for h in (1,3,7):
    allr=[r for r in parent_rows if r["horizon_days"]==h]
    spotled=[r for r in allr if r["leader_if_shrank"]=="SPOT_LED"]
    parent_summary[str(h)]={
        "all":summarize(allr),
        "state_space_SPOT_LED": {
            **summarize(spotled),
            "actual_price_against_closure_rate":frac(not r["actual_supports_closure"] for r in spotled),
            "raw_state_closure_positive_but_actual_against_rate":frac(
                (r["raw_state_closure"]>0 and not r["actual_supports_closure"]) for r in spotled
            )
        }
    }

# 2025 cycles, h=1. PnL ledger is never read.
drv_rows=[]
for r in drv:
    d=date.fromisoformat(r["d0"]); g0=float(r["G0"])
    x=decomp(d,1,g0)
    if x is None: continue
    drv_rows.append({
        "d0":r["d0"],"direction":r["direction"],
        "confirmed":str(r["confirmed"]).lower()=="true",
        "SC1_z":float(r["SC1"]) if r.get("SC1") not in ("",None) else None,
        "NC1_z":float(r["NC1"]) if r.get("NC1") not in ("",None) else None,
        **x
    })
drv_confirmed=[r for r in drv_rows if r["confirmed"]]

result={
    "lab_id":"CMM-MECH-001",
    "status":"DIAGNOSTIC_ONLY",
    "source_pass":True,
    "pnl_ledgers_read":False,
    "price_archive_months":len(receipts),
    "parent_2021_2024":parent_summary,
    "drv_2025":{
        "all_initial_cycles":summarize(drv_rows),
        "confirmed_only":summarize(drv_confirmed),
        "confirmed_identity_detail":drv_confirmed,
    },
    "governance":{
        "changes_parent_verdicts":False,
        "promotion_authority":False,
        "live_trading_authorized":False,
        "main_merge_authorized":False
    }
}

with open(os.path.join(OUT,"CMM_MECH_001_RESULT_V01.json"),"w",encoding="utf-8") as f:
    json.dump(result,f,indent=2,sort_keys=True)

fields=["event_date","block","horizon_days","orientation","gap_shrank","leader_if_shrank",
        "actual_price_closure","rolloff_closure","raw_state_closure","actual_return_bps",
        "rolloff_segment_bps","actual_supports_closure","rolloff_supports_closure","rolloff_abs_gt_actual_abs"]
with open(os.path.join(OUT,"CMM_MECH_001_PARENT_DECOMPOSITION_V01.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for r in parent_rows:w.writerow({k:r.get(k) for k in fields})

close=["# CMM-MECH-001 — SPOT-STATE ROLL-OFF AUDIT V0.1","",
       "**Status: DIAGNOSTIC ONLY — NO PROMOTION**","",
       "This audit reads no parent/child PnL ledger. It decomposes the trailing 7-day spot-state change into actual new BTC price movement versus the historical return segment rolling out of the window.",""]
for h in (1,3,7):
    x=parent_summary[str(h)]["state_space_SPOT_LED"]
    close += [f"## Parent state-space SPOT_LED — {h}d",
              f"- N: {x['n']}",
              f"- Actual BTC price supported closure: {100*x['actual_price_support_rate']:.2f}%" if x.get("actual_price_support_rate") is not None else "- Actual BTC price supported closure: NA",
              f"- Roll-off supported closure: {100*x['rolloff_support_rate']:.2f}%" if x.get("rolloff_support_rate") is not None else "- Roll-off supported closure: NA",
              f"- |roll-off| > |actual price move|: {100*x['rolloff_abs_gt_actual_abs_rate']:.2f}%" if x.get("rolloff_abs_gt_actual_abs_rate") is not None else "- dominance: NA",
              f"- State-space SPOT_LED while actual price moved against closure: {100*x['actual_price_against_closure_rate']:.2f}%" if x.get("actual_price_against_closure_rate") is not None else "- contradiction: NA",""]
x=summarize(drv_confirmed)
close += ["## 2025 dynamic confirmed cycles — first 24h",
          f"- N: {x['n']}",
          f"- Actual BTC price supported closure: {100*x['actual_price_support_rate']:.2f}%" if x.get("actual_price_support_rate") is not None else "- Actual BTC price supported closure: NA",
          f"- Roll-off supported closure: {100*x['rolloff_support_rate']:.2f}%" if x.get("rolloff_support_rate") is not None else "- Roll-off supported closure: NA",
          f"- |roll-off| > |actual price move|: {100*x['rolloff_abs_gt_actual_abs_rate']:.2f}%" if x.get("rolloff_abs_gt_actual_abs_rate") is not None else "- dominance: NA","",
          "## Interpretation boundary",
          "This can diagnose whether the spot-state proxy is mechanically contaminated. It cannot rescue any strategy or create a new signal from favorable subgroups.",
          "Any next candidate requires a new pre-outcome freeze."]
with open(os.path.join(OUT,"CMM_MECH_001_CLOSEOUT_V01.md"),"w",encoding="utf-8") as f:
    f.write("\n".join(close)+"\n")

print(json.dumps(result,indent=2,sort_keys=True))

#!/usr/bin/env python3
import csv
import hashlib
import io
import json
import math
import os
import random
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timedelta, timezone

LAB_ID = "CMM-DRV-001-V01"
AUTHORITY = "CMM_DRV_001_2025_OOS_AUTHORITY_V01"
OUT_DIR = os.path.join(os.path.dirname(__file__), "drv001_results")
os.makedirs(OUT_DIR, exist_ok=True)
UTC = timezone.utc
UA = "CryptoLab-CMM-DRV-001/0.1 research-only"

YEAR_START = date(2025, 1, 1)
YEAR_END = date(2025, 12, 31)
LAST_INITIAL_DAY = date(2025, 12, 28)
SPOT_FETCH_START = date(2024, 12, 1)
SPOT_FETCH_END = YEAR_END
COST_BPS = 10.0
STRESS_BPS = 20.0
BOOT_N = 10000
BOOT_SEED = 20260925
EXPECTED_PARENT_DAILY_GIT_BLOB = "c30a38638dcbd8dd33a5a627ad15a3a7096011ca"
PARENT_DAILY = os.path.join(os.path.dirname(__file__), "discovery_results", "CMM001_DAILY_STATE_LEDGER_V01.csv")

def daterange(a, b):
    d=a
    while d<=b:
        yield d
        d += timedelta(days=1)

def months(a,b):
    y,m=a.year,a.month
    while (y,m) <= (b.year,b.month):
        yield y,m
        if m==12:
            y,m=y+1,1
        else:
            m+=1

def get_bytes(url, timeout=60, retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url, headers={"User-Agent":UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), dict(r.headers), r.status
        except Exception as e:
            last=e
            if i+1 < retries:
                time.sleep(0.5*(i+1))
    raise last

def get_json(url, timeout=60, retries=4):
    b,h,s=get_bytes(url,timeout,retries)
    return json.loads(b.decode("utf-8")),h,s

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def git_blob_sha1_bytes(b):
    head=f"blob {len(b)}\0".encode("utf-8")
    return hashlib.sha1(head+b).hexdigest()

def parse_checksum(b):
    t=b.decode("utf-8","replace").strip()
    if not t:
        return None
    x=t.split()[0].lower()
    return x if re.fullmatch(r"[0-9a-f]{64}",x) else None

def download_zip_verified(url):
    b,_,s=get_bytes(url)
    cb,_,cs=get_bytes(url+".CHECKSUM")
    exp=parse_checksum(cb)
    act=sha256_bytes(b)
    if s != 200 or cs != 200 or exp != act:
        raise RuntimeError(f"CHECKSUM_FAIL {url} expected={exp} actual={act} http={s}/{cs}")
    z=zipfile.ZipFile(io.BytesIO(b))
    bad=z.testzip()
    if bad is not None:
        raise RuntimeError(f"ZIP_CRC_FAIL {url} member={bad}")
    return z, {"url":url,"sha256":act,"checksum_ok":True,"members":z.namelist()}

def percentile_linear(values,q):
    xs=sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    if not xs:
        return None
    if len(xs)==1:
        return xs[0]
    pos=(len(xs)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:
        return xs[lo]
    w=pos-lo
    return xs[lo]*(1-w)+xs[hi]*w

def robust_z(current,hist):
    if current is None or len(hist)<180:
        return None
    ref=list(hist)[-180:]
    med=statistics.median(ref)
    mad=statistics.median([abs(x-med) for x in ref])
    scale=1.4826*mad
    if not math.isfinite(scale) or scale<=0:
        return None
    z=(current-med)/scale
    return max(-5.0,min(5.0,z))

def safe_float(x):
    if x in (None,""):
        return None
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def profit_factor(vals):
    pos=sum(x for x in vals if x>0)
    neg=-sum(x for x in vals if x<0)
    if neg==0:
        return float("inf") if pos>0 else 0.0
    return pos/neg

def sanitize(obj):
    if isinstance(obj,float):
        if math.isnan(obj): return "NaN"
        if math.isinf(obj): return "INF" if obj>0 else "-INF"
        return obj
    if isinstance(obj,dict):
        return {k:sanitize(v) for k,v in obj.items()}
    if isinstance(obj,list):
        return [sanitize(v) for v in obj]
    return obj

def metrics(events):
    vals=[e["net10_bps"] for e in events]
    stress=[e["stress20_bps"] for e in events]
    pos=[x for x in vals if x>0]
    conc=max(pos)/sum(pos) if pos and sum(pos)>0 else None
    return {
        "n":len(events),
        "mean_net10_bps":statistics.fmean(vals) if vals else None,
        "median_net10_bps":statistics.median(vals) if vals else None,
        "pf_net10":profit_factor(vals),
        "positive_fraction":sum(x>0 for x in vals)/len(vals) if vals else None,
        "mean_stress20_bps":statistics.fmean(stress) if stress else None,
        "pf_stress20":profit_factor(stress),
        "largest_positive_net_share":conc,
    }

# ---------------------------------------------------------
# 0. PARENT WARMUP IDENTITY — NO EVENT LEDGER / NO PNL READ
# ---------------------------------------------------------
with open(PARENT_DAILY,"rb") as fh:
    parent_bytes=fh.read()
parent_blob=git_blob_sha1_bytes(parent_bytes)
if parent_blob != EXPECTED_PARENT_DAILY_GIT_BLOB:
    raise SystemExit(f"FAIL_CLOSED_PARENT_DAILY_BLOB_MISMATCH expected={EXPECTED_PARENT_DAILY_GIT_BLOB} actual={parent_blob}")

parent_rows=[]
reader=csv.DictReader(io.StringIO(parent_bytes.decode("utf-8")))
allowed={"date","S_raw","O_raw","R_raw","L_raw","G"}
for r in reader:
    d=date.fromisoformat(r["date"])
    if d > date(2024,12,31):
        raise SystemExit("FAIL_CLOSED_PARENT_DAILY_CONTAINS_POST_2024")
    parent_rows.append({
        "date":d,
        "S_raw":safe_float(r.get("S_raw")),
        "O_raw":safe_float(r.get("O_raw")),
        "R_raw":safe_float(r.get("R_raw")),
        "L_raw":safe_float(r.get("L_raw")),
        "G":safe_float(r.get("G")),
    })

hist={k:deque(maxlen=180) for k in ("S","O","R","L")}
g_hist=[]
for r in sorted(parent_rows,key=lambda x:x["date"]):
    for k,col in (("S","S_raw"),("O","O_raw"),("R","R_raw"),("L","L_raw")):
        v=r[col]
        if v is not None:
            hist[k].append(v)
    if r["G"] is not None:
        g_hist.append(r["G"])

if any(len(hist[k])<180 for k in hist) or len(g_hist)<180:
    raise SystemExit("FAIL_CLOSED_PARENT_WARMUP_INSUFFICIENT")

# ------------------------------------
# 1. BINANCE SPOT 1H — SOURCE ONLY
# ------------------------------------
spot_open={}
spot_receipts=[]
spot_errors=[]

def fetch_spot_month(ym):
    y,m=ym
    stamp=f"{y:04d}-{m:02d}"
    url=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{stamp}.zip"
    z,rec=download_zip_verified(url)
    pts=[]
    for member in z.namelist():
        if member.endswith("/"): continue
        raw=z.read(member).decode("utf-8-sig","replace")
        for row in csv.reader(io.StringIO(raw)):
            if len(row)<2: continue
            try:
                ts=int(row[0])
                # Binance Spot archives use microseconds from 2025 onward.
                if ts > 10**14:
                    ts = ts // 1000
                px=float(row[1])
                dt=datetime.fromtimestamp(ts/1000.0,UTC)
                pts.append((dt,px))
            except Exception:
                continue
    return rec,pts

spot_months=list(months(SPOT_FETCH_START,SPOT_FETCH_END))
with ThreadPoolExecutor(max_workers=8) as ex:
    futs={ex.submit(fetch_spot_month,ym):ym for ym in spot_months}
    for fut in as_completed(futs):
        ym=futs[fut]
        try:
            rec,pts=fut.result()
            spot_receipts.append(rec)
            for dt,px in pts:
                if SPOT_FETCH_START <= dt.date() <= SPOT_FETCH_END:
                    spot_open[dt]=px
        except Exception as e:
            spot_errors.append({"month":f"{ym[0]:04d}-{ym[1]:02d}","error":repr(e)})

# -----------------------
# 2. FRED DGS2 — CORE
# -----------------------
fred_url="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd=2024-11-01&coed=2025-12-31"
fred_b,_,fred_status=get_bytes(fred_url)
fred=[]
for r in csv.DictReader(io.StringIO(fred_b.decode("utf-8-sig"))):
    ds=r.get("DATE") or r.get("observation_date")
    try:
        fred.append((date.fromisoformat(ds),float(r.get("DGS2"))))
    except Exception:
        pass
fred.sort()
fred_dates=[d for d,_ in fred]; fred_vals=[v for _,v in fred]

def latest_idx(dates,cut):
    lo,hi,ans=0,len(dates)-1,None
    while lo<=hi:
        mid=(lo+hi)//2
        if dates[mid]<=cut:
            ans=mid; lo=mid+1
        else:
            hi=mid-1
    return ans

rates_raw={}
for d in daterange(YEAR_START,YEAR_END):
    i=latest_idx(fred_dates,d-timedelta(days=1))
    if i is not None and i>=5:
        rates_raw[d]=-(fred_vals[i]-fred_vals[i-5])

# ---------------------------------
# 3. DEFILLAMA STABLECOINS — CORE
# ---------------------------------
llama_url="https://stablecoins.llama.fi/stablecoincharts/all"
llama,_,llama_status=get_json(llama_url)
stable=[]
for x in llama if isinstance(llama,list) else []:
    try:
        d=datetime.fromtimestamp(int(x["date"]),UTC).date()
        v=float(x["totalCirculatingUSD"]["peggedUSD"])
        if math.isfinite(v) and v>0 and date(2024,11,1) <= d <= YEAR_END:
            stable.append((d,v))
    except Exception:
        pass
stable.sort()
stable_dates=[d for d,_ in stable]; stable_vals=[v for _,v in stable]

liquidity_raw={}
for d in daterange(YEAR_START,YEAR_END):
    i1=latest_idx(stable_dates,d-timedelta(days=1))
    i0=latest_idx(stable_dates,d-timedelta(days=31))
    if i1 is not None and i0 is not None and stable_vals[i1]>0 and stable_vals[i0]>0:
        liquidity_raw[d]=math.log(stable_vals[i1]/stable_vals[i0])

# ----------------------------
# 4. DERIBIT OPTIONS — CORE
# ----------------------------
inst_re=re.compile(r"^BTC-(\d{1,2}[A-Z]{3}\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$")
option_raw={}
option_meta={}
option_errors=[]
option_truncated=[]

def fetch_option_day(d):
    start_dt=datetime.combine(d,dtime(15,0),UTC)
    end_dt=datetime.combine(d,dtime(17,0),UTC)-timedelta(milliseconds=1)
    q=urllib.parse.urlencode({
        "currency":"BTC","kind":"option",
        "start_timestamp":int(start_dt.timestamp()*1000),
        "end_timestamp":int(end_dt.timestamp()*1000),
        "count":10000,"include_old":"true","sorting":"asc",
    })
    url="https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time?"+q
    data,_,status=get_json(url,75,4)
    rr=data.get("result",{})
    trades=rr.get("trades",[])
    has_more=bool(rr.get("has_more",False))
    calls=[]; puts=[]; eligible=0
    for t in trades:
        try:
            name=str(t.get("instrument_name",""))
            m=inst_re.match(name)
            if not m: continue
            trade_ts=datetime.fromtimestamp(int(t["timestamp"])/1000.0,UTC)
            expiry=datetime.strptime(m.group(1),"%d%b%y").replace(tzinfo=UTC,hour=8)
            strike=float(m.group(2)); cp=m.group(3)
            idx=float(t["index_price"]); iv=float(t["iv"])
            dte=(expiry-trade_ts).total_seconds()/86400.0
            if not(7<=dte<=45) or idx<=0 or not math.isfinite(iv):
                continue
            ratio=strike/idx
            eligible+=1
            if cp=="C" and 1.05<=ratio<=1.20:
                calls.append(iv)
            elif cp=="P" and 0.80<=ratio<=0.95:
                puts.append(iv)
        except Exception:
            continue
    raw=None
    if len(calls)>=5 and len(puts)>=5:
        raw=-(statistics.median(puts)-statistics.median(calls))
    return d,raw,{
        "http_status":status,"trades":len(trades),"eligible_any":eligible,
        "eligible_calls":len(calls),"eligible_puts":len(puts),"has_more":has_more
    }

days=list(daterange(YEAR_START,YEAR_END))
with ThreadPoolExecutor(max_workers=6) as ex:
    futs={ex.submit(fetch_option_day,d):d for d in days}
    done=0
    for fut in as_completed(futs):
        d=futs[fut]
        try:
            dd,raw,meta=fut.result()
            option_meta[dd]=meta
            if meta["has_more"]:
                option_truncated.append(dd.isoformat())
            if raw is not None:
                option_raw[dd]=raw
        except Exception as e:
            option_errors.append({"date":d.isoformat(),"error":repr(e)})
        done+=1
        if done%100==0:
            print(f"OPTIONS_PROGRESS {done}/{len(days)}",flush=True)

# -----------------------------
# 5. 2025 RAW SPOT STATE
# -----------------------------
spot_state_raw={}
for d in daterange(YEAR_START,YEAR_END):
    dt=datetime.combine(d,dtime(17,0),UTC)
    dt7=datetime.combine(d-timedelta(days=7),dtime(17,0),UTC)
    if dt in spot_open and dt7 in spot_open and spot_open[dt]>0 and spot_open[dt7]>0:
        spot_state_raw[d]=math.log(spot_open[dt]/spot_open[dt7])

# ------------------------------------------------------
# 6. BUILD COMPLETE 2025 STATE PATH — NO PNL CALCULATION
# ------------------------------------------------------
state_rows=[]
state_by_date={}
for d in daterange(YEAR_START,YEAR_END):
    raws={"S":spot_state_raw.get(d),"O":option_raw.get(d),"R":rates_raw.get(d),"L":liquidity_raw.get(d)}
    zs={k:robust_z(raws[k],hist[k]) for k in hist}
    nonspot=[zs[k] for k in ("O","R","L") if zs[k] is not None]
    nstate=statistics.median(nonspot) if len(nonspot)>=2 else None
    g=zs["S"]-nstate if zs["S"] is not None and nstate is not None else None
    q95=percentile_linear([abs(x) for x in g_hist],0.95) if len(g_hist)>=180 else None
    extreme=bool(d<=LAST_INITIAL_DAY and g is not None and q95 is not None and abs(g)>q95 and g!=0)
    row={
        "date":d,"S_raw":raws["S"],"O_raw":raws["O"],"R_raw":raws["R"],"L_raw":raws["L"],
        "S_z":zs["S"],"O_z":zs["O"],"R_z":zs["R"],"L_z":zs["L"],
        "N":nstate,"G":g,"q95":q95,"extreme":extreme
    }
    state_rows.append(row); state_by_date[d]=row
    if g is not None:
        g_hist.append(g)
    for k in hist:
        if raws[k] is not None and math.isfinite(raws[k]):
            hist[k].append(raws[k])

# --------------------------------------------------------
# 7. IDENTIFY CYCLES + CONFIRMATIONS WITHOUT USING OUTCOMES
# --------------------------------------------------------
cycles=[]
pending=None
blocked_until=date(2024,12,31)

for d in daterange(YEAR_START,YEAR_END):
    row=state_by_date[d]

    if pending is not None and d == pending["d0"]+timedelta(days=1):
        r0=state_by_date[pending["d0"]]
        r1=row
        confirmed=False
        sc=nc=None
        reasons=[]
        if r1["G"] is None or r1["G"]==0:
            reasons.append("G1_INVALID_OR_ZERO")
        elif (1 if r1["G"]>0 else -1) != pending["sign"]:
            reasons.append("GAP_ALREADY_CROSSED")
        else:
            if abs(r1["G"]) >= abs(pending["G0"]):
                reasons.append("GAP_NOT_SHRINKING")
            sc=pending["sign"]*(r0["S_z"]-r1["S_z"]) if r0["S_z"] is not None and r1["S_z"] is not None else None
            nc=pending["sign"]*(r1["N"]-r0["N"]) if r0["N"] is not None and r1["N"] is not None else None
            if sc is None or sc<=0:
                reasons.append("SPOT_NOT_CLOSING")
            if sc is None or nc is None or sc<=nc:
                reasons.append("SPOT_NOT_LEADING")
            if not reasons:
                confirmed=True

        cycle=dict(pending)
        cycle.update({
            "confirm_date":d,"G1":r1["G"],"SC1":sc,"NC1":nc,
            "confirmed":confirmed,
            "no_entry_reasons":reasons,
            "entry_dt":datetime.combine(d,dtime(18,0),UTC) if confirmed else None,
            "exit_dt":datetime.combine(pending["d0"]+timedelta(days=3),dtime(18,0),UTC) if confirmed else None,
        })
        cycles.append(cycle)
        pending=None
        blocked_until=(cycle["d0"]+timedelta(days=3)) if confirmed else d
        continue

    if pending is None and d>blocked_until and row["extreme"]:
        pending={
            "d0":d,"G0":row["G"],"q95_0":row["q95"],
            "sign":1 if row["G"]>0 else -1,
            "direction":-1 if row["G"]>0 else 1,
            "S0":row["S_z"],"N0":row["N"],
        }

# Any unresolved last-day pending is a no-entry source/state observation.
if pending is not None:
    cycles.append({**pending,"confirm_date":pending["d0"]+timedelta(days=1),"G1":None,"SC1":None,"NC1":None,
                   "confirmed":False,"no_entry_reasons":["CONFIRMATION_OUTSIDE_AUTHORIZED_2025_WINDOW"],
                   "entry_dt":None,"exit_dt":None})

confirmed=[c for c in cycles if c["confirmed"]]

# --------------------------------------------
# 8. FULL SOURCE/INTEGRITY FIREWALL
# --------------------------------------------
required_state_hours=0
present_state_hours=0
for d in daterange(YEAR_START,YEAR_END):
    required_state_hours+=1
    if datetime.combine(d,dtime(17,0),UTC) in spot_open:
        present_state_hours+=1

required_outcome_hours=0
present_outcome_hours=0
for c in confirmed:
    for dt in (c["entry_dt"],c["exit_dt"]):
        required_outcome_hours+=1
        if dt in spot_open:
            present_outcome_hours+=1

spot_state_avail=present_state_hours/required_state_hours if required_state_hours else 0
spot_outcome_avail=present_outcome_hours/required_outcome_hours if required_outcome_hours else 1
option_cov=len(option_raw)/len(days) if days else 0

source_gates={
    "parent_daily_blob_match":parent_blob==EXPECTED_PARENT_DAILY_GIT_BLOB,
    "spot_13_month_checksums":len(spot_receipts)==13 and not spot_errors,
    "spot_state_17h_availability_ge_99_5pct":spot_state_avail>=0.995,
    "spot_confirmed_entry_exit_availability_100pct":spot_outcome_avail==1.0,
    "deribit_zero_transport_parse_errors":len(option_errors)==0,
    "deribit_zero_has_more_truncation":len(option_truncated)==0,
    "deribit_oraw_coverage_ge_75pct":option_cov>=0.75,
    "fred_source_readable":fred_status==200 and len(fred)>=250,
    "defillama_source_readable":llama_status==200 and len(stable)>=390,
    "no_2026_source_fetched":all("2026" not in r["url"] for r in spot_receipts),
}

source_report={
    "lab_id":LAB_ID,"authority":AUTHORITY,
    "generated_at_utc":datetime.now(UTC).isoformat(),
    "outcomes_opened":False,
    "parent_daily_git_blob":parent_blob,
    "parent_event_ledger_read":False,
    "source_gates":source_gates,
    "source_pass":all(source_gates.values()),
    "spot":{"receipts":len(spot_receipts),"errors":spot_errors,"state_availability":spot_state_avail,
            "confirmed_outcome_hour_availability":spot_outcome_avail},
    "options":{"requested_days":len(days),"valid_oraw_days":len(option_raw),"coverage":option_cov,
               "errors":option_errors[:50],"error_count":len(option_errors),
               "truncated_days":option_truncated[:50],"truncated_count":len(option_truncated)},
    "fred":{"status":fred_status,"numeric_observations":len(fred)},
    "stablecoin":{"status":llama_status,"dated_observations":len(stable)},
    "cycle_counts":{"initial_cycles":len(cycles),"confirmed_entries":len(confirmed)},
    "protected_2026":"LOCKED_NOT_FETCHED",
}

source_path=os.path.join(OUT_DIR,"CMM_DRV_001_2025_SOURCE_REPORT_V01.json")
with open(source_path,"w",encoding="utf-8") as fh:
    json.dump(sanitize(source_report),fh,indent=2,sort_keys=True)

# State ledger is source-only and can be preserved even on failure.
state_path=os.path.join(OUT_DIR,"CMM_DRV_001_2025_STATE_LEDGER_V01.csv")
state_fields=["date","S_raw","O_raw","R_raw","L_raw","S_z","O_z","R_z","L_z","N","G","q95","extreme"]
with open(state_path,"w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=state_fields); w.writeheader()
    for r in state_rows:
        w.writerow({**r,"date":r["date"].isoformat()})

cycle_pre_path=os.path.join(OUT_DIR,"CMM_DRV_001_2025_CYCLE_IDENTITY_LEDGER_V01.csv")
cycle_fields=["d0","G0","q95_0","direction","confirm_date","G1","SC1","NC1","confirmed","no_entry_reasons","entry_dt","exit_dt"]
with open(cycle_pre_path,"w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=cycle_fields); w.writeheader()
    for c in cycles:
        w.writerow({
            "d0":c["d0"].isoformat(),"G0":c["G0"],"q95_0":c["q95_0"],
            "direction":"LONG" if c["direction"]==1 else "SHORT",
            "confirm_date":c["confirm_date"].isoformat(),"G1":c.get("G1"),"SC1":c.get("SC1"),"NC1":c.get("NC1"),
            "confirmed":c["confirmed"],"no_entry_reasons":";".join(c.get("no_entry_reasons",[])),
            "entry_dt":c["entry_dt"].isoformat() if c.get("entry_dt") else "",
            "exit_dt":c["exit_dt"].isoformat() if c.get("exit_dt") else "",
        })

if not source_report["source_pass"]:
    close=[
        "# CMM-DRV-001 — 2025 ONE-SHOT SOURCE CLOSEOUT V0.1","",
        "**STATE: SOURCE_INADEQUATE / OUTCOMES NOT OPENED**","",
        "The complete state path and cycle identities were constructed without PnL. One or more frozen source gates failed, so no 2025 economic outcome was computed.","",
        "## Gates"
    ]
    close += [f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in source_gates.items()]
    close += ["",f"Initial cycles: {len(cycles)}",f"Confirmed identities before outcome firewall: {len(confirmed)}",
              "","2026 remained locked. This is not a scientific market verdict."]
    with open(os.path.join(OUT_DIR,"CMM_DRV_001_2025_CLOSEOUT_V01.md"),"w",encoding="utf-8") as fh:
        fh.write("\n".join(close)+"\n")
    print(json.dumps({"state":"SOURCE_INADEQUATE","source_gates":source_gates,"outcomes_opened":False},indent=2))
    sys.exit(2)

# -----------------------------
# 9. OPEN AUTHORIZED OUTCOMES
# -----------------------------
source_report["outcomes_opened"]=True
with open(source_path,"w",encoding="utf-8") as fh:
    json.dump(sanitize(source_report),fh,indent=2,sort_keys=True)

events=[]
for c in confirmed:
    entry=spot_open[c["entry_dt"]]
    exitp=spot_open[c["exit_dt"]]
    gross=c["direction"]*((exitp/entry)-1.0)*10000.0
    ev=dict(c)
    ev.update(entry_price=entry,exit_price=exitp,gross_bps=gross,
              net10_bps=gross-COST_BPS,stress20_bps=gross-STRESS_BPS)
    events.append(ev)

m=metrics(events)

# Leave-one-trade-out minimum mean
loo_means=[]
if len(events)>1:
    for i in range(len(events)):
        vals=[e["net10_bps"] for j,e in enumerate(events) if j!=i]
        loo_means.append(statistics.fmean(vals))
loo_min=min(loo_means) if loo_means else None

# Monthly diagnostics
monthly={}
for month in range(1,13):
    evs=[e for e in events if e["entry_dt"].month==month]
    monthly[f"2025-{month:02d}"]={
        "n":len(evs),
        "mean_net10_bps":statistics.fmean([e["net10_bps"] for e in evs]) if evs else None
    }

# Direction counts
longs=sum(e["direction"]==1 for e in events)
shorts=sum(e["direction"]==-1 for e in events)

# Bootstrap
vals=[e["net10_bps"] for e in events]
rng=random.Random(BOOT_SEED)
boot=[]
if vals:
    n=len(vals)
    for _ in range(BOOT_N):
        boot.append(statistics.fmean([vals[rng.randrange(n)] for _ in range(n)]))
boot.sort()
bootstrap={
    "reps":BOOT_N,"seed":BOOT_SEED,
    "p_mean_le_zero":sum(x<=0 for x in boot)/len(boot) if boot else None,
    "p05":percentile_linear(boot,0.05) if boot else None,
    "p50":percentile_linear(boot,0.50) if boot else None,
    "p95":percentile_linear(boot,0.95) if boot else None,
}

adequate=m["n"]>=8
supportive=(
    adequate and m["mean_net10_bps"] is not None and m["mean_net10_bps"]>0
    and m["pf_net10"]>1.0
    and m["positive_fraction"] is not None and m["positive_fraction"]>=0.50
    and m["mean_stress20_bps"] is not None and m["mean_stress20_bps"]>0
    and m["largest_positive_net_share"] is not None and m["largest_positive_net_share"]<=0.50
)
contradicts=(adequate and m["mean_net10_bps"] is not None and m["mean_net10_bps"]<0 and m["pf_net10"]<1.0)

if not adequate:
    verdict="INSUFFICIENT_SAMPLE"
elif supportive:
    verdict="OOS_SUPPORTIVE__TIER3_HIGH_RESEARCH_CANDIDATE"
elif contradicts:
    verdict="OOS_CONTRADICTS"
else:
    verdict="OOS_MIXED__TIER3_LOW"

# Final event ledger
event_path=os.path.join(OUT_DIR,"CMM_DRV_001_2025_EVENT_LEDGER_V01.csv")
event_fields=["d0","confirm_date","direction","G0","q95_0","G1","SC1","NC1","entry_utc","exit_utc",
              "entry_price","exit_price","gross_bps","net10_bps","stress20_bps"]
with open(event_path,"w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=event_fields); w.writeheader()
    for e in events:
        w.writerow({
            "d0":e["d0"].isoformat(),"confirm_date":e["confirm_date"].isoformat(),
            "direction":"LONG" if e["direction"]==1 else "SHORT","G0":e["G0"],"q95_0":e["q95_0"],
            "G1":e["G1"],"SC1":e["SC1"],"NC1":e["NC1"],
            "entry_utc":e["entry_dt"].isoformat(),"exit_utc":e["exit_dt"].isoformat(),
            "entry_price":e["entry_price"],"exit_price":e["exit_price"],
            "gross_bps":e["gross_bps"],"net10_bps":e["net10_bps"],"stress20_bps":e["stress20_bps"],
        })

result={
    "lab_id":LAB_ID,"authority":AUTHORITY,"verdict":verdict,
    "source_pass":True,"outcomes_opened":True,
    "parent_verdict_unchanged":"CMM-001-V01 INSUFFICIENT_SAMPLE",
    "candidate_tier2_possible_from_this_run":False,
    "cycle_counts":{
        "initial_cycles":len(cycles),
        "confirmed_entries":len(events),
        "confirmation_rate":len(events)/len(cycles) if cycles else None,
    },
    "economics":m,
    "leave_one_trade_out_min_mean_net10_bps":loo_min,
    "monthly":monthly,
    "direction_counts":{"LONG":longs,"SHORT":shorts},
    "bootstrap":bootstrap,
    "sample_adequacy":{"min_entered_trades":8,"pass":adequate},
    "supportive_gates":{
        "mean_net10_gt_zero":m["mean_net10_bps"] is not None and m["mean_net10_bps"]>0,
        "pf_net10_gt_1":m["pf_net10"]>1,
        "positive_fraction_ge_50pct":m["positive_fraction"] is not None and m["positive_fraction"]>=0.5,
        "mean_stress20_gt_zero":m["mean_stress20_bps"] is not None and m["mean_stress20_bps"]>0,
        "largest_positive_share_le_50pct":m["largest_positive_net_share"] is not None and m["largest_positive_net_share"]<=0.5,
    },
    "protected_2026":"LOCKED_NOT_FETCHED",
    "governance":{
        "live_trading_authorized":False,"micro_live_authorized":False,
        "tier2_authorized":False,"main_merge_authorized":False,"rescue_authorized":False
    }
}

# Evidence hashes
for p in (source_path,state_path,cycle_pre_path,event_path):
    with open(p,"rb") as fh:
        result.setdefault("evidence_sha256",{})[os.path.basename(p)]=sha256_bytes(fh.read())

result_path=os.path.join(OUT_DIR,"CMM_DRV_001_2025_RESULT_V01.json")
with open(result_path,"w",encoding="utf-8") as fh:
    json.dump(sanitize(result),fh,indent=2,sort_keys=True)

def fmt(x,n=4):
    if x is None:return "NA"
    if isinstance(x,float) and math.isinf(x):return "INF"
    return f"{x:.{n}f}"

close=[
    "# CMM-DRV-001 — 2025 ONE-SHOT HOLDOUT CLOSEOUT V0.1","",
    f"**VERDICT: {verdict}**","",
    "Parent CMM-001 verdict remains INSUFFICIENT_SAMPLE and is not rescued by this child.","",
    "## Dynamic funnel",
    f"- Initial extreme-gap cycles: {len(cycles)}",
    f"- Confirmed spot-led shrinking-gap entries: {len(events)}",
    f"- Confirmation rate: {fmt((len(events)/len(cycles)*100) if cycles else None,2)}%","",
    "## Economics — confirmed entries only",
    f"- N: {m['n']}",
    f"- Mean NET10: {fmt(m['mean_net10_bps'])} bps",
    f"- Median NET10: {fmt(m['median_net10_bps'])} bps",
    f"- PF NET10: {fmt(m['pf_net10'])}",
    f"- Positive fraction: {fmt((m['positive_fraction']*100) if m['positive_fraction'] is not None else None,2)}%",
    f"- Mean STRESS20: {fmt(m['mean_stress20_bps'])} bps",
    f"- PF STRESS20: {fmt(m['pf_stress20'])}",
    f"- Largest positive contribution: {fmt((m['largest_positive_net_share']*100) if m['largest_positive_net_share'] is not None else None,2)}%",
    f"- Leave-one-trade-out minimum mean NET10: {fmt(loo_min)} bps","",
    "## Bootstrap",
    f"- 10,000 reps, seed {BOOT_SEED}",
    f"- P(mean <= 0): {fmt(bootstrap['p_mean_le_zero'],4)}",
    f"- p05 / median / p95: {fmt(bootstrap['p05'])} / {fmt(bootstrap['p50'])} / {fmt(bootstrap['p95'])} bps","",
    "## Governance",
    "- This run cannot grant Tier 2.",
    "- A supportive result is at most TIER 3 HIGH because the rule was generated from the 2021-2024 exploratory resolution map.",
    "- No parameter, component, direction, month or cost rescue is authorized.",
    "- 2026 remained locked.",
    "- No live trading, micro-live, orders, exchange mutation, alerts/webhooks, Render or main merge.",
]
close_path=os.path.join(OUT_DIR,"CMM_DRV_001_2025_CLOSEOUT_V01.md")
with open(close_path,"w",encoding="utf-8") as fh:
    fh.write("\n".join(close)+"\n")

with open(close_path,"rb") as fh:
    close_sha=sha256_bytes(fh.read())
with open(result_path,"rb") as fh:
    result_sha=sha256_bytes(fh.read())

print(json.dumps(sanitize({
    "verdict":verdict,"initial_cycles":len(cycles),"confirmed_entries":len(events),
    "economics":m,"bootstrap":bootstrap,"result_sha256":result_sha,"closeout_sha256":close_sha,
    "2026":"LOCKED_NOT_FETCHED"
}),indent=2))

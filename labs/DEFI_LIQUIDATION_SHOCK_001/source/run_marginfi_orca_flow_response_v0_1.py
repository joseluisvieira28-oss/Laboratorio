#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

SYMBOL="SOLUSDT"
START=dt.datetime(2024,7,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2024,10,1,tzinfo=dt.timezone.utc)
FOLD_CUT=dt.datetime(2024,9,1,tzinfo=dt.timezone.utc)
BOOT_N=20000
BOOT_RHO_SEED=26100101
BOOT_DELTA_SEED=26100102

ap=argparse.ArgumentParser()
ap.add_argument("--feature-root",required=True)
ap.add_argument("--workers",type=int,default=12)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_FLOW_RESPONSE_V01_RECEIPT.json"
LEDGER=OUT/"MARGINFI_ORCA_FLOW_RESPONSE_V01_LEDGER.ndjson"
MANIFEST=OUT/"MARGINFI_ORCA_FLOW_RESPONSE_V01_MARKET_DATA_MANIFEST.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def ms(t): return int(t.timestamp()*1000)

def http_bytes(url,retries=8):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-orca-flow-response-v01/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            last={"http":int(e.code)}
            if e.code in (429,500,502,503,504):
                time.sleep(min(30,2**i));continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]}
            time.sleep(min(30,2**i))
    return None,last

def acquire_day(day):
    ds=day.isoformat()
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    ss,sb=http_bytes(base+".CHECKSUM");zs,zb=http_bytes(base)
    rec={"date":ds,"checksum_http":ss,"zip_http":zs,"status":None,"bars":0}
    if ss!=200 or zs!=200 or not isinstance(sb,(bytes,bytearray)) or not isinstance(zb,(bytes,bytearray)):
        rec["status"]="TRANSPORT_FAIL";return rec,{}
    m=re.search(r"([0-9a-fA-F]{64})",sb.decode("utf-8","replace"))
    if not m:
        rec["status"]="CHECKSUM_FORMAT_INVALID";return rec,{}
    exp=m.group(1).lower();obs=hashlib.sha256(zb).hexdigest()
    rec["expected_sha256"]=exp;rec["observed_sha256"]=obs
    if exp!=obs:
        rec["status"]="CHECKSUM_MISMATCH";return rec,{}
    try:
        z=zipfile.ZipFile(io.BytesIO(zb));names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:
            rec["status"]="ZIP_MEMBER_COUNT_INVALID";return rec,{}
        day0=dt.datetime.combine(day,dt.time(0),tzinfo=dt.timezone.utc)
        lo=ms(day0);hi=lo+86400000
        bars={};prev=None;dup=0;nonmono=0
        with z.open(names[0]) as fh:
            rdr=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
            for row in rdr:
                if not row:continue
                if str(row[0]).strip().lower()=="open_time":continue
                t=int(row[0])
                if t>10**14:t//=1000
                if t%60000!=0 or not(lo<=t<hi):
                    rec["status"]="TIMESTAMP_INTEGRITY_FAIL";return rec,{}
                if prev is not None and t<=prev:
                    if t==prev:dup+=1
                    else:nonmono+=1
                prev=t
                if t in bars:dup+=1
                op=float(row[1])
                if op<=0:
                    rec["status"]="NONPOSITIVE_OPEN";return rec,{}
                bars[t]=op
        if dup or nonmono:
            rec.update({"status":"ARCHIVE_STRUCTURE_CONFLICT","duplicate_count":dup,"non_monotonic_count":nonmono});return rec,{}
        rec.update({"status":"PASS","bars":len(bars),"missing_minutes":1440-len(bars),
                    "duplicate_count":0,"non_monotonic_count":0})
        return rec,bars
    except Exception as e:
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:240]})
        return rec,{}

def crosses_funding(a,b):
    d=a.date()-dt.timedelta(days=1)
    while d<=b.date():
        for h in (0,8,16):
            f=dt.datetime(d.year,d.month,d.day,h,tzinfo=dt.timezone.utc)
            if a<=f<=b:return True
        d+=dt.timedelta(days=1)
    return False

def average_ranks(vals):
    n=len(vals);order=sorted(range(n),key=lambda i:vals[i]);r=[0.0]*n;i=0
    while i<n:
        j=i+1
        while j<n and vals[order[j]]==vals[order[i]]:j+=1
        avg=((i+1)+j)/2.0
        for k in range(i,j):r[order[k]]=avg
        i=j
    return r

def pearson(a,b):
    n=len(a)
    if n<2:return None
    ma=sum(a)/n;mb=sum(b)/n
    va=sum((x-ma)**2 for x in a);vb=sum((y-mb)**2 for y in b)
    if va<=0 or vb<=0:return None
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(va*vb)

def spearman(rows):
    if len(rows)<3:return None
    x=[r["x"] for r in rows];y=[r["y"] for r in rows]
    return pearson(average_ranks(x),average_ranks(y))

def pct_ci(vals):
    vals=sorted(v for v in vals if v is not None and math.isfinite(v))
    if not vals:return (None,None)
    def q(p):
        i=(len(vals)-1)*p;lo=int(math.floor(i));hi=int(math.ceil(i))
        if lo==hi:return vals[lo]
        return vals[lo]+(vals[hi]-vals[lo])*(i-lo)
    return q(.025),q(.975)

def block_boot_rho(rows):
    by=defaultdict(list)
    for r in rows:by[r["day"]].append(r)
    days=sorted(by);rng=random.Random(BOOT_RHO_SEED);vals=[]
    for _ in range(BOOT_N):
        sample=[]
        for __ in range(len(days)):
            sample.extend(by[days[rng.randrange(len(days))]])
        vals.append(spearman(sample))
    lo,hi=pct_ci(vals)
    return {"replicates":BOOT_N,"seed":BOOT_RHO_SEED,"day_count":len(days),"lower":lo,"upper":hi}

def block_boot_delta(rows):
    by=defaultdict(list)
    for r in rows:by[r["day"]].append(r)
    days=sorted(by);rng=random.Random(BOOT_DELTA_SEED);vals=[]
    for _ in range(BOOT_N):
        sample=[]
        for __ in range(len(days)):
            sample.extend(by[days[rng.randrange(len(days))]])
        top=[r["y"] for r in sample if r["quartile_group"]=="TOP"]
        bot=[r["y"] for r in sample if r["quartile_group"]=="BOTTOM"]
        if top and bot:vals.append(sum(top)/len(top)-sum(bot)/len(bot))
    lo,hi=pct_ci(vals)
    return {"replicates":BOOT_N,"seed":BOOT_DELTA_SEED,"day_count":len(days),"lower":lo,"upper":hi}

def sign(v):
    if v is None or v==0:return 0
    return 1 if v>0 else -1

prec=find_one(args.feature_root,"MARGINFI_ORCA_EXTREME_REBOUND_V01_PREOUTCOME_SELECTION_RECEIPT.json")
prows=find_one(args.feature_root,"MARGINFI_ORCA_EXTREME_REBOUND_V01_PREOUTCOME_SELECTION_ROWS.ndjson")
if prec is None or prows is None:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"feature_authority","errors":["preoutcome_artifact_missing_or_duplicate"]},indent=2)+"\n")
    raise SystemExit(2)
pr=json.loads(prec.read_text())
if pr.get("classification") not in ("MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_READY","MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE"):
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"feature_authority","feature_classification":pr.get("classification")},indent=2)+"\n")
    raise SystemExit(2)
fw=pr.get("firewall") or {}
if fw.get("ohlc_read") is not False or fw.get("returns_read") is not False or fw.get("pnl_read") is not False:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"feature_firewall","feature_firewall":fw},indent=2)+"\n")
    raise SystemExit(2)

features=[json.loads(x) for x in prows.read_text().splitlines() if x.strip()]
if len(features)!=192:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"feature_population","expected":192,"observed":len(features)},indent=2)+"\n")
    raise SystemExit(2)

required_dates=set()
for r in features:
    A=parse_iso(r["decision_time"]);B=A+dt.timedelta(minutes=1)
    required_dates.add(A.date());required_dates.add(B.date())

bars={};manifest=[];hard=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in sorted(required_dates)}
    for fut in as_completed(futs):
        rec,b=fut.result();manifest.append(rec)
        if rec["status"]!="PASS":hard.append(rec)
        else:bars.update(b)
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
if hard:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"market_data","hard_error_count":len(hard),"hard_errors":hard},indent=2)+"\n")
    raise SystemExit(2)

rows=[];missing=0;funding=0
for r in features:
    A=parse_iso(r["decision_time"]);B=A+dt.timedelta(minutes=1)
    if not(START<=A<END) or B>END:continue
    if crosses_funding(A,B):
        funding+=1;continue
    oa=bars.get(ms(A));ob=bars.get(ms(B))
    if oa is None or ob is None:
        missing+=1;continue
    x=float(r["flow_turnover_intensity"])
    if not math.isfinite(x) or x<=0:
        RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"feature_value","bad_cascade_id":r.get("cascade_id")},indent=2)+"\n")
        raise SystemExit(2)
    y=ob/oa-1.0
    rows.append({
      "cascade_id":r["cascade_id"],"decision_time":A.isoformat(),"day":A.date().isoformat(),
      "fold":"F1" if A<FOLD_CUT else "F2","x":x,"y":y,
      "source_event_count":r.get("source_event_count"),"cascade_sold_sol":r.get("cascade_sold_sol"),
      "pre5m_base_volume_sol":r.get("pre5m_base_volume_sol"),"quartile_group":"MIDDLE"
    })
if missing:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_ORCA_FLOW_RESPONSE_SOURCE_BLOCKED","stage":"market_data","missing_entry_exit_count":missing},indent=2)+"\n")
    raise SystemExit(2)

N=len(rows);q=N//4
order=sorted(range(N),key=lambda i:(rows[i]["x"],rows[i]["cascade_id"]))
for i in order[:q]:rows[i]["quartile_group"]="BOTTOM"
for i in order[-q:]:rows[i]["quartile_group"]="TOP"

rho=spearman(rows)
f1rows=[r for r in rows if r["fold"]=="F1"];f2rows=[r for r in rows if r["fold"]=="F2"]
rho1=spearman(f1rows);rho2=spearman(f2rows)
top=[r["y"] for r in rows if r["quartile_group"]=="TOP"]
bot=[r["y"] for r in rows if r["quartile_group"]=="BOTTOM"]
delta=(sum(top)/len(top)-sum(bot)/len(bot)) if top and bot else None
bootrho=block_boot_rho(rows);bootdelta=block_boot_delta(rows)
days=len({r["day"] for r in rows})
s=sign(rho)
gate={
 "n_ge_150":N>=150,
 "days_ge_30":days>=30,
 "f1_n_ge_120":len(f1rows)>=120,
 "f2_n_ge_30":len(f2rows)>=30,
 "abs_rho_ge_0_15":rho is not None and abs(rho)>=0.15,
 "rho_bootstrap_excludes_zero":bootrho["lower"] is not None and (bootrho["lower"]>0 or bootrho["upper"]<0),
 "f1_same_sign":s!=0 and sign(rho1)==s,
 "f2_same_sign":s!=0 and sign(rho2)==s,
 "abs_f1_rho_ge_0_05":rho1 is not None and abs(rho1)>=0.05,
 "abs_f2_rho_ge_0_05":rho2 is not None and abs(rho2)>=0.05,
 "delta_same_sign":s!=0 and sign(delta)==s,
 "delta_bootstrap_excludes_zero":bootdelta["lower"] is not None and (bootdelta["lower"]>0 or bootdelta["upper"]<0)
}
classification="MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS" if all(gate.values()) else "MARGINFI_ORCA_FLOW_RESPONSE_NO_RELATIONSHIP"

with LEDGER.open("w") as fh:
    for r in sorted(rows,key=lambda x:x["decision_time"]):fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

receipt={
 "schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-FLOW-RESPONSE-001",
 "classification":classification,
 "authority":"MARGINFI_ORCA_FLOW_RESPONSE_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "feature_artifact":{"run_id":36781289721,"artifact_id":11127324942,
                     "digest":"sha256:8dfa5ef296ea65b4e51b46136cd6387b5d0586748ee081737d1ded101c182c87"},
 "analyzable_n":N,"distinct_utc_days":days,"funding_excluded":funding,
 "F1":{"n":len(f1rows),"spearman_rho":rho1},
 "F2":{"n":len(f2rows),"spearman_rho":rho2},
 "overall_spearman_rho":rho,
 "discovered_sign":"POSITIVE_REBOUND" if s>0 else ("NEGATIVE_CONTINUATION" if s<0 else "ZERO"),
 "quartile_size":q,
 "bottom_quartile_mean_response":sum(bot)/len(bot) if bot else None,
 "top_quartile_mean_response":sum(top)/len(top) if top else None,
 "top_minus_bottom_mean_response":delta,
 "rho_day_block_bootstrap_95ci":bootrho,
 "delta_day_block_bootstrap_95ci":bootdelta,
 "market_data":{"required_day_count":len(required_dates),"pass_count":sum(1 for r in manifest if r["status"]=="PASS"),
                "missing_minutes_total":sum(int(r.get("missing_minutes") or 0) for r in manifest),"hard_error_count":0},
 "gate":gate,
 "firewall":{"jul_sep_discovery_only":True,"jul_sep_trading_validation":False,
             "oct_dec_2024_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False,
             "post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

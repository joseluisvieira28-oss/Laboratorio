#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,re,time,urllib.error,urllib.request,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2024,7,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2024,10,1,tzinfo=dt.timezone.utc)
FOLD_CUT=dt.datetime(2024,9,1,tzinfo=dt.timezone.utc)
LINK_MIN=5
Q90=1.0307255992127644e-05

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--workers",type=int,default=12)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_EXTREME_REBOUND_V01_PREOUTCOME_SELECTION_RECEIPT.json"
ROWS=OUT/"MARGINFI_SOL_EXTREME_REBOUND_V01_PREOUTCOME_SELECTION_ROWS.ndjson"
MANIFEST=OUT/"MARGINFI_SOL_EXTREME_REBOUND_V01_PREOUTCOME_VOLUME_MANIFEST.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])
def entry_minute(t):return t.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)
def ms(t):return int(t.timestamp()*1000)

def http_bytes(url,retries=8):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-extreme-rebound-preoutcome-v01/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            last={"http":int(e.code)}
            if e.code in (429,500,502,503,504):
                time.sleep(min(30,2**i));continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(30,2**i))
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
                vol=float(row[5])
                if vol<0:
                    rec["status"]="NEGATIVE_BASE_VOLUME";return rec,{}
                # PRE-OUTCOME: intentionally store ONLY base volume, not OHLC.
                bars[t]=vol
        if dup or nonmono:
            rec.update({"status":"ARCHIVE_STRUCTURE_CONFLICT","duplicate_count":dup,"non_monotonic_count":nonmono});return rec,{}
        rec.update({"status":"PASS","bars":len(bars),"missing_minutes":1440-len(bars),
                    "duplicate_count":0,"non_monotonic_count":0})
        return rec,bars
    except Exception as e:
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:240]})
        return rec,{}

def blocked(stage,detail,**extra):
    rec={"schema_version":"0.1","classification":"MARGINFI_SOL_EXTREME_REBOUND_PREOUTCOME_BLOCKED",
         "stage":stage,"detail":str(detail)[:1600],
         "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
                     "jul_sep_market_outcomes_opened":False,"oct_dec_2024_opened":False,
                     "market_2025_opened":False,"market_2026_opened":False,
                     "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False},
         **extra}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

srec=find_one(args.source_root,"MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_RECEIPT_V0.1.json")
srows=find_one(args.source_root,"MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_ROWS_V0.1.ndjson")
crec=find_one(args.calibration_root,"MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_RECEIPT_V0.1.json")
if srec is None or srows is None or crec is None:
    blocked("authority","source_or_calibration_artifact_missing_or_duplicate")
sr=json.loads(srec.read_text());cr=json.loads(crec.read_text())
if sr.get("classification")!="MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS":
    blocked("source_authority",sr.get("classification"))
if cr.get("classification")!="MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS":
    blocked("calibration_authority",cr.get("classification"))
if abs(float(cr.get("q90_flow_turnover_intensity",-1))-Q90)>1e-18:
    blocked("q90_mismatch",cr.get("q90_flow_turnover_intensity"))

src=[json.loads(x) for x in srows.read_text().splitlines() if x.strip()]
events=[];bad=[]
for r in src:
    if r.get("classification")!="DIRECTION_PROVEN":continue
    if r.get("route_semantic")!="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN":continue
    if r.get("asset_label")!="SIGNED_SELL_PRESSURE_PROVEN":continue
    if r.get("asset_mint")!=SOL:continue
    evs=r.get("decoded_swap_events") or []
    if not evs or evs[0].get("inputMint")!=SOL:
        bad.append({"identity":ident(r),"reason":"first_swap_not_sol"});continue
    amt=evs[0].get("inputAmount")
    if not isinstance(amt,int) or amt<=0:
        bad.append({"identity":ident(r),"reason":"bad_input_amount"});continue
    t=parse_iso(r["timestamp"])
    if START<=t<END:events.append({**r,"t":t,"sold_sol":amt/1_000_000_000.0})
if bad:blocked("source_amount",f"{len(bad)} invalid source amounts",errors=bad[:100])

events.sort(key=lambda r:(r["t"],r["signature"],addrkey(r["instructionAddress"])))
cascades=[]
for e in events:
    if not cascades or e["t"]>cascades[-1]["last"]+dt.timedelta(minutes=LINK_MIN):
        cascades.append({"first":e["t"],"last":e["t"],"events":[e]})
    else:
        cascades[-1]["events"].append(e);cascades[-1]["last"]=e["t"]

required_dates=set()
for c in cascades:
    A=entry_minute(c["last"])
    for k in range(1,6):required_dates.add((A-dt.timedelta(minutes=k)).date())

volume={};manifest=[];hard=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in sorted(required_dates)}
    for fut in as_completed(futs):
        rec,b=fut.result();manifest.append(rec)
        if rec["status"]!="PASS":hard.append(rec)
        else:volume.update(b)
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
if hard:blocked("market_volume",f"{len(hard)} hard archive errors",hard_errors=hard)

rows=[];missing=[]
for i,c in enumerate(cascades,1):
    A=entry_minute(c["last"])
    mins=[A-dt.timedelta(minutes=k) for k in range(5,0,-1)]
    vals=[]
    for t in mins:
        v=volume.get(ms(t))
        if v is None:missing.append({"cascade_id":i,"minute":t.isoformat()})
        else:vals.append(v)
    if len(vals)!=5:continue
    pre=sum(vals)
    if pre<=0:missing.append({"cascade_id":i,"reason":"pre5m_volume_nonpositive"});continue
    sold=sum(e["sold_sol"] for e in c["events"])
    intensity=sold/pre
    fold="F1" if A<FOLD_CUT else "F2"
    rows.append({
      "cascade_id":f"pre-{i:05d}","first_event_time":c["first"].isoformat(),
      "last_event_time":c["last"].isoformat(),"decision_time":A.isoformat(),"fold":fold,
      "source_event_count":len(c["events"]),"cascade_sold_sol":sold,
      "pre5m_base_volume_sol":pre,"flow_turnover_intensity":intensity,
      "threshold_q90":Q90,"selected":intensity>=Q90,
      "member_identities":[ident(e) for e in c["events"]]
    })
if missing:blocked("feature_integrity",f"{len(missing)} required feature minutes missing",missing=missing[:200])

selected=[r for r in rows if r["selected"]]
n=len(selected);f1=sum(1 for r in selected if r["fold"]=="F1");f2=n-f1
days=len({r["decision_time"][:10] for r in selected})
ready=(n>=25 and days>=8 and f1>=15 and f2>=8)
classification="MARGINFI_SOL_EXTREME_REBOUND_PREOUTCOME_READY" if ready else "MARGINFI_SOL_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE"

with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
receipt={
 "schema_version":"0.1","lab_id":"DLS-MARGINFI-SOL-EXTREME-FLOW-REBOUND-001",
 "classification":classification,
 "authority":"MARGINFI_SOL_EXTREME_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "q90":Q90,"eligible_source_events":len(events),"source_cascade_count":len(cascades),
 "selected_count":n,"selected_distinct_utc_days":days,"F1_selected_count":f1,"F2_selected_count":f2,
 "sample_gate":{"n_ge_25":n>=25,"days_ge_8":days>=8,"f1_n_ge_15":f1>=15,"f2_n_ge_8":f2>=8},
 "market_volume_day_count":len(required_dates),"market_volume_pass_count":sum(1 for r in manifest if r["status"]=="PASS"),
 "hard_error_count":0,"missing_feature_minute_count":0,
 "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
             "jul_sep_market_outcomes_opened":False,"oct_dec_2024_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

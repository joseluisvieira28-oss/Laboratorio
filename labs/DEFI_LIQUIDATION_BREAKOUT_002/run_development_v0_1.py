#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,shutil,tempfile,time,urllib.error,urllib.request,zipfile
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone,timedelta
from pathlib import Path

LAB="DEFI-LIQUIDATION-BREAKOUT-002"
TARGET="mint:So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=datetime(2021,1,1,tzinfo=timezone.utc)
END=datetime(2026,1,1,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000); END_MS=int(END.timestamp()*1000)
PRIMARY_COST=0.0026
STRESS_COST=0.0040
BOOT_N=5000
SEED_TEXT=LAB+"development-2021-2025"+"1m-confirm-4m-hold"+"V0.1"
BASE="https://data.binance.vision/data/spot/daily/klines/SOLUSDT/1m"
OUT=Path("labs/DEFI_LIQUIDATION_BREAKOUT_002/run_output")
PARENT_CENSUS_SHA="0a10bf5ff4d7ad41f4764c4c1eb592c28f25b01b0a854b144944adf46363d46b"
Y2025_CENSUS_SHA="f89889c2b2f184e54ddd8b0ba83cfce47d75b0e5ba59c8fd863cbe8e0051717c"

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()

def parse_iso(s:str)->datetime:
    return datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(timezone.utc)

def strict_next_minute_ms(x:datetime)->int:
    return (int(x.timestamp()//60)+1)*60000

def norm_ts(v)->int:
    x=int(float(v));a=abs(x)
    if a<10**11:return x*1000
    if a<10**14:return x
    if a<10**17:return x//1000
    return x//1_000_000

def qtype7(vals,p):
    a=sorted(vals);n=len(a)
    if not n:return None
    if n==1:return a[0]
    h=(n-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
    if lo==hi:return a[lo]
    return a[lo]+(a[hi]-a[lo])*(h-lo)

def mean(vals):
    return sum(vals)/len(vals) if vals else None

def profit_factor(vals):
    pos=sum(x for x in vals if x>0)
    neg=-sum(x for x in vals if x<0)
    if neg==0:return math.inf if pos>0 else 0.0
    return pos/neg

def fetch(url,path,retries=6):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-DLB002/0.1"})
            with urllib.request.urlopen(req,timeout=60) as r,path.open("wb") as w:
                if int(r.status)!=200:raise RuntimeError(f"http_{r.status}")
                shutil.copyfileobj(r,w,1024*1024)
            return
        except urllib.error.HTTPError as e:
            if e.code==404:raise FileNotFoundError(url)
            last=e
        except Exception as e:last=e
        time.sleep(min(2**i,12))
    raise RuntimeError(f"download_failed:{url}:{type(last).__name__}:{last}")

def load_source(path:Path, expected_sha:str, label:str):
    actual=sha256_file(path)
    if actual!=expected_sha:raise RuntimeError(f"{label}_census_sha_mismatch:{actual}")
    out=[]
    ids=set()
    with path.open("r",encoding="utf-8") as f:
        for lineno,line in enumerate(f,1):
            if not line.strip():continue
            r=json.loads(line)
            if r.get("primary_market_identity")!=TARGET:continue
            t0=parse_iso(r["t0"])
            if not (START<=t0<END):continue
            cid=r["cluster_id"]
            if cid in ids:raise RuntimeError(f"{label}_duplicate_cluster_id:{cid}")
            ids.add(cid)
            out.append({
              "cluster_id":cid,"protocol":r["protocol"],"instruction_class":r["instruction_class"],
              "t0":r["t0"],"split":r.get("split"),"source_label":label
            })
    return out

def boundaries(row):
    t0=parse_iso(row["t0"])
    e0=strict_next_minute_ms(t0)
    e1=e0+60000
    x=e0+5*60000
    return e0,e1,x

def day_str(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).date().isoformat()

def acquire_day(day,tmp:Path,needed:set[int]):
    name=f"{SYMBOL}-1m-{day}.zip";url=f"{BASE}/{name}"
    z=tmp/name;c=tmp/(name+".CHECKSUM")
    rec={"date":day,"url":url,"needed_timestamp_count":len(needed),"status":"PENDING"}
    try:
        fetch(url,z);fetch(url+".CHECKSUM",c)
        expected=c.read_text(encoding="utf-8").strip().split()[0].lower()
        actual=sha256_file(z)
        rec["zip_sha256"]=actual;rec["checksum_expected"]=expected
        if actual!=expected:
            rec["status"]="CHECKSUM_MISMATCH";return day,rec,{}
        opens={};all_ts=[];members=[]
        with zipfile.ZipFile(z) as zz:
            members=zz.namelist()
            if len(members)!=1:
                rec["status"]="ZIP_MEMBER_COUNT_INVALID";rec["members"]=members;return day,rec,{}
            with zz.open(members[0],"r") as raw:
                rd=csv.reader((line.decode("utf-8") for line in raw))
                prev=None;seen=set()
                for row in rd:
                    if not row or not str(row[0]).strip().lstrip("-").isdigit():continue
                    ts=norm_ts(row[0])
                    if ts%60000:raise RuntimeError(f"unaligned_minute:{day}:{ts}")
                    if prev is not None and ts<=prev:raise RuntimeError(f"nonmonotonic:{day}:{ts}")
                    if ts in seen:raise RuntimeError(f"duplicate_ts:{day}:{ts}")
                    seen.add(ts);prev=ts
                    if day_str(ts)!=day:raise RuntimeError(f"out_of_day:{day}:{ts}")
                    if ts in needed:opens[ts]=float(row[1])
                all_ts=list(seen)
        rec["archive_minute_count"]=len(all_ts)
        rec["found_needed_count"]=len(opens)
        rec["missing_needed_count"]=len(needed-set(opens))
        rec["member"]=members[0]
        rec["status"]="PASS" if len(opens)==len(needed) else "MISSING_REQUIRED_BAR"
        return day,rec,opens
    except FileNotFoundError:
        rec["status"]="ARCHIVE_NOT_FOUND";return day,rec,{}
    except Exception as e:
        rec["status"]="SOURCE_ERROR";rec["error"]=type(e).__name__+":"+str(e);return day,rec,{}
    finally:
        z.unlink(missing_ok=True);c.unlink(missing_ok=True)

def bootstrap_days(trades):
    byday=defaultdict(list)
    for t in trades:byday[t["t0"][:10]].append(t["net_primary_26bps"])
    days=sorted(byday)
    seed=int(hashlib.sha256(SEED_TEXT.encode()).hexdigest(),16)
    rng=random.Random(seed);boots=[]
    for _ in range(BOOT_N):
        vals=[]
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))]
            vals.extend(byday[d])
        boots.append(sum(vals)/len(vals))
    return {
      "block_day_count":len(days),"repetitions":BOOT_N,
      "seed_sha256":hashlib.sha256(SEED_TEXT.encode()).hexdigest(),
      "ci95_primary_net":[qtype7(boots,.025),qtype7(boots,.975)],
      "one_sided_p":(1+sum(1 for x in boots if x<=0))/(BOOT_N+1)
    }

def concentration(trades,key):
    total=sum(max(0,t["net_primary_26bps"]) for t in trades)
    if total<=0:return 1.0,{}
    groups=defaultdict(float)
    for t in trades:
        if t["net_primary_26bps"]>0:groups[t[key]]+=t["net_primary_26bps"]
    shares={k:v/total for k,v in sorted(groups.items())}
    return max(shares.values(),default=0.0),shares

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent-census",required=True)
    ap.add_argument("--y2025-census",required=True)
    ap.add_argument("--workers",type=int,default=12)
    a=ap.parse_args()

    parent=load_source(Path(a.parent_census),PARENT_CENSUS_SHA,"parent_2021_2024")
    y25=load_source(Path(a.y2025_census),Y2025_CENSUS_SHA,"protected_2025")
    # enforce source-year ownership and no hidden 2026
    if any(parse_iso(x["t0"]).year==2025 for x in parent):raise RuntimeError("parent_contains_2025")
    if any(parse_iso(x["t0"]).year!=2025 for x in y25):raise RuntimeError("protected_source_non_2025")
    rows=parent+y25
    ids=[x["cluster_id"] for x in rows]
    if len(ids)!=len(set(ids)):raise RuntimeError("cross_source_duplicate_cluster_id")
    rows.sort(key=lambda r:(r["t0"],r["protocol"],r["cluster_id"]))

    eligible=[];boundary_excluded=[]
    needed_by_day=defaultdict(set)
    for r in rows:
        e0,e1,x=boundaries(r)
        if e0<START_MS or x>=END_MS:
            boundary_excluded.append({"cluster_id":r["cluster_id"],"t0":r["t0"],"reason":"DEVELOPMENT_BOUNDARY"})
            continue
        z={**r,"_e0":e0,"_e1":e1,"_x":x}
        eligible.append(z)
        for ts in (e0,e1,x):needed_by_day[day_str(ts)].add(ts)

    if any(d>="2026-01-01" for d in needed_by_day):raise RuntimeError("2026_market_date_requested")

    manifest=[];opens={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        with ThreadPoolExecutor(max_workers=max(1,min(a.workers,16))) as ex:
            futs=[ex.submit(acquire_day,d,tmp,set(ts)) for d,ts in sorted(needed_by_day.items())]
            for fut in as_completed(futs):
                d,rec,vals=fut.result();manifest.append(rec);opens.update(vals)
                print(json.dumps({"date":d,"status":rec["status"],"needed":rec["needed_timestamp_count"],"found":rec.get("found_needed_count",0)}),flush=True)

    manifest.sort(key=lambda x:x["date"])
    hard=[x for x in manifest if x["status"] in ("CHECKSUM_MISMATCH","ZIP_MEMBER_COUNT_INVALID","SOURCE_ERROR")]
    complete=[];missing=Counter()
    for r in eligible:
        miss=[name for name,ts in (("E0",r["_e0"]),("E1",r["_e1"]),("X",r["_x"])) if ts not in opens]
        if miss:
            missing["+".join(miss)]+=1
        else:complete.append(r)
    coverage=len(complete)/len(eligible) if eligible else 0.0

    OUT.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/"DEVELOPMENT_MARKET_ARCHIVE_MANIFEST_V0.1.json"
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    acq={
      "schema_version":"0.1","lab_id":LAB,"classification":"DEVELOPMENT_MARKET_SOURCE_PASS" if not hard and coverage>=.95 else "SOURCE_BLOCKED_DEVELOPMENT_BREAKOUT",
      "parent_source_cluster_count":len(parent),"protected_2025_source_cluster_count":len(y25),
      "development_source_cluster_count":len(rows),"boundary_excluded_count":len(boundary_excluded),
      "market_denominator":len(eligible),"market_complete_count":len(complete),"source_market_coverage":coverage,
      "required_archive_day_count":len(needed_by_day),"hard_source_error_count":len(hard),
      "missing_reasons":dict(missing),"archive_manifest_sha256":sha256_file(manifest_path),
      "parent_census_sha256":PARENT_CENSUS_SHA,"protected_2025_census_sha256":Y2025_CENSUS_SHA,
      "max_market_timestamp_requested_utc":datetime.fromtimestamp(max((x for s in needed_by_day.values() for x in s),default=0)/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "protected_2026_market_opened":False,"trading_authority":"NONE"
    }
    (OUT/"DEVELOPMENT_ACQUISITION_RECEIPT_V0.1.json").write_text(json.dumps(acq,indent=2,sort_keys=True)+"\n")
    if hard or coverage<.95:
        res={**acq,"classification":"SOURCE_BLOCKED_DEVELOPMENT_BREAKOUT","economic_inference_computed":False}
        (OUT/"DEVELOPMENT_RECEIPT_V0.1.json").write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
        print(json.dumps(res,indent=2,sort_keys=True));return

    candidates=[]
    zero_confirm=0
    for r in complete:
        p0=opens[r["_e0"]];p1=opens[r["_e1"]];px=opens[r["_x"]]
        if min(p0,p1,px)<=0:raise RuntimeError("nonpositive_market_price")
        c1=p1/p0-1.0
        if c1==0:
            zero_confirm+=1;continue
        direction=1 if c1>0 else -1
        gross=direction*(px/p1-1.0)
        dt0=parse_iso(r["t0"])
        candidates.append({
          "cluster_id":r["cluster_id"],"protocol":r["protocol"],"instruction_class":r["instruction_class"],
          "t0":r["t0"],"utc_day":dt0.date().isoformat(),"calendar_year":dt0.year,
          "e0":datetime.fromtimestamp(r["_e0"]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
          "e1":datetime.fromtimestamp(r["_e1"]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
          "x":datetime.fromtimestamp(r["_x"]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
          "p0":p0,"p1":p1,"px":px,"confirmation_return_1m":c1,
          "direction":"LONG" if direction>0 else "SHORT",
          "gross_return":gross,"net_primary_26bps":gross-PRIMARY_COST,"net_stress_40bps":gross-STRESS_COST,
          "_e1_ms":r["_e1"],"_x_ms":r["_x"]
        })

    candidates.sort(key=lambda x:(x["_e1_ms"],x["cluster_id"]))
    trades=[];suppressed=0;open_until=-1
    for r in candidates:
        if r["_e1_ms"]<open_until:
            suppressed+=1;continue
        trades.append(r);open_until=r["_x_ms"]

    vals=[x["net_primary_26bps"] for x in trades]
    stress=[x["net_stress_40bps"] for x in trades]
    boot=bootstrap_days(trades) if trades else {"block_day_count":0,"ci95_primary_net":[None,None],"repetitions":BOOT_N,"seed_sha256":hashlib.sha256(SEED_TEXT.encode()).hexdigest(),"one_sided_p":None}
    byyear=[];year_map=defaultdict(list)
    for t in trades:year_map[t["calendar_year"]].append(t["net_primary_26bps"])
    for y in range(2021,2026):
        xs=year_map.get(y,[])
        byyear.append({"year":y,"n":len(xs),"mean_net_primary":mean(xs),"positive":bool(xs and mean(xs)>0)})
    byproto=[];proto_map=defaultdict(list)
    for t in trades:proto_map[t["protocol"]].append(t["net_primary_26bps"])
    for p in sorted(proto_map):
        xs=proto_map[p]
        byproto.append({"protocol":p,"n":len(xs),"mean_net_primary":mean(xs),"positive":bool(len(xs)>=100 and mean(xs)>0)})
    dayconc,_=concentration(trades,"utc_day")
    yearconc,_=concentration(trades,"calendar_year")
    years_present=sorted({t["calendar_year"] for t in trades})
    valid_proto=[x for x in byproto if x["n"]>=100]
    positive_proto=[x for x in valid_proto if x["mean_net_primary"]>0]
    positive_years=sum(1 for x in byyear if x["positive"])
    pf=profit_factor(vals)
    gates={
      "source_market_coverage_ge_95pct":coverage>=.95,
      "serialized_n_ge_3000":len(trades)>=3000,
      "utc_trade_days_ge_250":boot["block_day_count"]>=250,
      "all_five_years_represented":years_present==[2021,2022,2023,2024,2025],
      "three_protocol_families_ge_100":len(valid_proto)>=3,
      "mean_primary_positive":bool(vals and mean(vals)>0),
      "bootstrap_ci95_lower_positive":bool(boot["ci95_primary_net"][0] is not None and boot["ci95_primary_net"][0]>0),
      "mean_stress_positive":bool(stress and mean(stress)>0),
      "primary_profit_factor_ge_1_10":pf>=1.10,
      "four_of_five_years_positive":positive_years>=4,
      "three_protocol_families_positive":len(positive_proto)>=3,
      "day_positive_pnl_concentration_le_25pct":dayconc<=.25,
      "year_positive_pnl_concentration_le_40pct":yearconc<=.40
    }
    classification="DEVELOPMENT_BREAKOUT_SURVIVES" if all(gates.values()) else "NO_EDGE_DEVELOPMENT_BREAKOUT"
    report={
      "schema_version":"0.1","lab_id":LAB,"classification":classification,
      "source_cluster_count":len(rows),"market_denominator":len(eligible),"source_market_complete_count":len(complete),
      "source_market_coverage":coverage,"zero_confirmation_no_trade_count":zero_confirm,
      "candidate_trade_count":len(candidates),"overlap_suppressed_count":suppressed,"serialized_trade_count":len(trades),
      "direction_counts":dict(Counter(x["direction"] for x in trades)),
      "mean_gross_return":mean([x["gross_return"] for x in trades]),
      "mean_net_primary_26bps":mean(vals),"mean_net_stress_40bps":mean(stress),
      "primary_profit_factor":pf,"bootstrap":boot,
      "year_results":byyear,"protocol_results":byproto,
      "positive_year_count":positive_years,"positive_protocol_family_count_ge100":len(positive_proto),
      "max_positive_pnl_day_concentration":dayconc,"max_positive_pnl_year_concentration":yearconc,
      "gates":gates,"all_gates_pass":all(gates.values()),
      "parent_census_sha256":PARENT_CENSUS_SHA,"protected_2025_census_sha256":Y2025_CENSUS_SHA,
      "protected_2026_source_opened":False,"protected_2026_market_opened":False,
      "post_outcome_tuning":False,"trading_authority":"NONE"
    }
    cleanfields=["cluster_id","protocol","instruction_class","t0","utc_day","calendar_year","e0","e1","x","p0","p1","px","confirmation_return_1m","direction","gross_return","net_primary_26bps","net_stress_40bps"]
    with (OUT/"DEVELOPMENT_TRADES_V0.1.ndjson").open("w",encoding="utf-8") as f:
        for t in trades:f.write(json.dumps({k:t[k] for k in cleanfields},sort_keys=True,separators=(",",":"))+"\n")
    (OUT/"DEVELOPMENT_RECEIPT_V0.1.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False),flush=True)

if __name__=="__main__":main()

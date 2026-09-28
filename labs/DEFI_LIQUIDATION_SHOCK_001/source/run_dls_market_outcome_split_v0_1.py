#!/usr/bin/env python3
import argparse,bisect,csv,datetime as dt,hashlib,io,json,math,random,time,urllib.error,urllib.parse,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal,InvalidOperation
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
HORIZONS=(1,5,30,240)
SECONDARY=(1,30,240)
BOOTSTRAPS=5000
UTC=dt.timezone.utc

ap=argparse.ArgumentParser()
ap.add_argument("--split",choices=["discovery","oos"],required=True)
ap.add_argument("--sample-root",required=True)
ap.add_argument("--market-root",required=True)
ap.add_argument("--authority-root",required=True)
ap.add_argument("--registry",required=True)
ap.add_argument("--discovery-receipt")
args=ap.parse_args()

ROOT=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
PREFIX="DISCOVERY" if args.split=="discovery" else "OOS"
RECEIPT=ROOT/f"DLS_{PREFIX}_RECEIPT_V0.1.json"
QA_OUT=ROOT/f"DLS_{PREFIX}_MARKET_DATA_QA_V0.1.json"
PAIR_OUT=ROOT/f"DLS_{PREFIX}_MATCHED_PAIR_OUTCOMES_V0.1.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    if len(hits)!=1:
        raise RuntimeError(f"expected_one:{name}:found={len(hits)}")
    return json.loads(hits[0].read_text()),hits[0]

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def parse_ts(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(UTC)

def canon_minute(m):
    return dt.datetime.fromtimestamp(m*60,tz=UTC).strftime("%Y-%m-%dT%H:%M:00Z")

def ceil_minute(t):
    sec=int(t.timestamp())
    return (sec+59)//60

def month_key(t):
    return f"{t.year:04d}-{t.month:02d}"

def month_bounds(y,m):
    a=dt.datetime(y,m,1,tzinfo=UTC)
    b=dt.datetime(y+1,1,1,tzinfo=UTC) if m==12 else dt.datetime(y,m+1,1,tzinfo=UTC)
    return a,b

def daterange(a,b):
    d=a.date()
    while d < b.date():
        yield d
        d += dt.timedelta(days=1)

def get_bytes(url,retries=5):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-outcome-v0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:
                return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404,403): return int(e.code),None
            last=f"http_{e.code}"
            if e.code in (429,500,502,503,504):
                time.sleep(min(12,2**i)); continue
            return int(e.code),None
        except Exception as e:
            last=f"{type(e).__name__}:{str(e)[:120]}"
            time.sleep(min(12,2**i))
    return None,None

def get_json(url,retries=5):
    st,b=get_bytes(url,retries)
    if st!=200 or b is None: return st,None
    try:return st,json.loads(b)
    except Exception:return st,None

authority,authority_path=find_one(args.authority_root,"FINAL_PRE_DISCOVERY_AUTHORITY_RECEIPT_V0.1.json")
if authority.get("classification")!="FINAL_PRE_DISCOVERY_AUTHORITY_PASS":
    raise SystemExit("FINAL_PRE_DISCOVERY_AUTHORITY_NOT_PASS")
market,market_path=find_one(args.market_root,"MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")
if market.get("classification")!="MARKET_DATA_SOURCE_PASS":
    raise SystemExit("MARKET_DATA_SOURCE_NOT_PASS")
sample,sample_receipt_path=find_one(args.sample_root,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
if sample.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
    raise SystemExit("SOURCE_SAMPLE_GATE_NOT_PASS")
census_hits=sorted(Path(args.sample_root).rglob("SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"))
if len(census_hits)!=1: raise SystemExit("SOURCE_CLUSTER_CENSUS_NOT_UNIQUE")
census_path=census_hits[0]

registry_path=Path(args.registry)
registry=json.loads(registry_path.read_text())
registry_hash=sha256_file(registry_path)
if registry_hash!=market.get("mapping_registry_sha256"):
    raise SystemExit(f"MAPPING_REGISTRY_HASH_MISMATCH:{registry_hash}:{market.get('mapping_registry_sha256')}")

if args.split=="oos":
    if not args.discovery_receipt: raise SystemExit("OOS_REQUIRES_DISCOVERY_RECEIPT")
    dr=json.loads(Path(args.discovery_receipt).read_text())
    if dr.get("classification")!="SURVIVES_DISCOVERY":
        raise SystemExit(f"OOS_NOT_AUTHORIZED:{dr.get('classification')}")

direct=[x for x in registry.get("mappings",[]) if x.get("status") in ("BINANCE_DIRECT","OKX_DIRECT")]
if len(direct)!=1: raise SystemExit(f"V01_EXPECTS_ONE_DIRECT_MAPPING:{len(direct)}")
mapping=direct[0]
if mapping.get("status")!="BINANCE_DIRECT": raise SystemExit("V01_IMPLEMENTATION_REQUIRES_BINANCE_DIRECT")
target=mapping["target_identity"]
symbol=mapping["symbol"]
listing=parse_ts(mapping["listing_start_utc"])
if args.split=="discovery":
    split_start=dt.datetime(2021,1,1,tzinfo=UTC); split_end=dt.datetime(2024,1,1,tzinfo=UTC)
else:
    split_start=dt.datetime(2024,1,1,tzinfo=UTC); split_end=dt.datetime(2025,1,1,tzinfo=UTC)

clusters=[]
all_market_t0=[]
with open(census_path,"r",encoding="utf-8") as fh:
    for line in fh:
        if not line.strip(): continue
        o=json.loads(line)
        if o.get("primary_market_identity")!=target: continue
        t=parse_ts(o["t0"])
        if dt.datetime(2021,1,1,tzinfo=UTC) <= t < dt.datetime(2025,1,1,tzinfo=UTC):
            all_market_t0.append(t.timestamp())
        if o.get("split")!=args.split: continue
        if not (split_start <= t < split_end): continue
        if t < listing: continue
        o["_t0_dt"]=t
        o["_a_min"]=ceil_minute(t)
        clusters.append(o)

if not clusters: raise SystemExit("NO_ACTIVE_SPLIT_CLUSTERS")
all_market_t0.sort()

months=sorted({month_key(o["_t0_dt"]) for o in clusters})
required_dates=set()
for ym in months:
    y,m=map(int,ym.split("-"))
    a,b=month_bounds(y,m)
    a=max(a,split_start,listing)
    b=min(b,split_end)
    for d in daterange(a,b): required_dates.add(d)
    if b < split_end:
        required_dates.add(b.date())
# Never acquire outside active split.
required_dates={d for d in required_dates if split_start.date() <= d < split_end.date()}

archive_template=mapping["archive_route_template"]
checksum_template=mapping["checksum_route_template"]

def acquire_day(day):
    ds=day.isoformat()
    zu=archive_template.replace("{symbol}",symbol).replace("{date}",ds)
    cu=checksum_template.replace("{symbol}",symbol).replace("{date}",ds)
    cst,cb=get_bytes(cu)
    zst,zb=get_bytes(zu)
    qa={"date":ds,"zip_http_status":zst,"checksum_http_status":cst,"accepted":False,
        "observed_bars":0,"duplicate_count":0,"non_monotonic_count":0,"missing_minute_count":1440}
    if cst!=200 or zst!=200 or cb is None or zb is None:
        qa["reason"]="archive_or_checksum_unavailable"
        return qa,{},[]
    checksum_text=cb.decode("utf-8","replace").strip()
    expected=checksum_text.split()[0].strip().lower() if checksum_text else ""
    actual=hashlib.sha256(zb).hexdigest()
    qa["checksum_expected"]=expected;qa["checksum_actual"]=actual;qa["checksum_pass"]=(expected==actual)
    if expected!=actual:
        qa["reason"]="checksum_mismatch"
        return qa,{},["checksum_mismatch"]
    bars={}
    conflicts=[]
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            names=[n for n in z.namelist() if not n.endswith("/")]
            if len(names)!=1:
                qa["reason"]="archive_member_count"; return qa,{},["archive_member_count"]
            prev=None;dups=0;nonmono=0;outside=0;bad=0
            day0=int(dt.datetime(day.year,day.month,day.day,tzinfo=UTC).timestamp()//60)
            day1=day0+1440
            with z.open(names[0]) as raw:
                reader=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
                for row in reader:
                    if len(row)<2: bad+=1;continue
                    try:
                        ts=int(row[0])
                        if ts>10**15: ts//=1000
                        if ts%60000!=0: bad+=1;continue
                        minute=ts//60000
                        Decimal(row[1])
                    except Exception:
                        bad+=1;continue
                    if not (day0 <= minute < day1): outside+=1;continue
                    if prev is not None and minute<=prev: nonmono+=1
                    prev=minute
                    if minute in bars: dups+=1
                    bars[minute]=row[1]
            qa["observed_bars"]=len(bars);qa["duplicate_count"]=dups;qa["non_monotonic_count"]=nonmono
            qa["out_of_day_count"]=outside;qa["bad_row_count"]=bad
            qa["missing_minute_count"]=1440-len(bars)
            if dups or nonmono or outside or bad:
                qa["reason"]="archive_integrity_conflict"
                conflicts.append("archive_integrity_conflict")
                return qa,{},conflicts
            qa["accepted"]=True;qa["reason"]="accepted"
            return qa,bars,[]
    except Exception as e:
        qa["reason"]="archive_parse_error";qa["detail"]=f"{type(e).__name__}:{str(e)[:160]}"
        return qa,{},["archive_parse_error"]

qas=[];opens={};source_conflicts=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    futs={ex.submit(acquire_day,d):d for d in sorted(required_dates)}
    for fut in as_completed(futs):
        qa,bars,conf=fut.result()
        qas.append(qa)
        if bars: opens.update(bars)
        if conf: source_conflicts.append({"date":qa["date"],"reasons":conf})
qas.sort(key=lambda x:x["date"])

# Mandatory deterministic archive/API reconciliation, timestamp selection independent of price value.
reconciliation=[]
years=sorted({dt.datetime.fromtimestamp(m*60,tz=UTC).year for m in opens})
for year in years:
    mins=[m for m in opens if dt.datetime.fromtimestamp(m*60,tz=UTC).year==year]
    ranked=sorted(mins,key=lambda m:hashlib.sha256(f"{LAB}{symbol}{year}{canon_minute(m)}".encode()).digest())[:16]
    for m in ranked:
        ms=m*60000
        url="https://data-api.binance.vision/api/v3/klines?"+urllib.parse.urlencode(
            {"symbol":symbol,"interval":"1m","startTime":ms,"endTime":ms+59999,"limit":1})
        st,obj=get_json(url)
        ok=False;rest_open=None;rest_ts=None
        if st==200 and isinstance(obj,list) and len(obj)==1 and isinstance(obj[0],list) and len(obj[0])>=2:
            rest_ts=int(obj[0][0]);rest_open=str(obj[0][1])
            try: ok=(rest_ts==ms and Decimal(rest_open)==Decimal(opens[m]))
            except InvalidOperation: ok=False
        reconciliation.append({"year":year,"minute":canon_minute(m),"http_status":st,
                               "archive_open":opens[m],"rest_open":rest_open,"rest_open_time":rest_ts,"pass":ok})
        if not ok: source_conflicts.append({"reason":"archive_rest_reconciliation_failed","minute":canon_minute(m)})

# Candidate controls are source/time/bar-availability only.
def near_any_event(candidate_sec):
    i=bisect.bisect_left(all_market_t0,candidate_sec)
    for j in (i-1,i):
        if 0<=j<len(all_market_t0) and abs(all_market_t0[j]-candidate_sec)<=4*3600: return True
    return False

required_offsets=(0,1,5,30,240)
pool={}
for ym in months:
    y,m=map(int,ym.split("-"));ma,mb=month_bounds(y,m)
    for hour in range(24):
        candidates=[]
        d=max(ma,split_start,listing)
        while d < min(mb,split_end):
            day=d.date()
            for minute_of_hour in range(60):
                c=dt.datetime(day.year,day.month,day.day,hour,minute_of_hour,tzinfo=UTC)
                if c < listing or not (split_start <= c < split_end): continue
                cm=int(c.timestamp()//60)
                if dt.datetime.fromtimestamp((cm+240)*60,tz=UTC) >= split_end: continue
                if near_any_event(cm*60): continue
                if all((cm+off) in opens for off in required_offsets):
                    candidates.append(cm)
            d += dt.timedelta(days=1)
        pool[(ym,hour)]=candidates

pairs=[]
missing_reasons=defaultdict(int)
sub_den=defaultdict(int);sub_pair=defaultdict(int)
for o in clusters:
    sg=(o["protocol"],o["instruction_class"]);sub_den[sg]+=1
    a=o["_a_min"]
    if dt.datetime.fromtimestamp((a+240)*60,tz=UTC) >= split_end:
        missing_reasons["event_horizon_crosses_split"]+=1;continue
    if not all((a+off) in opens for off in required_offsets):
        missing_reasons["event_required_bar_missing"]+=1;continue
    ym=month_key(o["_t0_dt"]);hour=dt.datetime.fromtimestamp(a*60,tz=UTC).hour
    cands=pool.get((ym,hour),[])
    if not cands:
        missing_reasons["no_admissible_control"]+=1;continue
    def rank_key(cm):
        return hashlib.sha256((o["cluster_id"]+canon_minute(cm)).encode("utf-8")).digest()
    control=min(cands,key=rank_key)
    pairs.append({"cluster":o,"event_minute":a,"control_minute":control})
    sub_pair[sg]+=1

inferential_status={}
for sg in market.get("post_mapping_subgroups") or []:
    inferential_status[(sg.get("protocol"),sg.get("class"))]=sg.get("post_mapping_status")

den=len(clusters);paired=len(pairs);coverage=paired/den if den else 0.0
coverage_errors=[]
if coverage < .95:
    coverage_errors.append({"reason":"pooled_pair_coverage_below_95pct","paired":paired,"denominator":den,"coverage":coverage})
for sg,n in sorted(sub_den.items()):
    status=inferential_status.get(sg)
    active=(status=="INFERENTIAL_DISCOVERY_AND_OOS" or (args.split=="oos" and status=="EXTERNAL_CONFIRMATORY_INFERENTIAL"))
    if not active or n==0: continue
    cov=sub_pair[sg]/n
    if cov < .90:
        coverage_errors.append({"reason":"inferential_subgroup_pair_coverage_below_90pct",
                                "protocol":sg[0],"class":sg[1],"paired":sub_pair[sg],"denominator":n,"coverage":cov})
min_n=1000 if args.split=="discovery" else 500
if paired < min_n:
    coverage_errors.append({"reason":"paired_sample_below_frozen_gate","paired":paired,"required":min_n})

qa_receipt={
    "schema_version":"0.1","lab_id":LAB,"split":args.split,"symbol":symbol,"target_identity":target,
    "authority_classification":authority.get("classification"),"market_source_classification":market.get("classification"),
    "sample_gate_classification":sample.get("classification"),"registry_sha256":registry_hash,
    "archive_date_count":len(qas),"accepted_archive_date_count":sum(1 for q in qas if q.get("accepted")),
    "source_conflict_count":len(source_conflicts),"source_conflicts":source_conflicts,
    "archives":qas,"reconciliation_sample_count":len(reconciliation),
    "reconciliation_pass_count":sum(1 for x in reconciliation if x["pass"]),"reconciliation":reconciliation,
    "market_mappable_cluster_count":den,"paired_cluster_count":paired,"pair_coverage":coverage,
    "missing_reasons":dict(sorted(missing_reasons.items())),
    "subgroup_coverage":[{"protocol":k[0],"class":k[1],"status":inferential_status.get(k),
                          "denominator":n,"paired":sub_pair[k],"coverage":(sub_pair[k]/n if n else None)}
                         for k,n in sorted(sub_den.items())],
    "coverage_error_count":len(coverage_errors),"coverage_errors":coverage_errors,
    "protected_2025_2026_opened":False,"live_trading":False,"orders":False,"wallets":False,
    "exchange_mutation":False,"merge_main":False
}
QA_OUT.write_text(json.dumps(qa_receipt,indent=2,sort_keys=True)+"\n")

if source_conflicts or coverage_errors:
    receipt={
      "schema_version":"0.1","lab_id":LAB,"split":args.split,"classification":"SOURCE_BLOCKED",
      "economic_inference_computed":False,"source_conflict_count":len(source_conflicts),
      "coverage_error_count":len(coverage_errors),"market_mappable_cluster_count":den,
      "paired_cluster_count":paired,"pair_coverage":coverage,
      "authority_receipt_sha256":sha256_file(authority_path),"market_source_receipt_sha256":sha256_file(market_path),
      "sample_gate_receipt_sha256":sha256_file(sample_receipt_path),"registry_sha256":registry_hash,
      "implementation_freeze":"DISCOVERY_EXECUTION_IMPLEMENTATION_FREEZE_V0.1.md",
      "protected_2025_2026_opened":False,"post_outcome_tuning":False,
      "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False
    }
    RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(2)

# Economic inference is authorized only after source/coverage gates above pass.
outcomes=[]
for p in pairs:
    o=p["cluster"];a=p["event_minute"];c=p["control_minute"]
    row={"cluster_id":o["cluster_id"],"protocol":o["protocol"],"instruction_class":o["instruction_class"],
         "t0":o["t0"],"event_entry_minute":canon_minute(a),"control_entry_minute":canon_minute(c),"horizons":{}}
    for h in HORIZONS:
        ep0=float(Decimal(opens[a]));eph=float(Decimal(opens[a+h]))
        cp0=float(Decimal(opens[c]));cph=float(Decimal(opens[c+h]))
        er=math.log(eph/ep0);cr=math.log(cph/cp0);d=abs(er)-abs(cr)
        row["horizons"][str(h)]={"event_abs_return":abs(er),"control_abs_return":abs(cr),"paired_difference":d}
    outcomes.append(row)

with open(PAIR_OUT,"w",encoding="utf-8") as fh:
    for row in outcomes: fh.write(json.dumps(row,sort_keys=True)+"\n")

def bootstrap_stats(h):
    vals=[x["horizons"][str(h)]["paired_difference"] for x in outcomes]
    observed=sum(vals)/len(vals)
    by_day=defaultdict(lambda:[0.0,0])
    for x,dv in zip(outcomes,vals):
        day=x["t0"][:10];by_day[day][0]+=dv;by_day[day][1]+=1
    blocks=sorted(by_day.items())
    seed=int(hashlib.sha256(f"{LAB}{args.split}{h}V0.1".encode()).hexdigest(),16)
    rng=random.Random(seed);boots=[]
    n=len(blocks)
    for _ in range(BOOTSTRAPS):
        s=0.0;c=0
        for _j in range(n):
            _day,(bs,bc)=blocks[rng.randrange(n)]
            s+=bs;c+=bc
        boots.append(s/c)
    boots.sort()
    li=math.floor(.025*(BOOTSTRAPS-1));ui=math.ceil(.975*(BOOTSTRAPS-1))
    p=(1+sum(1 for x in boots if x<=0.0))/(BOOTSTRAPS+1)
    return observed,boots[li],boots[ui],p,len(blocks)

stats={}
for h in HORIZONS:
    event_mean=sum(x["horizons"][str(h)]["event_abs_return"] for x in outcomes)/len(outcomes)
    control_mean=sum(x["horizons"][str(h)]["control_abs_return"] for x in outcomes)/len(outcomes)
    mean_d,lo,hi,pval,days=bootstrap_stats(h)
    uplift=(event_mean/control_mean-1.0) if control_mean>0 else None
    stats[str(h)]={"event_abs_mean":event_mean,"control_abs_mean":control_mean,"mean_paired_difference":mean_d,
                   "relative_uplift":uplift,"bootstrap_ci95":[lo,hi],"one_sided_bootstrap_p":pval,
                   "bootstrap_repetitions":BOOTSTRAPS,"day_block_count":days}

# Holm-Bonferroni secondary family.
ordered=sorted(SECONDARY,key=lambda h:(stats[str(h)]["one_sided_bootstrap_p"],h))
holm={};active=True
m=len(SECONDARY)
for i,h in enumerate(ordered):
    threshold=.05/(m-i)
    p=stats[str(h)]["one_sided_bootstrap_p"]
    reject=bool(active and p<=threshold)
    holm[str(h)]={"p":p,"threshold":threshold,"reject_null":reject,"rank":i+1}
    if not reject: active=False

family_vals=defaultdict(list)
for x in outcomes:
    sg=(x["protocol"],x["instruction_class"])
    status=inferential_status.get(sg)
    active_family=(status=="INFERENTIAL_DISCOVERY_AND_OOS" or (args.split=="oos" and status=="EXTERNAL_CONFIRMATORY_INFERENTIAL"))
    if active_family: family_vals[x["protocol"]].append(x["horizons"]["5"]["paired_difference"])
protocol_family_means={p:sum(v)/len(v) for p,v in sorted(family_vals.items()) if v}
positive_families=sum(1 for v in protocol_family_means.values() if v>0)
secondary_positive=sum(1 for h in SECONDARY if stats[str(h)]["mean_paired_difference"]>0)

primary=stats["5"]
gates={
 "paired_n": paired>=min_n,
 "primary_mean_positive": primary["mean_paired_difference"]>0,
 "primary_ci_lower_positive": primary["bootstrap_ci95"][0]>0,
 "primary_relative_uplift_ge_10pct": primary["relative_uplift"] is not None and primary["relative_uplift"]>=.10,
 "at_least_two_inferential_protocol_families_positive": positive_families>=2,
 "at_least_two_secondary_horizons_positive": secondary_positive>=2
}
if args.split=="discovery":
    gates["at_least_one_secondary_holm_survives"]=sum(1 for v in holm.values() if v["reject_null"])>=1
passed=all(gates.values())
classification=("SURVIVES_DISCOVERY" if passed else "NO_EDGE_DISCOVERY") if args.split=="discovery" else ("SURVIVES_OOS" if passed else "NO_EDGE_OOS")

receipt={
 "schema_version":"0.1","lab_id":LAB,"split":args.split,"classification":classification,
 "market_mappable_cluster_count":den,"paired_cluster_count":paired,"pair_coverage":coverage,
 "statistics":stats,"secondary_holm_bonferroni":holm,"protocol_family_5m_mean_paired_difference":protocol_family_means,
 "positive_inferential_protocol_family_count":positive_families,"secondary_positive_horizon_count":secondary_positive,
 "gates":gates,"all_frozen_gates_pass":passed,
 "authority_receipt_sha256":sha256_file(authority_path),"market_source_receipt_sha256":sha256_file(market_path),
 "sample_gate_receipt_sha256":sha256_file(sample_receipt_path),"registry_sha256":registry_hash,
 "implementation_freeze":"DISCOVERY_EXECUTION_IMPLEMENTATION_FREEZE_V0.1.md",
 "prices_opened":True,"returns_computed":True,"pnl_computed":False,"directional_outcome_used":False,
 "protected_2025_2026_opened":False,"post_outcome_tuning":False,
 "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

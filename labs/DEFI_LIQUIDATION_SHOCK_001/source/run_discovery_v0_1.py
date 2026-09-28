#!/usr/bin/env python3
import argparse,bisect,csv,datetime as dt,hashlib,io,json,math,random,re,time,urllib.error,urllib.parse,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
HORIZONS={"1m":1,"5m":5,"30m":30,"240m":240}
DISCOVERY_END=dt.datetime(2024,1,1,tzinfo=dt.timezone.utc)
EXPECTED_REGISTRY_SHA256="97ff771dbeb2ec9c3b0a408edd8733701a973ffc1ae597413fbfed4455482f90"
EXPECTED_REQUIREMENTS_SHA256="b17164cd6735cae47bb3323cb82789ca2fa492f81eb4e70439b281a58a48bbe4"
BOOTSTRAP_N=5000

ap=argparse.ArgumentParser()
ap.add_argument("--authority",required=True)
ap.add_argument("--sample-gate",required=True)
ap.add_argument("--market-source",required=True)
ap.add_argument("--registry",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
ap.add_argument("--workers",type=int,default=12)
args=ap.parse_args()
OUT=Path(args.outdir); OUT.mkdir(parents=True,exist_ok=True)
ACQ=OUT/"DISCOVERY_MARKET_DATA_ACQUISITION_RECEIPT_V0.1.json"
RES=OUT/"DISCOVERY_RESULT_RECEIPT_V0.1.json"
PAIRS=OUT/"DISCOVERY_PAIRED_OUTCOMES_V0.1.ndjson"
MANIFEST=OUT/"DISCOVERY_MARKET_DATA_ARCHIVE_MANIFEST_V0.1.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits: return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def iso_minute(x):
    return x.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")

def ceil_minute(x):
    x=x.astimezone(dt.timezone.utc)
    if x.second==0 and x.microsecond==0: return x.replace(second=0,microsecond=0)
    return (x.replace(second=0,microsecond=0)+dt.timedelta(minutes=1))

def ms(x): return int(x.timestamp()*1000)

def daterange(a,b_inclusive):
    d=a
    while d<=b_inclusive:
        yield d
        d+=dt.timedelta(days=1)

def http_bytes(url,retries=6,allow_404=False):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-discovery/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:
                return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404: return 404,None
            last={"http":e.code}
            if e.code in (429,500,502,503,504):
                time.sleep(min(20,2**i)); continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]}
            time.sleep(min(20,2**i))
    return None,last

def http_json(url,retries=6):
    st,b=http_bytes(url,retries=retries,allow_404=False)
    if st!=200: return st,None
    try:return st,json.loads(b)
    except Exception:return st,None

def qtype7(vals,q):
    s=sorted(vals); n=len(s)
    if not n:return None
    if n==1:return s[0]
    h=(n-1)*q
    lo=int(math.floor(h)); hi=int(math.ceil(h))
    if lo==hi:return s[lo]
    return s[lo]+(s[hi]-s[lo])*(h-lo)

def mean(xs): return sum(xs)/len(xs) if xs else None

def bootstrap_stats(pairs,hlabel):
    by=defaultdict(lambda:[0.0,0])
    key="d_"+hlabel
    for p in pairs:
        day=p["event_t0"][:10]
        by[day][0]+=p[key]; by[day][1]+=1
    days=sorted(by)
    seed=int(hashlib.sha256((LAB+"discovery"+hlabel+"V0.1").encode()).hexdigest(),16)
    rng=random.Random(seed)
    boots=[]
    for _ in range(BOOTSTRAP_N):
        ss=0.0; nn=0
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))]
            ss+=by[d][0]; nn+=by[d][1]
        boots.append(ss/nn)
    p_one=(1+sum(1 for x in boots if x<=0))/(BOOTSTRAP_N+1)
    return {
        "repetitions":BOOTSTRAP_N,
        "block_day_count":len(days),
        "seed_sha256":hashlib.sha256((LAB+"discovery"+hlabel+"V0.1").encode()).hexdigest(),
        "ci95":[qtype7(boots,0.025),qtype7(boots,0.975)],
        "one_sided_p":p_one
    }

def holm(pmap,alpha=0.05):
    ordered=sorted(pmap.items(),key=lambda kv:(kv[1],kv[0]))
    out={k:False for k in pmap}; rows=[]; active=True; m=len(ordered)
    for i,(k,p) in enumerate(ordered):
        thr=alpha/(m-i)
        sig=active and p<=thr
        if not sig: active=False
        out[k]=sig
        rows.append({"horizon":k,"p":p,"threshold":thr,"significant":sig})
    return out,rows

authority,_=find_one(args.authority,"FINAL_PRE_DISCOVERY_AUTHORITY_RECEIPT_V0.1.json")
sample_receipt,_=find_one(args.sample_gate,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
source_receipt,_=find_one(args.market_source,"MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")
census_hits=sorted(Path(args.sample_gate).rglob("SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"))
registry_path=Path(args.registry)
hard_errors=[]

if not authority or authority.get("classification")!="FINAL_PRE_DISCOVERY_AUTHORITY_PASS":
    hard_errors.append({"reason":"final_authority_not_pass","classification":(authority or {}).get("classification")})
if not sample_receipt or sample_receipt.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
    hard_errors.append({"reason":"sample_gate_not_pass","classification":(sample_receipt or {}).get("classification")})
if not source_receipt or source_receipt.get("classification")!="MARKET_DATA_SOURCE_PASS":
    hard_errors.append({"reason":"market_source_not_pass","classification":(source_receipt or {}).get("classification")})
if not census_hits: hard_errors.append({"reason":"cluster_census_missing"})
if not registry_path.exists(): hard_errors.append({"reason":"mapping_registry_missing"})
if hard_errors:
    rec={"schema_version":"0.1","lab_id":LAB,"classification":"MARKET_DATA_SOURCE_BLOCKED","stage":"pre_acquisition_authority_check","error_count":len(hard_errors),"errors":hard_errors}
    ACQ.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n"); raise SystemExit(2)

registry_bytes=registry_path.read_bytes()
registry_sha=hashlib.sha256(registry_bytes).hexdigest()
registry=json.loads(registry_bytes)
if registry_sha!=EXPECTED_REGISTRY_SHA256:
    hard_errors.append({"reason":"registry_sha256_mismatch","observed":registry_sha,"expected":EXPECTED_REGISTRY_SHA256})
if source_receipt.get("mapping_requirements_receipt_sha256")!=EXPECTED_REQUIREMENTS_SHA256:
    hard_errors.append({"reason":"requirements_sha256_mismatch","observed":source_receipt.get("mapping_requirements_receipt_sha256"),"expected":EXPECTED_REQUIREMENTS_SHA256})

direct={}
for row in registry.get("mappings") or []:
    if row.get("status")=="BINANCE_DIRECT":
        direct[row["target_identity"]]=row

clusters=[]
with census_hits[0].open() as f:
    for line in f:
        r=json.loads(line)
        if r.get("split")!="discovery": continue
        m=direct.get(r.get("primary_market_identity"))
        if not m: continue
        x=dict(r); x["symbol"]=m["symbol"]; x["listing_start_utc"]=m["listing_start_utc"]
        clusters.append(x)
expected_mapped=int(((source_receipt.get("post_mapping_sample") or {}).get("mapped_discovery_cluster_count") or 0))
if len(clusters)!=expected_mapped:
    hard_errors.append({"reason":"mapped_discovery_cluster_count_mismatch","observed":len(clusters),"expected":expected_mapped})

symbols=sorted(set(x["symbol"] for x in clusters))
if not symbols:
    hard_errors.append({"reason":"no_direct_discovery_symbols"})

bars={s:{} for s in symbols}
archive_rows=[]
transport_errors=[]

def acquire_day(symbol,row,day):
    ds=day.isoformat()
    zip_url=row["archive_route_template"].replace("{symbol}",symbol).replace("{date}",ds)
    sum_url=row["checksum_route_template"].replace("{symbol}",symbol).replace("{date}",ds)
    ss,sb=http_bytes(sum_url,allow_404=True)
    zs,zb=http_bytes(zip_url,allow_404=True)
    base={"symbol":symbol,"date":ds,"zip_url":zip_url,"checksum_url":sum_url,"zip_http":zs,"checksum_http":ss}
    if ss==404 or zs==404:
        base.update({"status":"MISSING_ARCHIVE","observed_bars":0,"missing_minutes":1440}); return base,{}
    if ss!=200 or zs!=200 or not isinstance(sb,(bytes,bytearray)) or not isinstance(zb,(bytes,bytearray)):
        base.update({"status":"TRANSPORT_EXHAUSTED","detail":{"zip":zb if not isinstance(zb,(bytes,bytearray)) else None,"checksum":sb if not isinstance(sb,(bytes,bytearray)) else None}})
        return base,{}
    txt=sb.decode("utf-8","replace").strip()
    m=re.search(r"([0-9a-fA-F]{64})",txt)
    if not m:
        base.update({"status":"CHECKSUM_FORMAT_INVALID"}); return base,{}
    expected=m.group(1).lower(); observed=hashlib.sha256(zb).hexdigest()
    base["expected_sha256"]=expected; base["observed_sha256"]=observed
    if expected!=observed:
        base.update({"status":"CHECKSUM_MISMATCH"}); return base,{}
    try:
        z=zipfile.ZipFile(io.BytesIO(zb))
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:
            base.update({"status":"ZIP_MEMBER_COUNT_INVALID","members":names}); return base,{}
        out={}; prev=None; dup=0; nonmono=0
        with z.open(names[0]) as fh:
            reader=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
            for rec in reader:
                if not rec: continue
                t=int(rec[0]); 
                if t>10**14:t//=1000
                if t%60000!=0: 
                    base.update({"status":"TIMESTAMP_NOT_MINUTE_ALIGNED","timestamp":t}); return base,{}
                if prev is not None and t<=prev:
                    if t==prev: dup+=1
                    else: nonmono+=1
                prev=t
                if t in out: dup+=1
                out[t]=rec[1]
        start=ms(dt.datetime.combine(day,dt.time(0),tzinfo=dt.timezone.utc))
        end=start+86400000
        out={t:v for t,v in out.items() if start<=t<end}
        missing=1440-len(out)
        base.update({"status":"PASS","observed_bars":len(out),"missing_minutes":missing,"duplicate_count":dup,"non_monotonic_count":nonmono})
        if dup or nonmono:
            base["status"]="ARCHIVE_STRUCTURE_CONFLICT"
        return base,out
    except Exception as e:
        base.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:240]}); return base,{}

for symbol in symbols:
    rows=[v for v in direct.values() if v.get("symbol")==symbol]
    row=rows[0]
    listing=parse_iso(row["listing_start_utc"]).date()
    last=dt.date(2023,12,31)
    days=list(daterange(listing,last))
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs={ex.submit(acquire_day,symbol,row,d):d for d in days}
        for fut in as_completed(futs):
            ar,bd=fut.result(); archive_rows.append(ar)
            if ar["status"]=="PASS":
                bars[symbol].update(bd)
            elif ar["status"] not in ("MISSING_ARCHIVE",):
                transport_errors.append(ar)

archive_rows.sort(key=lambda x:(x["symbol"],x["date"]))
with MANIFEST.open("w") as f:
    for r in archive_rows:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")

# REST reconciliation: 5 deterministic timestamps per symbol/year.
reconciliation=[]
for symbol in symbols:
    ts_all=sorted(bars[symbol])
    years=sorted(set(dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).year for t in ts_all))
    for year in years:
        ys=[t for t in ts_all if dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).year==year]
        ranked=sorted(ys,key=lambda t:hashlib.sha256((symbol+"|"+str(year)+"|"+str(t)+"|DLS_RECON_V0.1").encode()).hexdigest())[:5]
        for t in ranked:
            q=urllib.parse.urlencode({"symbol":symbol,"interval":"1m","startTime":t,"endTime":t+59999,"limit":1})
            st,obj=http_json("https://data-api.binance.vision/api/v3/klines?"+q)
            ok=False; reason=None
            if st==200 and isinstance(obj,list) and len(obj)==1:
                rt=int(obj[0][0]); ro=str(obj[0][1]); ao=str(bars[symbol].get(t))
                ok=(rt==t and Decimal(ro)==Decimal(ao))
                if not ok: reason="archive_rest_open_conflict"
            else: reason="rest_reconciliation_transport_or_shape_failure"
            reconciliation.append({"symbol":symbol,"year":year,"timestamp_ms":t,"http_status":st,"pass":ok,"reason":reason})
            if not ok: hard_errors.append({"reason":reason,"symbol":symbol,"year":year,"timestamp_ms":t,"http_status":st})

for r in transport_errors:
    if r["status"] in ("CHECKSUM_MISMATCH","ARCHIVE_STRUCTURE_CONFLICT","TIMESTAMP_NOT_MINUTE_ALIGNED"):
        hard_errors.append({"reason":r["status"],"symbol":r["symbol"],"date":r["date"]})

# Build event proximity indexes by mapped symbol using all mapped Discovery T0s.
event_sec={}
for symbol in symbols:
    event_sec[symbol]=sorted(parse_iso(c["t0"]).timestamp() for c in clusters if c["symbol"]==symbol)

def near_event(symbol,candidate_dt):
    arr=event_sec[symbol]; x=candidate_dt.timestamp(); lo=x-14400; hi=x+14400
    i=bisect.bisect_left(arr,lo)
    return i<len(arr) and arr[i]<=hi

def all_required(symbol,t0ms):
    return all((t0ms+m*60000) in bars[symbol] for m in (0,1,5,30,240))

pairs=[]; exclusions=defaultdict(int)
for c in clusters:
    symbol=c["symbol"]; t0=parse_iso(c["t0"]); A=ceil_minute(t0)
    listing=parse_iso(c["listing_start_utc"])
    event_ms=ms(A)
    if A+dt.timedelta(minutes=240)>=DISCOVERY_END:
        exclusions["event_split_boundary"]+=1; continue
    if not all_required(symbol,event_ms):
        exclusions["event_required_bar_missing"]+=1; continue

    month_start=dt.datetime(t0.year,t0.month,1,tzinfo=dt.timezone.utc)
    if t0.month==12: month_end=dt.datetime(t0.year+1,1,1,tzinfo=dt.timezone.utc)
    else: month_end=dt.datetime(t0.year,t0.month+1,1,tzinfo=dt.timezone.utc)
    cand=[]
    d=month_start.date()
    while d<month_end.date():
        for minute in range(60):
            x=dt.datetime(d.year,d.month,d.day,t0.hour,minute,tzinfo=dt.timezone.utc)
            if x<listing or x>=DISCOVERY_END: continue
            if x+dt.timedelta(minutes=240)>=DISCOVERY_END: continue
            if near_event(symbol,x): continue
            canon=iso_minute(x)
            rank=hashlib.sha256((c["cluster_id"]+canon).encode()).hexdigest()
            cand.append((rank,x,canon))
        d+=dt.timedelta(days=1)
    cand.sort(key=lambda x:x[0])
    chosen=None
    for rank,x,canon in cand:
        cm=ms(x)
        if all_required(symbol,cm):
            chosen=(rank,x,canon,cm); break
    if chosen is None:
        exclusions["no_admissible_control"]+=1; continue

    _,ctrl,ctrl_iso,ctrl_ms=chosen
    p={"cluster_id":c["cluster_id"],"protocol":c["protocol"],"instruction_class":c["instruction_class"],
       "primary_market_identity":c["primary_market_identity"],"symbol":symbol,"event_t0":c["t0"],
       "event_aligned":iso_minute(A),"control_aligned":ctrl_iso}
    for hl,mn in HORIZONS.items():
        e0=Decimal(bars[symbol][event_ms]); eh=Decimal(bars[symbol][event_ms+mn*60000])
        c0=Decimal(bars[symbol][ctrl_ms]); ch=Decimal(bars[symbol][ctrl_ms+mn*60000])
        er=math.log(float(eh/e0)); cr=math.log(float(ch/c0))
        p["event_abs_"+hl]=abs(er); p["control_abs_"+hl]=abs(cr); p["d_"+hl]=abs(er)-abs(cr)
    pairs.append(p)

with PAIRS.open("w") as f:
    for p in pairs:f.write(json.dumps(p,sort_keys=True,separators=(",",":"))+"\n")

mapped_n=len(clusters); pair_n=len(pairs); coverage=pair_n/mapped_n if mapped_n else 0.0
inferential=[x for x in (source_receipt.get("post_mapping_subgroups") or []) if x.get("post_mapping_status")=="INFERENTIAL_DISCOVERY_AND_OOS"]
subgroup_cov=[]
for g in inferential:
    den=sum(1 for c in clusters if c["protocol"]==g["protocol"] and c["instruction_class"]==g["class"])
    num=sum(1 for p in pairs if p["protocol"]==g["protocol"] and p["instruction_class"]==g["class"])
    subgroup_cov.append({"protocol":g["protocol"],"class":g["class"],"mapped_n":den,"paired_n":num,"coverage":num/den if den else 0.0})

archive_missing=sum(int(x.get("missing_minutes") or 0) for x in archive_rows)
acq_class="DISCOVERY_MARKET_DATA_ACQUISITION_PASS"
if hard_errors or coverage<0.95 or any(x["coverage"]<0.90 for x in subgroup_cov):
    acq_class="MARKET_DATA_SOURCE_BLOCKED"
acq={
 "schema_version":"0.1","lab_id":LAB,"classification":acq_class,
 "authority_classification":authority.get("classification"),"sample_gate_classification":sample_receipt.get("classification"),
 "market_source_classification":source_receipt.get("classification"),"registry_sha256":registry_sha,
 "mapped_discovery_cluster_count":mapped_n,"paired_discovery_count":pair_n,"aggregate_pair_coverage":coverage,
 "inferential_subgroup_coverage":subgroup_cov,"exclusions":dict(exclusions),
 "archive_manifest_path":str(MANIFEST),"archive_day_count":len(archive_rows),
 "archive_missing_minute_count":archive_missing,"reconciliation":reconciliation,
 "hard_error_count":len(hard_errors),"hard_errors":hard_errors,
 "firewall":{"discovery_only":True,"oos_2024_opened":False,"protected_2025_2026_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False}
}
ACQ.write_text(json.dumps(acq,indent=2,sort_keys=True)+"\n")
if acq_class!="DISCOVERY_MARKET_DATA_ACQUISITION_PASS":
    blocked={"schema_version":"0.1","lab_id":LAB,"classification":"MARKET_DATA_SOURCE_BLOCKED",
             "acquisition_classification":acq_class,"economic_hypothesis_tested":False,
             "firewall":acq["firewall"]}
    RES.write_text(json.dumps(blocked,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":"MARKET_DATA_SOURCE_BLOCKED","paired_n":pair_n,"coverage":coverage,"hard_errors":len(hard_errors)},indent=2))
    raise SystemExit(2)

metrics={}
boot={}
for hl in HORIZONS:
    ds=[p["d_"+hl] for p in pairs]
    ev=[p["event_abs_"+hl] for p in pairs]
    co=[p["control_abs_"+hl] for p in pairs]
    metrics[hl]={"mean_paired_difference":mean(ds),"mean_event_abs":mean(ev),"mean_control_abs":mean(co),
                 "relative_uplift":(mean(ev)/mean(co)-1) if mean(co) not in (None,0) else None,
                 "positive_mean":mean(ds)>0}
    boot[hl]=bootstrap_stats(pairs,hl)

family5=[]
for g in inferential:
    ps=[p for p in pairs if p["protocol"]==g["protocol"] and p["instruction_class"]==g["class"]]
    family5.append({"protocol":g["protocol"],"class":g["class"],"n":len(ps),"mean_d_5m":mean([p["d_5m"] for p in ps]),
                    "positive":bool(ps) and mean([p["d_5m"] for p in ps])>0})

sec_p={h:boot[h]["one_sided_p"] for h in ("1m","30m","240m")}
holm_sig,holm_rows=holm(sec_p)
checks={
 "paired_n_ge_1000":pair_n>=1000,
 "mean_d_5m_positive":metrics["5m"]["mean_paired_difference"]>0,
 "bootstrap_ci_5m_lower_positive":boot["5m"]["ci95"][0]>0,
 "relative_uplift_5m_ge_10pct":metrics["5m"]["relative_uplift"] is not None and metrics["5m"]["relative_uplift"]>=0.10,
 "two_inferential_families_positive_5m":sum(1 for x in family5 if x["positive"])>=2,
 "two_secondary_horizons_positive":sum(1 for h in ("1m","30m","240m") if metrics[h]["positive"])>=2,
 "one_secondary_holm_significant":sum(1 for v in holm_sig.values() if v)>=1
}
classification="SURVIVES_DISCOVERY" if all(checks.values()) else "NO_EDGE_DISCOVERY"
result={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,"split":"discovery",
 "paired_n":pair_n,"mapped_source_n":mapped_n,"pair_coverage":coverage,
 "metrics":metrics,"bootstrap":boot,"inferential_family_5m":family5,
 "holm_bonferroni":{"alpha":0.05,"rows":holm_rows,"significant":holm_sig},
 "discovery_checks":checks,
 "acquisition_classification":acq_class,
 "oos_authorized_next":classification=="SURVIVES_DISCOVERY",
 "oos_2024_opened":False,"protected_2025_2026_opened":False,
 "firewall":{"post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False}
}
RES.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"paired_n":pair_n,"coverage":coverage,
                  "mean_d_5m":metrics["5m"]["mean_paired_difference"],
                  "uplift_5m":metrics["5m"]["relative_uplift"],
                  "ci5":boot["5m"]["ci95"],"checks":checks},indent=2))

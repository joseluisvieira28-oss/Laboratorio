#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,time,urllib.error,urllib.parse,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
TARGET="mint:So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,9,28,tzinfo=dt.timezone.utc)
PRIMARY_COST=0.0026
HARD_STRESS=0.0040
BOOTSTRAPS=5000
MIN_TRADES=500
MIN_FAMILY_TRADES=100
ARCHIVE="https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip"
CHECKSUM=ARCHIVE+".CHECKSUM"

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
ap.add_argument("--workers",type=int,default=12)
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)

def parse_ts(s):return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)
def minute_ms(x):return int(x.timestamp()//60)*60000
def strict_next_minute_ms(x):return (int(x.timestamp()//60)+1)*60000
def iso_ms(ms):return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")
def daterange(a,b):
    d=a
    while d<b:
        yield d
        d+=dt.timedelta(days=1)
def get_bytes(url,retries=6,allow_404=False):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-2026-economic/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404:return 404,None
            last=f"http_{e.code}"
            if e.code in (429,500,502,503,504):
                time.sleep(min(16,2**i));continue
            return e.code,None
        except Exception as e:
            last=f"{type(e).__name__}:{str(e)[:160]}";time.sleep(min(16,2**i))
    return None,None

def get_json(url):
    st,b=get_bytes(url)
    if st!=200 or b is None:return st,None
    try:return st,json.loads(b)
    except Exception:return st,None

receipt_hits=sorted(Path(args.source_root).rglob("FINAL_2026_SOURCE_AUTHORITY_RECEIPT_V0.1.json"))
census_hits=sorted(Path(args.source_root).rglob("FINAL_2026_SOURCE_CLUSTER_CENSUS_V0.1.ndjson"))
errors=[]
if len(receipt_hits)!=1:errors.append({"reason":"source_authority_receipt_count","observed":len(receipt_hits)})
if len(census_hits)!=1:errors.append({"reason":"source_cluster_census_count","observed":len(census_hits)})
if errors:
    raise SystemExit(json.dumps(errors))
source_receipt=json.loads(receipt_hits[0].read_text())
if source_receipt.get("classification")!="FINAL_2026_SOURCE_AUTHORITY_PASS":
    raise SystemExit("SOURCE_AUTHORITY_NOT_PASS")

clusters=[]
with census_hits[0].open() as f:
    for line in f:
        if not line.strip():continue
        c=json.loads(line)
        if c.get("primary_market_identity")!=TARGET:continue
        t0=parse_ts(c["t0"])
        if START<=t0<END:clusters.append(c)
clusters.sort(key=lambda c:(c["t0"],c["cluster_id"]))
if not clusters:raise SystemExit("NO_2026_SOL_CLUSTERS")

def acquire_day(day):
    ds=day.isoformat();zu=ARCHIVE.format(symbol=SYMBOL,date=ds);cu=CHECKSUM.format(symbol=SYMBOL,date=ds)
    cs,cb=get_bytes(cu,allow_404=True);zs,zb=get_bytes(zu,allow_404=True)
    qa={"date":ds,"checksum_http":cs,"zip_http":zs,"accepted":False,"observed_bars":0}
    if cs==404 or zs==404 or cb is None or zb is None:
        qa["reason"]="missing_archive";return qa,{},[]
    txt=cb.decode("utf-8","replace")
    m=re.search(r"([0-9a-fA-F]{64})",txt)
    if not m:
        qa["reason"]="checksum_format";return qa,{},["checksum_format"]
    exp=m.group(1).lower();act=hashlib.sha256(zb).hexdigest()
    qa["checksum_expected"]=exp;qa["checksum_actual"]=act
    if exp!=act:
        qa["reason"]="checksum_mismatch";return qa,{},["checksum_mismatch"]
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            names=[n for n in z.namelist() if not n.endswith("/")]
            if len(names)!=1:return {**qa,"reason":"archive_member_count"},{},["archive_member_count"]
            bars={};prev=None;dup=0;nonmono=0;outside=0;bad=0
            lo=int(dt.datetime(day.year,day.month,day.day,tzinfo=dt.timezone.utc).timestamp()*1000)
            hi=lo+86400000
            with z.open(names[0]) as raw:
                for row in csv.reader(io.TextIOWrapper(raw,encoding="utf-8")):
                    if len(row)<2:bad+=1;continue
                    try:
                        t=int(row[0])
                        if t<10**14:t*=1000
                        if t%60000!=0:bad+=1;continue
                        Decimal(row[1])
                    except Exception:bad+=1;continue
                    if not(lo<=t<hi):outside+=1;continue
                    if prev is not None and t<=prev:nonmono+=1
                    prev=t
                    if t in bars:dup+=1
                    bars[t]=row[1]
            qa.update({"accepted":not any((dup,nonmono,outside,bad)),"observed_bars":len(bars),
                       "duplicate_count":dup,"non_monotonic_count":nonmono,"out_of_day_count":outside,"bad_row_count":bad})
            if not qa["accepted"]:return qa,{},["archive_integrity_conflict"]
            qa["reason"]="accepted";return qa,bars,[]
    except Exception as e:
        qa["reason"]="archive_parse_error";qa["detail"]=f"{type(e).__name__}:{str(e)[:160]}"
        return qa,{},["archive_parse_error"]

qas=[];bars={};conflicts=[]
days=list(daterange(START.date(),END.date()))
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in days}
    for fut in as_completed(futs):
        qa,b,cf=fut.result();qas.append(qa);bars.update(b)
        if cf:conflicts.append({"date":qa["date"],"reasons":cf})
qas.sort(key=lambda x:x["date"])

# Deterministic archive/REST reconciliation: exact frozen 5 samples for 2026.
mins=sorted(bars)
ranked=sorted(mins,key=lambda t:hashlib.sha256(f"{SYMBOL}|2026|{t}|DLS_RECON_V0.1".encode()).digest())[:5]
recon=[]
for t in ranked:
    qs=urllib.parse.urlencode({"symbol":SYMBOL,"interval":"1m","startTime":t,"endTime":t+59999,"limit":1})
    st,obj=get_json("https://data-api.binance.vision/api/v3/klines?"+qs)
    ok=False;ro=None;rt=None
    if st==200 and isinstance(obj,list) and len(obj)==1:
        rt=int(obj[0][0]);ro=str(obj[0][1])
        try:ok=(rt==t and Decimal(ro)==Decimal(bars[t]))
        except Exception:ok=False
    recon.append({"timestamp_ms":t,"http_status":st,"archive_open":bars.get(t),"rest_open":ro,"rest_open_time":rt,"pass":ok})
    if not ok:conflicts.append({"reason":"archive_rest_reconciliation_failed","timestamp_ms":t})

# Market resolvability before operational overlap suppression.
resolved=[]
missing=[]
for c in clusters:
    e=strict_next_minute_ms(parse_ts(c["t0"]))
    x=e+5*60000
    if x>=int(END.timestamp()*1000):
        missing.append({"cluster_id":c["cluster_id"],"reason":"exit_crosses_final_cutoff"});continue
    if e not in bars or x not in bars:
        missing.append({"cluster_id":c["cluster_id"],"reason":"required_bar_missing","entry":iso_ms(e),"exit":iso_ms(x)});continue
    resolved.append((c,e,x))
coverage=len(resolved)/len(clusters) if clusters else 0.0

# Frozen one-position-at-a-time serialization.
accepted=[];suppressed=0;current_exit=None
for c,e,x in sorted(resolved,key=lambda z:(z[1],z[0]["cluster_id"])):
    if current_exit is not None and e<current_exit:
        suppressed+=1;continue
    entry=float(Decimal(bars[e]));exitp=float(Decimal(bars[x]))
    gross=(entry-exitp)/entry
    accepted.append({"cluster_id":c["cluster_id"],"protocol":c["protocol"],"instruction_class":c["instruction_class"],
                     "t0":c["t0"],"entry_time":iso_ms(e),"exit_time":iso_ms(x),
                     "entry_open":entry,"exit_open":exitp,"gross_short_return":gross,
                     "net_return_26bps":gross-PRIMARY_COST,"net_return_40bps":gross-HARD_STRESS})
    current_exit=x

qa={"schema_version":"0.1","lab_id":LAB,"classification":"FINAL_2026_MARKET_DATA_PASS",
    "source_cluster_count":len(clusters),"market_resolved_cluster_count":len(resolved),
    "market_pair_coverage":coverage,"missing_cluster_count":len(missing),"missing_examples":missing[:100],
    "archive_day_count":len(qas),"accepted_archive_day_count":sum(1 for q in qas if q.get("accepted")),
    "source_conflict_count":len(conflicts),"source_conflicts":conflicts,
    "reconciliation":recon,"post_cutoff_2026_opened":False}
if conflicts or coverage<0.95:
    qa["classification"]="SOURCE_BLOCKED_2026_FINAL_HOLDOUT"
Path(OUT/"FINAL_2026_ECONOMIC_MARKET_QA_V0.1.json").write_text(json.dumps(qa,indent=2,sort_keys=True)+"\n")
if qa["classification"]!="FINAL_2026_MARKET_DATA_PASS":
    result={"schema_version":"0.1","lab_id":LAB,"classification":"SOURCE_BLOCKED_2026_FINAL_HOLDOUT",
            "economic_inference_computed":False,"source_cluster_count":len(clusters),
            "market_pair_coverage":coverage,"post_cutoff_2026_opened":False,
            "firewall":{"post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
    Path(OUT/"FINAL_2026_ECONOMIC_HOLDOUT_RECEIPT_V0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2));raise SystemExit(2)

with Path(OUT/"FINAL_2026_SERIALIZED_TRADES_V0.1.ndjson").open("w") as f:
    for r in accepted:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")

def qtype7(vals,q):
    s=sorted(vals);n=len(s)
    if n==1:return s[0]
    h=(n-1)*q;lo=math.floor(h);hi=math.ceil(h)
    if lo==hi:return s[lo]
    return s[lo]+(s[hi]-s[lo])*(h-lo)

def bootstrap(rows,key):
    by=defaultdict(list)
    for r in rows:by[r["t0"][:10]].append(r[key])
    days=sorted(by)
    seed=int(hashlib.sha256((LAB+"2026-final-holdout"+"5m"+"V0.1").encode()).hexdigest(),16)
    rng=random.Random(seed);boot=[]
    for _ in range(BOOTSTRAPS):
        vals=[]
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))]
            vals.extend(by[d])
        boot.append(sum(vals)/len(vals))
    return {"mean":sum(r[key] for r in rows)/len(rows),
            "ci95":[qtype7(boot,.025),qtype7(boot,.975)],
            "one_sided_p":(1+sum(1 for x in boot if x<=0))/(BOOTSTRAPS+1),
            "day_block_count":len(days),"repetitions":BOOTSTRAPS}

primary=bootstrap(accepted,"net_return_26bps")
stress=bootstrap(accepted,"net_return_40bps")
families=[]
for p in sorted({r["protocol"] for r in accepted}):
    vals=[r["net_return_26bps"] for r in accepted if r["protocol"]==p]
    families.append({"protocol":p,"n":len(vals),"mean_net_return_26bps":sum(vals)/len(vals),
                     "eligible_for_family_gate":len(vals)>=MIN_FAMILY_TRADES,
                     "positive":len(vals)>=MIN_FAMILY_TRADES and sum(vals)/len(vals)>0})
positive_families=sum(1 for x in families if x["positive"])
gates={"serialized_trade_n_ge_500":len(accepted)>=MIN_TRADES,
       "market_pair_coverage_ge_95pct":coverage>=0.95,
       "mean_net_26bps_positive":primary["mean"]>0,
       "ci95_net_26bps_lower_positive":primary["ci95"][0]>0,
       "two_protocol_families_n100_positive":positive_families>=2}
passed=all(gates.values())
result={"schema_version":"0.1","lab_id":LAB,
        "classification":"SURVIVES_2026_FINAL_HOLDOUT" if passed else "NO_EDGE_2026_FINAL_HOLDOUT",
        "source_cluster_count":len(clusters),"market_resolved_cluster_count":len(resolved),
        "market_pair_coverage":coverage,"serialized_trade_count":len(accepted),"overlap_suppressed_count":suppressed,
        "primary_cost_hurdle":PRIMARY_COST,"hard_stress_hurdle":HARD_STRESS,
        "primary_net_statistics":primary,"hard_stress_statistics":stress,
        "protocol_families":families,"positive_family_count":positive_families,
        "gates":gates,"post_cutoff_2026_opened":False,
        "strategy_freeze":"STRATEGY_TRANSLATION_FREEZE_V0.1.md",
        "cost_freeze":"EXECUTION_COST_FREEZE_V0.1.md",
        "firewall":{"post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
Path(OUT/"FINAL_2026_ECONOMIC_HOLDOUT_RECEIPT_V0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))

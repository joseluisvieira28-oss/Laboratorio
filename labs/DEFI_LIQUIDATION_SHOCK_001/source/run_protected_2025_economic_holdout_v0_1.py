#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,time,urllib.error,urllib.parse,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
SYMBOL="SOLUSDT"
START=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
PRIMARY_COST=0.0026
STRESS_COST=0.0040
BOOTSTRAPS=5000
INFERENTIAL_FAMILIES=("kamino","marginfi","save11")
TARGET="mint:So11111111111111111111111111111111111111112"

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--oos-lock",required=True)
ap.add_argument("--direction-lock",required=True)
ap.add_argument("--fee-authority",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
ACQ=OUT/"PROTECTED_2025_ECONOMIC_HOLDOUT_ACQUISITION_RECEIPT_V0.1.json"
RES=OUT/"PROTECTED_2025_ECONOMIC_HOLDOUT_RECEIPT_V0.1.json"
ROWS=OUT/"PROTECTED_2025_ECONOMIC_HOLDOUT_TRADES_V0.1.ndjson"

def find_unique(root,names):
    hits=[]
    for n in names:hits.extend(Path(root).rglob(n))
    hits=sorted(set(hits))
    if len(hits)!=1:raise RuntimeError(f"expected_one:{names}:found={len(hits)}")
    return hits[0]

def iso(s):return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)
def minute_ms(x):return int(x.timestamp()//60)*60000
def strict_next_minute_ms(x):return (int(x.timestamp()//60)+1)*60000
def canon_ms(ms):return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def mean(xs):return sum(xs)/len(xs) if xs else None
def qtype7(vals,q):
    s=sorted(vals);n=len(s)
    if not n:return None
    if n==1:return s[0]
    h=(n-1)*q;lo=math.floor(h);hi=math.ceil(h)
    if lo==hi:return s[lo]
    return s[lo]+(s[hi]-s[lo])*(h-lo)

def get_bytes(url,retries=6,allow_404=False):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-2025-holdout/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404:return 404,None
            last=f"HTTP_{e.code}"
            if e.code in (429,500,502,503,504):
                time.sleep(min(20,2**i));continue
            raise RuntimeError(f"nonretry_http:{e.code}:{url}")
        except Exception as e:
            last=f"{type(e).__name__}:{str(e)[:200]}";time.sleep(min(20,2**i))
    raise RuntimeError(f"transport_exhausted:{last}:{url}")

def get_json(url):
    st,b=get_bytes(url,retries=6,allow_404=False)
    if st!=200:raise RuntimeError(f"json_http_{st}:{url}")
    return json.loads(b)

oos=json.loads(Path(args.oos_lock).read_text())
direction=json.loads(Path(args.direction_lock).read_text())
fee=json.loads(Path(args.fee_authority).read_text())
if oos.get("classification")!="SURVIVES_OOS":raise SystemExit("OOS_LOCK_NOT_PASS")
if direction.get("classification")!="DIRECTION_SOURCE_ROLE_AUDIT_PASS":raise SystemExit("DIRECTION_LOCK_NOT_PASS")
if direction.get("prospective_hypothesis")!="H_SHORT_COLLATERAL_LIQUIDATION_V0.1":raise SystemExit("DIRECTION_HYPOTHESIS_MISMATCH")
if fee.get("classification")!="MEXC_API_FUTURES_FEE_AUTHORITY_PASS":raise SystemExit("FEE_AUTHORITY_NOT_PASS")
if abs(float(fee["primary_execution_assumption"]["primary_all_in_cost_hurdle"])-PRIMARY_COST)>1e-12:
    raise SystemExit("PRIMARY_COST_AUTHORITY_MISMATCH")

srcp=find_unique(args.source_root,["PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.2.json","PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.1.json"])
censp=find_unique(args.source_root,["PROTECTED_2025_SOURCE_CLUSTER_CENSUS_V0.2.ndjson","PROTECTED_2025_SOURCE_CLUSTER_CENSUS_V0.1.ndjson"])
src=json.loads(srcp.read_text())
if src.get("classification")!="PROTECTED_2025_SOURCE_AUTHORITY_PASS":
    raise SystemExit("PROTECTED_2025_SOURCE_AUTHORITY_NOT_PASS")

clusters=[]
with censp.open() as f:
    for line in f:
        if not line.strip():continue
        r=json.loads(line)
        if r.get("primary_market_identity")!=TARGET:continue
        if r.get("split")!="protected_2025":raise SystemExit("UNEXPECTED_CLUSTER_SPLIT")
        t0=iso(r["t0"])
        e_ms=strict_next_minute_ms(t0)
        x_ms=e_ms+5*60000
        if e_ms<int(START.timestamp()*1000):continue
        if x_ms>=int(END.timestamp()*1000):
            continue
        r["_e_ms"]=e_ms;r["_x_ms"]=x_ms;r["_t0_dt"]=t0
        clusters.append(r)
if not clusters:raise SystemExit("ZERO_ELIGIBLE_2025_SOURCE_CLUSTERS")

required_dates=set()
for r in clusters:
    required_dates.add(dt.datetime.fromtimestamp(r["_e_ms"]/1000,dt.timezone.utc).date())
    required_dates.add(dt.datetime.fromtimestamp(r["_x_ms"]/1000,dt.timezone.utc).date())

def acquire_day(day):
    ds=day.isoformat()
    base=f"https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    cst,cb=get_bytes(base+".CHECKSUM",allow_404=True)
    zst,zb=get_bytes(base,allow_404=True)
    qa={"date":ds,"zip_http":zst,"checksum_http":cst,"status":None,"observed_bars":0}
    if cst==404 or zst==404 or cb is None or zb is None:
        qa["status"]="MISSING_ARCHIVE";return qa,{}
    expected=cb.decode("utf-8","replace").strip().split()[0].lower()
    actual=hashlib.sha256(zb).hexdigest()
    qa["expected_sha256"]=expected;qa["observed_sha256"]=actual
    if expected!=actual:
        qa["status"]="CHECKSUM_MISMATCH";return qa,{}
    out={}
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            names=[n for n in z.namelist() if not n.endswith("/")]
            if len(names)!=1:
                qa["status"]="ZIP_MEMBER_COUNT_INVALID";return qa,{}
            d0=int(dt.datetime(day.year,day.month,day.day,tzinfo=dt.timezone.utc).timestamp()*1000)
            d1=d0+86400000;prev=None;dup=0;nonmono=0;outside=0;bad=0
            with z.open(names[0]) as raw:
                reader=csv.reader(io.TextIOWrapper(raw,encoding="utf-8"))
                for row in reader:
                    if len(row)<2:bad+=1;continue
                    try:
                        t=int(row[0])
                        if t>10**14:t//=1000
                        Decimal(row[1])
                    except Exception:
                        bad+=1;continue
                    if t%60000!=0:bad+=1;continue
                    if not(d0<=t<d1):outside+=1;continue
                    if prev is not None and t<=prev:
                        if t==prev:dup+=1
                        else:nonmono+=1
                    prev=t
                    if t in out:dup+=1
                    out[t]=row[1]
            qa.update({"observed_bars":len(out),"missing_minutes":1440-len(out),
                       "duplicate_count":dup,"non_monotonic_count":nonmono,
                       "out_of_day_count":outside,"bad_row_count":bad})
            if dup or nonmono or outside or bad:
                qa["status"]="ARCHIVE_INTEGRITY_CONFLICT";return qa,{}
            qa["status"]="PASS";return qa,out
    except Exception as e:
        qa["status"]="ARCHIVE_PARSE_FAILURE";qa["detail"]=f"{type(e).__name__}:{str(e)[:200]}"
        return qa,{}

qas=[];opens={};hard=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    futs={ex.submit(acquire_day,d):d for d in sorted(required_dates)}
    for fut in as_completed(futs):
        qa,bars=fut.result();qas.append(qa)
        if qa["status"] not in ("PASS","MISSING_ARCHIVE"):
            hard.append({"reason":qa["status"],"date":qa["date"]})
        opens.update(bars)
qas.sort(key=lambda x:x["date"])

# Deterministic archive/REST reconciliation.
recon=[]
times=sorted(opens)
ranked=sorted(times,key=lambda t:hashlib.sha256(f"{SYMBOL}|2025|{t}|DLS_RECON_V0.1".encode()).digest())[:5]
for t in ranked:
    q=urllib.parse.urlencode({"symbol":SYMBOL,"interval":"1m","startTime":t,"endTime":t+59999,"limit":1})
    obj=get_json("https://data-api.binance.vision/api/v3/klines?"+q)
    ok=False;rest_open=None;rest_t=None
    if isinstance(obj,list) and len(obj)==1 and len(obj[0])>=2:
        rest_t=int(obj[0][0]);rest_open=str(obj[0][1])
        ok=(rest_t==t and Decimal(rest_open)==Decimal(opens[t]))
    recon.append({"timestamp_ms":t,"minute":canon_ms(t),"archive_open":opens.get(t),
                  "rest_open":rest_open,"rest_open_time":rest_t,"pass":ok})
    if not ok:hard.append({"reason":"ARCHIVE_REST_RECONCILIATION_CONFLICT","timestamp_ms":t})

market_complete=[];missing=defaultdict(int)
for r in clusters:
    e=r["_e_ms"];x=r["_x_ms"]
    if e not in opens or x not in opens:
        missing["required_bar_missing"]+=1;continue
    market_complete.append(r)
coverage=len(market_complete)/len(clusters) if clusters else 0.0

acq={
 "schema_version":"0.1","lab_id":LAB,
 "classification":"PROTECTED_2025_MARKET_ACQUISITION_PASS" if not hard and coverage>=0.95 else "SOURCE_BLOCKED_2025_ECONOMIC_HOLDOUT",
 "source_authority_classification":src.get("classification"),
 "source_authority_sha256":sha256_file(srcp),"source_census_sha256":sha256_file(censp),
 "source_cluster_denominator":len(clusters),"source_market_complete_count":len(market_complete),
 "source_market_coverage":coverage,"missing_reasons":dict(missing),
 "required_archive_day_count":len(required_dates),"archive_receipts":qas,
 "reconciliation":recon,"hard_error_count":len(hard),"hard_errors":hard,
 "returns_computed_before_coverage_gate":False,
 "firewall":{"protected_2025_market_outcomes_opened":True,"protected_2026_outcomes_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False}
}
ACQ.write_text(json.dumps(acq,indent=2,sort_keys=True)+"\n")
if hard or coverage<0.95:
    rec={"schema_version":"0.1","lab_id":LAB,"classification":"SOURCE_BLOCKED_2025_ECONOMIC_HOLDOUT",
         "economic_inference_computed":False,"source_market_coverage":coverage,
         "hard_error_count":len(hard),"protected_2026_outcomes_opened":False,
         "post_outcome_tuning":False,"live_trading":False,"merge_main":False}
    RES.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True))
    raise SystemExit(2)

# Frozen non-overlap serialization.
market_complete.sort(key=lambda r:(r["_e_ms"],r["cluster_id"]))
accepted=[];current_exit=None;suppressed=0
for r in market_complete:
    if current_exit is not None and r["_e_ms"]<current_exit:
        suppressed+=1;continue
    accepted.append(r);current_exit=r["_x_ms"]

trades=[]
for r in accepted:
    pe=Decimal(opens[r["_e_ms"]]);px=Decimal(opens[r["_x_ms"]])
    gross=float((pe-px)/pe)
    trades.append({
      "cluster_id":r["cluster_id"],"protocol":r["protocol"],"instruction_class":r["instruction_class"],
      "t0":r["t0"],"entry_minute":canon_ms(r["_e_ms"]),"exit_minute":canon_ms(r["_x_ms"]),
      "entry_open":str(pe),"exit_open":str(px),
      "gross_short_return":gross,"net_primary_26bps":gross-PRIMARY_COST,"net_stress_40bps":gross-STRESS_COST
    })

with ROWS.open("w") as f:
    for x in trades:f.write(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n")

vals=[x["net_primary_26bps"] for x in trades]
byday=defaultdict(list)
for x in trades:byday[x["t0"][:10]].append(x["net_primary_26bps"])
days=sorted(byday)
seed_text=LAB+"2025-economic-holdout"+"5m"+"V0.1"
seed=int(hashlib.sha256(seed_text.encode()).hexdigest(),16)
rng=random.Random(seed);boots=[]
for _ in range(BOOTSTRAPS):
    sample=[]
    for __ in range(len(days)):
        d=days[rng.randrange(len(days))]
        sample.extend(byday[d])
    boots.append(mean(sample))
ci=[qtype7(boots,0.025),qtype7(boots,0.975)] if boots else [None,None]
p_one=(1+sum(1 for x in boots if x<=0))/(BOOTSTRAPS+1) if boots else None

fam=[]
for p in INFERENTIAL_FAMILIES:
    xs=[x["net_primary_26bps"] for x in trades if x["protocol"]==p]
    fam.append({"protocol":p,"n":len(xs),"mean_net_primary":mean(xs),"positive":bool(xs and mean(xs)>0)})
positive_fams=sum(1 for x in fam if x["positive"])
m_primary=mean(vals)
m_stress=mean([x["net_stress_40bps"] for x in trades])
gates={
 "serialized_n_ge_500":len(trades)>=500,
 "source_market_coverage_ge_95pct":coverage>=0.95,
 "mean_net_primary_positive":m_primary is not None and m_primary>0,
 "bootstrap_ci95_lower_positive":ci[0] is not None and ci[0]>0,
 "two_inferential_protocol_families_positive":positive_fams>=2
}
passed=all(gates.values())
classification="SURVIVES_2025_ECONOMIC_HOLDOUT" if passed else "NO_EDGE_2025_ECONOMIC_HOLDOUT"
res={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "hypothesis":"H_SHORT_COLLATERAL_LIQUIDATION_V0.1",
 "direction":"SHORT","holding_minutes":5,"primary_cost_hurdle":PRIMARY_COST,"stress_cost_hurdle":STRESS_COST,
 "source_cluster_denominator":len(clusters),"source_market_complete_count":len(market_complete),
 "source_market_coverage":coverage,"serialized_trade_count":len(trades),
 "overlap_suppressed_signal_count":suppressed,
 "mean_gross_short_return":mean([x["gross_short_return"] for x in trades]),
 "mean_net_primary_26bps":m_primary,"mean_net_stress_40bps":m_stress,
 "bootstrap":{"repetitions":BOOTSTRAPS,"block_day_count":len(days),
              "seed_sha256":hashlib.sha256(seed_text.encode()).hexdigest(),
              "ci95_primary_net":ci,"one_sided_p":p_one},
 "inferential_protocol_families":fam,"positive_inferential_protocol_family_count":positive_fams,
 "gates":gates,"all_primary_gates_pass":passed,
 "source_authority_sha256":sha256_file(srcp),"source_census_sha256":sha256_file(censp),
 "oos_lock_sha256":sha256_file(Path(args.oos_lock)),
 "direction_lock_sha256":sha256_file(Path(args.direction_lock)),
 "fee_authority_sha256":sha256_file(Path(args.fee_authority)),
 "implementation_freeze":"PROTECTED_2025_ECONOMIC_HOLDOUT_IMPLEMENTATION_FREEZE_V0.1.md",
 "firewall":{"protected_2025_market_outcomes_opened":True,"protected_2026_outcomes_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False}
}
RES.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
print(json.dumps(res,indent=2,sort_keys=True))

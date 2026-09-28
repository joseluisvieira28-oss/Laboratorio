#!/usr/bin/env python3
from __future__ import annotations
import argparse, bisect, csv, datetime as dt, hashlib, io, json, math, random, re, time, urllib.error, urllib.parse, urllib.request, zipfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

LAB_ID = "DEFI-LIQUIDATION-SHOCK-001"
SCHEMA_VERSION = "0.1"
TARGET = "mint:So11111111111111111111111111111111111111112"
SYMBOL = "SOLUSDT"
TIMEFRAME = "1m"
HORIZONS_MIN = [1, 5, 30, 240]
PRIMARY_H = 5
BOOTSTRAP_REPS = 5000
DISCOVERY_START = dt.datetime(2021,12,8,tzinfo=dt.timezone.utc)
DISCOVERY_END = dt.datetime(2024,1,1,tzinfo=dt.timezone.utc)
OOS_START = DISCOVERY_END
OOS_END = dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
PROTECTED_START = OOS_END
EXPECTED_CENSUS_SHA256 = "0a10bf5ff4d7ad41f4764c4c1eb592c28f25b01b0a854b144944adf46363d46b"
EXPECTED_SAMPLE_RECEIPT_SHA256 = "abfd67aed58ef9a486995d5b211606a7e007ad49eeef8cb9fdf387eff19ac34d"
EXPECTED_FEASIBILITY_RECEIPT_SHA256 = "4537e4e4b85dab3bcd1a79f38b76dafe1c715057f23b28c77f3ba111a0f1e67d"
EXPECTED_FINAL_AUTHORITY_RECEIPT_SHA256 = "1d9ad1290f0cfc7959c709a2623bb09863365ee9ee920358420d086047455d5c"
EXPECTED_MAPPING_REGISTRY_SHA256 = "97ff771dbeb2ec9c3b0a408edd8733701a973ffc1ae597413fbfed4455482f90"
ARCHIVE_TEMPLATE = "https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip"
CHECKSUM_TEMPLATE = ARCHIVE_TEMPLATE + ".CHECKSUM"
API_BASES = [
    "https://api.binance.com",
    "https://api-gcp.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api4.binance.com",
    "https://data-api.binance.vision",
]

class SourceBlocked(RuntimeError):
    pass

class ContractError(RuntimeError):
    pass

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_json(obj) -> bytes:
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()

def find_one(root: Path, name: str) -> Path:
    hits=sorted(root.rglob(name))
    if len(hits)!=1:
        raise ContractError(f"expected exactly one {name}, found {len(hits)}")
    return hits[0]

def load_json_exact(root: Path, name: str, expected_sha: str|None=None):
    p=find_one(root,name)
    b=p.read_bytes()
    if expected_sha and sha256_bytes(b)!=expected_sha:
        raise ContractError(f"sha mismatch {name}: {sha256_bytes(b)}")
    return json.loads(b),p

def parse_iso(s:str)->dt.datetime:
    x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if x.tzinfo is None:
        x=x.replace(tzinfo=dt.timezone.utc)
    return x.astimezone(dt.timezone.utc)

def ms(x:dt.datetime)->int:
    return int(x.timestamp()*1000)

def iso_ms(t:int)->str:
    return dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ceil_minute_ms(x:dt.datetime)->int:
    t=ms(x)
    return ((t+59999)//60000)*60000

def http_get_bytes(url:str,retries=6,timeout=60,allow_404=False):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-discovery/0.1","Accept":"*/*"})
            with urllib.request.urlopen(q,timeout=timeout) as r:
                if int(r.status)!=200:
                    raise RuntimeError(f"HTTP_{r.status}")
                return r.read()
        except urllib.error.HTTPError as e:
            last=f"HTTP_{e.code}"
            if allow_404 and e.code==404:
                return None
            if e.code in (429,500,502,503,504):
                time.sleep(min(20,2**i))
                continue
            raise SourceBlocked(f"download_failed {url} {last}")
        except Exception as e:
            last=f"{type(e).__name__}:{str(e)[:160]}"
            time.sleep(min(20,2**i))
    raise SourceBlocked(f"download_exhausted {url} {last}")

def http_json_fallback(path_qs:str,retries_each=3):
    attempts=[]
    for base in API_BASES:
        url=base+path_qs
        try:
            b=http_get_bytes(url,retries=retries_each,timeout=45)
            attempts.append({"base":base,"status":200})
            return json.loads(b),attempts
        except Exception as e:
            attempts.append({"base":base,"error":str(e)[:200]})
    raise SourceBlocked("all_binance_public_api_routes_failed:"+json.dumps(attempts,separators=(",",":")))

def month_days(year:int,month:int,start:dt.datetime,end:dt.datetime):
    first=dt.datetime(year,month,1,tzinfo=dt.timezone.utc)
    if month==12:
        nxt=dt.datetime(year+1,1,1,tzinfo=dt.timezone.utc)
    else:
        nxt=dt.datetime(year,month+1,1,tzinfo=dt.timezone.utc)
    lo=max(first,start)
    hi=min(nxt,end)
    d=lo.date()
    while dt.datetime.combine(d,dt.time(),dt.timezone.utc)<hi:
        yield d
        d += dt.timedelta(days=1)

def parse_kline_zip(zip_bytes:bytes, day:dt.date):
    rows=[]
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise SourceBlocked(f"unexpected_zip_members {day} {names[:5]}")
        with z.open(names[0]) as fh:
            txt=io.TextIOWrapper(fh,encoding="utf-8",newline="")
            prev=None
            seen=set()
            for r in csv.reader(txt):
                if not r:
                    continue
                try:
                    t=int(r[0])
                    op=Decimal(r[1])
                except Exception:
                    continue
                if t%60000!=0:
                    raise SourceBlocked(f"non_minute_timestamp {day} {t}")
                if prev is not None and t<=prev:
                    raise SourceBlocked(f"non_monotonic_archive {day} {t}")
                if t in seen:
                    raise SourceBlocked(f"duplicate_archive_timestamp {day} {t}")
                prev=t
                seen.add(t)
                rows.append((t,op))
    return rows

def download_market(months:set[tuple[int,int]],start:dt.datetime,end:dt.datetime,cache:Path):
    cache.mkdir(parents=True,exist_ok=True)
    prices={}
    manifests=[]
    missing_minutes=0
    expected_minutes=0
    for y,m in sorted(months):
        seg_start=max(dt.datetime(y,m,1,tzinfo=dt.timezone.utc),start)
        seg_end=min(dt.datetime(y+1,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(y,m+1,1,tzinfo=dt.timezone.utc),end)
        expected_minutes += int((seg_end-seg_start).total_seconds()//60)
        for day in month_days(y,m,start,end):
            ds=day.isoformat()
            fn=f"{SYMBOL}-1m-{ds}.zip"
            zp=cache/fn
            cp=cache/(fn+".CHECKSUM")
            url=ARCHIVE_TEMPLATE.format(symbol=SYMBOL,date=ds)
            curl=CHECKSUM_TEMPLATE.format(symbol=SYMBOL,date=ds)
            if not zp.exists() or not cp.exists():
                zb=http_get_bytes(url,allow_404=True)
                cb=http_get_bytes(curl,allow_404=True)
                if zb is None or cb is None:
                    manifests.append({"date":ds,"archive":fn,"checksum_object":fn+".CHECKSUM","status":"MISSING_ARCHIVE","row_count":0})
                    continue
                zp.write_bytes(zb)
                cp.write_bytes(cb)
            zbytes=zp.read_bytes()
            checksum_text=cp.read_text(errors="replace").strip()
            expected=checksum_text.split()[0].lower() if checksum_text else ""
            actual=sha256_bytes(zbytes)
            if not re.fullmatch(r"[0-9a-f]{64}",expected) or actual!=expected:
                raise SourceBlocked(f"checksum_mismatch {ds} expected={expected} actual={actual}")
            dayrows=parse_kline_zip(zbytes,day)
            for t,op in dayrows:
                if t in prices:
                    raise SourceBlocked(f"duplicate_global_timestamp {t}")
                prices[t]=op
            manifests.append({"date":ds,"archive":fn,"archive_sha256":actual,"checksum_object":fn+".CHECKSUM","status":"PASS","row_count":len(dayrows)})
    for y,m in months:
        a=max(dt.datetime(y,m,1,tzinfo=dt.timezone.utc),start)
        b=min(dt.datetime(y+1,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(y,m+1,1,tzinfo=dt.timezone.utc),end)
        t=ms(a)
        be=ms(b)
        while t<be:
            if t not in prices:
                missing_minutes+=1
            t+=60000
    return prices,{
        "symbol":SYMBOL,
        "timeframe":TIMEFRAME,
        "segments_months":[f"{y:04d}-{m:02d}" for y,m in sorted(months)],
        "archive_count":len(manifests),
        "archives":manifests,
        "expected_minutes":expected_minutes,
        "observed_minutes":len(prices),
        "missing_minutes":missing_minutes,
        "hard_end_exclusive":end.isoformat().replace("+00:00","Z")
    }

def reconcile_rest(prices:dict[int,Decimal], split:str):
    byyear=defaultdict(list)
    for t in prices:
        byyear[dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).year].append(t)
    results=[]
    for year,times in sorted(byyear.items()):
        ranked=sorted(times,key=lambda t: hashlib.sha256(f"{SYMBOL}|{year}|{t}|DLS_RECON_V0.1".encode()).hexdigest())[:5]
        for t in ranked:
            qs=urllib.parse.urlencode({"symbol":SYMBOL,"interval":"1m","startTime":t,"endTime":t+59999,"limit":1})
            obj,attempts=http_json_fallback("/api/v3/klines?"+qs)
            if not isinstance(obj,list) or len(obj)!=1:
                raise SourceBlocked(f"rest_reconcile_shape {year} {t}")
            row=obj[0]
            rt=int(row[0])
            ro=Decimal(str(row[1]))
            ao=prices[t]
            ok=(rt==t and ro==ao)
            results.append({
                "year":year,
                "timestamp_ms":t,
                "archive_open":str(ao),
                "rest_open":str(ro),
                "timestamp_match":rt==t,
                "open_decimal_match":ro==ao,
                "pass":ok,
                "transport_attempts":attempts
            })
            if not ok:
                raise SourceBlocked(f"MARKET_DATA_SOURCE_CONFLICT_FAIL_CLOSED {year} {t}")
    return results

def load_clusters(census_path:Path):
    all_target=[]
    with census_path.open("r",encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r=json.loads(line)
            if r.get("primary_market_identity")==TARGET and int(r.get("quiet_seconds") or 0)==60:
                all_target.append(r)
    return all_target

def has_near_event(candidate_ms:int,event_t0_ms:list[int])->bool:
    i=bisect.bisect_left(event_t0_ms,candidate_ms)
    for j in (i-1,i):
        if 0<=j<len(event_t0_ms) and abs(event_t0_ms[j]-candidate_ms)<=4*3600*1000:
            return True
    return False

def candidate_pools(prices, clusters, start, end):
    event_t0=sorted(ms(parse_iso(c["t0"])) for c in clusters)
    pools=defaultdict(list)
    hmax=max(HORIZONS_MIN)*60000
    for t in sorted(prices):
        d=dt.datetime.fromtimestamp(t/1000,dt.timezone.utc)
        if d<start or d>=end:
            continue
        if t+hmax>=ms(end):
            continue
        if any((t+h*60000) not in prices for h in HORIZONS_MIN):
            continue
        if has_near_event(t,event_t0):
            continue
        pools[(d.year,d.month,d.hour)].append(t)
    return pools,event_t0

def control_for(cluster,pools):
    t0=parse_iso(cluster["t0"])
    key=(t0.year,t0.month,t0.hour)
    candidates=pools.get(key,[])
    if not candidates:
        return None
    cid=cluster["cluster_id"]
    return min(candidates,key=lambda t:hashlib.sha256((cid+iso_ms(t)).encode("utf-8")).hexdigest())

def returns_at(prices,t):
    p0=prices[t]
    out={}
    if p0<=0:
        raise SourceBlocked(f"nonpositive_open {t}")
    for h in HORIZONS_MIN:
        ph=prices[t+h*60000]
        if ph<=0:
            raise SourceBlocked(f"nonpositive_horizon_open {t} h={h}")
        out[h]=math.log(float(ph/p0))
    return out

def quantile_linear(xs,p):
    ys=sorted(xs)
    pos=p*(len(ys)-1)
    lo=int(math.floor(pos))
    hi=int(math.ceil(pos))
    if lo==hi:
        return ys[lo]
    w=pos-lo
    return ys[lo]*(1-w)+ys[hi]*w

def bootstrap_stats(pairs,h,split):
    byday=defaultdict(lambda:[0.0,0])
    vals=[]
    for p in pairs:
        v=p["d"][str(h)]
        vals.append(v)
        day=p["event_day"]
        byday[day][0]+=v
        byday[day][1]+=1
    days=sorted(byday)
    observed=sum(vals)/len(vals)
    seed_text=LAB_ID+split+f"{h}m"+"V0.1"
    seed=int(hashlib.sha256(seed_text.encode()).hexdigest(),16)
    rng=random.Random(seed)
    boots=[]
    for _ in range(BOOTSTRAP_REPS):
        s=0.0
        n=0
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))]
            ds,dn=byday[d]
            s+=ds
            n+=dn
        boots.append(s/n)
    return {
        "mean":observed,
        "ci95_low":quantile_linear(boots,0.025),
        "ci95_high":quantile_linear(boots,0.975),
        "one_sided_bootstrap_p":(1+sum(1 for x in boots if x<=0.0))/(BOOTSTRAP_REPS+1),
        "bootstrap_reps":BOOTSTRAP_REPS,
        "block_day_count":len(days),
        "seed_text":seed_text,
        "seed_full_sha256_int":seed
    }

def holm(pvals:dict[str,float],alpha=.05):
    ordered=sorted(pvals.items(),key=lambda kv:(kv[1],kv[0]))
    rejected=[]
    steps=[]
    active=True
    m=len(ordered)
    for i,(name,p) in enumerate(ordered):
        threshold=alpha/(m-i)
        reject=active and p<=threshold
        steps.append({"horizon":name,"p":p,"threshold":threshold,"reject":reject})
        if reject:
            rejected.append(name)
        else:
            active=False
    return {"alpha":alpha,"method":"Holm-Bonferroni","steps":steps,"rejected":rejected}

def inferential_statuses(feas,split):
    allowed=set()
    for s in feas.get("post_mapping_subgroups") or []:
        st=s.get("post_mapping_status")
        if split=="discovery" and st=="INFERENTIAL_DISCOVERY_AND_OOS":
            allowed.add((s["protocol"],s["class"]))
        if split=="oos" and st in ("INFERENTIAL_DISCOVERY_AND_OOS","EXTERNAL_CONFIRMATORY_INFERENTIAL"):
            allowed.add((s["protocol"],s["class"]))
    return allowed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--split",choices=["discovery","oos"],required=True)
    ap.add_argument("--sample-gate",required=True)
    ap.add_argument("--final-authority",required=True)
    ap.add_argument("--market-data-authority",required=True)
    ap.add_argument("--registry",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--cache",default="market_cache")
    ap.add_argument("--discovery-receipt")
    args=ap.parse_args()

    sample_root=Path(args.sample_gate)
    auth_root=Path(args.final_authority)
    market_root=Path(args.market_data_authority)
    outdir=Path(args.outdir)
    outdir.mkdir(parents=True,exist_ok=True)

    sample,_=load_json_exact(sample_root,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json",EXPECTED_SAMPLE_RECEIPT_SHA256)
    census=find_one(sample_root,"SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson")
    if sha256_file(census)!=EXPECTED_CENSUS_SHA256:
        raise ContractError("cluster census sha mismatch")
    authority,_=load_json_exact(auth_root,"FINAL_PRE_DISCOVERY_AUTHORITY_RECEIPT_V0.1.json",EXPECTED_FINAL_AUTHORITY_RECEIPT_SHA256)
    feas,_=load_json_exact(market_root,"MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json",EXPECTED_FEASIBILITY_RECEIPT_SHA256)

    if sample.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
        raise ContractError("sample gate not pass")
    if authority.get("classification")!="FINAL_PRE_DISCOVERY_AUTHORITY_PASS":
        raise ContractError("final authority not pass")
    if feas.get("classification")!="MARKET_DATA_SOURCE_PASS":
        raise ContractError("market data authority not pass")
    if feas.get("mapping_registry_sha256")!=EXPECTED_MAPPING_REGISTRY_SHA256:
        raise ContractError("authority registry sha mismatch")

    regp=Path(args.registry)
    if sha256_file(regp)!=EXPECTED_MAPPING_REGISTRY_SHA256:
        raise ContractError(f"checked-out registry sha mismatch {sha256_file(regp)}")
    reg=json.loads(regp.read_text())
    rows=[x for x in reg.get("mappings",[]) if x.get("target_identity")==TARGET]
    if len(rows)!=1 or rows[0].get("status")!="BINANCE_DIRECT" or rows[0].get("symbol")!=SYMBOL:
        raise ContractError("frozen direct mapping mismatch")

    if args.split=="oos":
        if not args.discovery_receipt:
            raise ContractError("OOS requires discovery receipt")
        dr=json.loads(Path(args.discovery_receipt).read_text())
        if dr.get("classification")!="SURVIVES_DISCOVERY":
            raise ContractError("OOS forbidden unless SURVIVES_DISCOVERY")
        start,end=OOS_START,OOS_END
    else:
        start,end=DISCOVERY_START,DISCOVERY_END

    all_target=load_clusters(census)
    split_clusters=[c for c in all_target if c.get("split")==args.split]
    clusters=[]
    for c in split_clusters:
        t0=parse_iso(c["t0"])
        if start<=t0<end:
            clusters.append(c)
    if not clusters:
        raise SourceBlocked("no directly mapped clusters in split")

    event_months={(parse_iso(c["t0"]).year,parse_iso(c["t0"]).month) for c in clusters}
    data_months=set()
    cursor=dt.datetime(start.year,start.month,1,tzinfo=dt.timezone.utc)
    while cursor<end:
        data_months.add((cursor.year,cursor.month))
        cursor=(dt.datetime(cursor.year+1,1,1,tzinfo=dt.timezone.utc)
                if cursor.month==12 else dt.datetime(cursor.year,cursor.month+1,1,tzinfo=dt.timezone.utc))

    prices,manifest=download_market(data_months,start,end,Path(args.cache))
    manifest["event_months"]=[f"{y:04d}-{m:02d}" for y,m in sorted(event_months)]
    if prices and max(prices)>=ms(end):
        raise ContractError("split boundary market bar opened")
    if max(prices,default=0)>=ms(PROTECTED_START):
        raise ContractError("protected 2025+ market bar opened")
    manifest["rest_reconciliation"]=reconcile_rest(prices,args.split)

    pools,_=candidate_pools(prices,clusters,start,end)
    pairs=[]
    exclude=Counter()
    maxh=max(HORIZONS_MIN)*60000
    for c in clusters:
        a=ceil_minute_ms(parse_iso(c["t0"]))
        if a<ms(start) or a+maxh>=ms(end):
            exclude["event_boundary_or_horizon_outside_split"]+=1
            continue
        if a not in prices or any(a+h*60000 not in prices for h in HORIZONS_MIN):
            exclude["event_required_bar_missing"]+=1
            continue
        ctrl=control_for(c,pools)
        if ctrl is None:
            exclude["no_admissible_matched_control"]+=1
            continue
        er=returns_at(prices,a)
        cr=returns_at(prices,ctrl)
        d={str(h):abs(er[h])-abs(cr[h]) for h in HORIZONS_MIN}
        pairs.append({
            "cluster_id":c["cluster_id"],
            "protocol":c["protocol"],
            "instruction_class":c["instruction_class"],
            "event_day":parse_iso(c["t0"]).date().isoformat(),
            "t0":c["t0"],
            "event_aligned_open":iso_ms(a),
            "control_aligned_open":iso_ms(ctrl),
            "event_returns":{str(h):er[h] for h in HORIZONS_MIN},
            "control_returns":{str(h):cr[h] for h in HORIZONS_MIN},
            "d":d
        })

    expected=len(clusters)
    paired=len(pairs)
    aggregate_coverage=paired/expected if expected else 0.0
    inferential=inferential_statuses(feas,args.split)
    exp_sub=Counter((c["protocol"],c["instruction_class"]) for c in clusters if (c["protocol"],c["instruction_class"]) in inferential)
    got_sub=Counter((p["protocol"],p["instruction_class"]) for p in pairs if (p["protocol"],p["instruction_class"]) in inferential)
    subgroup_cov={
        f"{k[0]}::{k[1]}":{
            "expected":exp_sub[k],
            "paired":got_sub[k],
            "coverage":got_sub[k]/exp_sub[k] if exp_sub[k] else None
        }
        for k in sorted(exp_sub)
    }

    source_errors=[]
    if aggregate_coverage<0.95:
        source_errors.append({"reason":"aggregate_eligible_pair_coverage_below_95pct","coverage":aggregate_coverage})
    for k,v in subgroup_cov.items():
        if v["expected"] and v["coverage"]<0.90:
            source_errors.append({"reason":"inferential_subgroup_coverage_below_90pct","subgroup":k,"coverage":v["coverage"]})
    min_n=1000 if args.split=="discovery" else 500
    if paired<min_n:
        source_errors.append({"reason":"paired_cluster_count_below_frozen_gate","observed":paired,"required":min_n})

    manifest.update({
        "split":args.split,
        "archive_payload_downloaded":True,
        "candles_opened":True,
        "prices_opened":True,
        "source_mappable_clusters":expected,
        "paired_clusters":paired,
        "aggregate_eligible_pair_coverage":aggregate_coverage,
        "exclusions":dict(exclude),
        "inferential_subgroup_coverage":subgroup_cov,
        "max_loaded_bar_open":iso_ms(max(prices)) if prices else None,
        "protected_2025_2026_opened":False
    })
    (outdir/f"DLS_{args.split.upper()}_MARKET_DATA_ACQUISITION_MANIFEST_V0.1.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")

    rows_path=outdir/f"DLS_{args.split.upper()}_PAIRED_ROWS_V0.1.ndjson"
    with rows_path.open("w") as f:
        for p in pairs:
            f.write(canonical_json(p).decode()+"\n")

    if source_errors:
        receipt={
            "schema_version":SCHEMA_VERSION,
            "lab_id":LAB_ID,
            "split":args.split,
            "classification":"MARKET_DATA_SOURCE_BLOCKED",
            "source_errors":source_errors,
            "paired_n":paired,
            "aggregate_coverage":aggregate_coverage,
            "inferential_subgroup_coverage":subgroup_cov,
            "outcomes_opened":True,
            "protected_2025_2026_opened":False,
            "post_outcome_tuning":False
        }
    else:
        stats={str(h):bootstrap_stats(pairs,h,args.split) for h in HORIZONS_MIN}
        for h in HORIZONS_MIN:
            event_mean=sum(abs(p["event_returns"][str(h)]) for p in pairs)/paired
            control_mean=sum(abs(p["control_returns"][str(h)]) for p in pairs)/paired
            stats[str(h)].update({
                "event_abs_mean":event_mean,
                "control_abs_mean":control_mean,
                "relative_uplift":event_mean/control_mean-1 if control_mean>0 else None
            })

        family_means={}
        inferential_protocols=sorted({prot for prot,cls in inferential})
        for prot in inferential_protocols:
            sub=[p for p in pairs if p["protocol"]==prot and (p["protocol"],p["instruction_class"]) in inferential]
            if sub:
                family_means[prot]=sum(p["d"][str(PRIMARY_H)] for p in sub)/len(sub)
        positive_families=sum(1 for v in family_means.values() if v>0)

        secondary=[1,30,240]
        positive_secondary=sum(1 for h in secondary if stats[str(h)]["mean"]>0)
        holm_result=holm({f"{h}m":stats[str(h)]["one_sided_bootstrap_p"] for h in secondary})

        if args.split=="discovery":
            gates={
                "paired_n":paired>=1000,
                "mean_d5_positive":stats["5"]["mean"]>0,
                "ci95_d5_low_positive":stats["5"]["ci95_low"]>0,
                "relative_uplift_5m_ge_10pct":stats["5"]["relative_uplift"] is not None and stats["5"]["relative_uplift"]>=0.10,
                "two_inferential_protocol_families_positive":positive_families>=2,
                "two_secondary_horizons_positive":positive_secondary>=2,
                "one_secondary_survives_holm":len(holm_result["rejected"])>=1
            }
            classification="SURVIVES_DISCOVERY" if all(gates.values()) else "NO_EDGE_DISCOVERY"
        else:
            gates={
                "paired_n":paired>=500,
                "mean_d5_positive":stats["5"]["mean"]>0,
                "ci95_d5_low_positive":stats["5"]["ci95_low"]>0,
                "relative_uplift_5m_ge_10pct":stats["5"]["relative_uplift"] is not None and stats["5"]["relative_uplift"]>=0.10,
                "two_inferential_protocol_families_positive":positive_families>=2,
                "two_secondary_horizons_positive":positive_secondary>=2
            }
            classification="SURVIVES_OOS" if all(gates.values()) else "NO_EDGE_OOS"

        receipt={
            "schema_version":SCHEMA_VERSION,
            "lab_id":LAB_ID,
            "split":args.split,
            "classification":classification,
            "paired_n":paired,
            "aggregate_coverage":aggregate_coverage,
            "inferential_subgroup_coverage":subgroup_cov,
            "statistics":stats,
            "inferential_family_d5_means":family_means,
            "positive_inferential_family_count":positive_families,
            "positive_secondary_horizon_count":positive_secondary,
            "secondary_holm":holm_result,
            "gates":gates,
            "outcomes_opened":True,
            "protected_2025_2026_opened":False,
            "post_outcome_tuning":False
        }

    receipt.update({
        "authority":{
            "final_pre_discovery_receipt_sha256":EXPECTED_FINAL_AUTHORITY_RECEIPT_SHA256,
            "sample_gate_receipt_sha256":EXPECTED_SAMPLE_RECEIPT_SHA256,
            "cluster_census_sha256":EXPECTED_CENSUS_SHA256,
            "market_data_feasibility_receipt_sha256":EXPECTED_FEASIBILITY_RECEIPT_SHA256,
            "mapping_registry_sha256":EXPECTED_MAPPING_REGISTRY_SHA256
        },
        "frozen_horizons_minutes":HORIZONS_MIN,
        "primary_horizon_minutes":PRIMARY_H,
        "bootstrap_repetitions":BOOTSTRAP_REPS,
        "control_hash_serialization":"UTF8(cluster_id + candidate_UTC_YYYY-MM-DDTHH:MM:00Z)",
        "market_target":TARGET,
        "symbol":SYMBOL,
        "price_field":"1m OPEN",
        "firewall":{
            "live_trading":False,
            "orders":False,
            "wallets":False,
            "exchange_mutation":False,
            "merge_main":False,
            "protected_2025_2026_opened":False,
            "post_outcome_tuning":False
        }
    })

    outname=f"DLS_{args.split.upper()}_RECEIPT_V0.1.json"
    (outdir/outname).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":receipt["classification"],
        "split":args.split,
        "paired_n":paired,
        "aggregate_coverage":aggregate_coverage,
        "source_error_count":len(source_errors),
        "gates":receipt.get("gates")
    },indent=2,sort_keys=True))
    if receipt["classification"]=="MARKET_DATA_SOURCE_BLOCKED":
        raise SystemExit(2)

if __name__=="__main__":
    main()

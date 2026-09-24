#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, math, random, statistics, urllib.request, urllib.error, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL")
MAN=ROOT/"research/BINANCE_COLLATERAL_HAIRCUT_001_EVENT_MANIFEST_V0.1C.json"
OUT=ROOT/"runtime/binance_collateral_haircut_001/discovery_2024_receipt.json"
BASE="https://data.binance.vision/data/spot/daily/klines"
CACHE={}
PROV={}

def fetch_day(symbol, day):
    key=(symbol,day)
    if key in CACHE:return CACHE[key]
    url=f"{BASE}/{symbol}/5m/{symbol}-5m-{day}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-BCH-001/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
    except urllib.error.HTTPError as e:
        if e.code==404:
            CACHE[key]=None; return None
        raise
    sha=hashlib.sha256(raw).hexdigest()
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=z.namelist()[0]
        with io.TextIOWrapper(z.open(name),encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if not row or not row[0].isdigit(): continue
                rows.append({"open_ms":int(row[0]),"close":float(row[4]),"close_ms":int(row[6])})
    rows.sort(key=lambda x:x["close_ms"])
    PROV[url]={"sha256":sha,"rows":len(rows)}
    CACHE[key]=rows
    return rows

def daystr(dt): return dt.strftime("%Y-%m-%d")

def latest_close_before(symbol, target_dt):
    days=[target_dt.date()+timedelta(days=o) for o in (-1,0)]
    rows=[]
    for d in days:
        z=fetch_day(symbol,d.isoformat())
        if z: rows.extend(z)
    t=int(target_dt.timestamp()*1000)
    ok=[x for x in rows if x["close_ms"]<t]
    return ok[-1]["close"] if ok else None

def has_30d_history(symbol, effective):
    probe=(effective-timedelta(days=30)).date().isoformat()
    z=fetch_day(symbol,probe)
    return bool(z)

def bootstrap_cluster(events,reps=10000,seed=20261003):
    by=defaultdict(list)
    for e in events:by[e["cluster"]].append(e["signed_mar24"])
    clusters=sorted(by)
    rng=random.Random(seed); vals=[]
    for _ in range(reps):
        xs=[]
        for __ in clusters:
            c=clusters[rng.randrange(len(clusters))]
            xs.extend(by[c])
        vals.append(sum(xs)/len(xs))
    vals.sort()
    def q(p):
        k=(len(vals)-1)*p; f=math.floor(k); c=math.ceil(k)
        return vals[f] if f==c else vals[f]*(c-k)+vals[c]*(k-f)
    return [q(.025),q(.975)]

def sign_p(xs):
    nz=[x for x in xs if x!=0]
    n=len(nz); k=sum(x>0 for x in nz)
    if n==0:return None
    return sum(math.comb(n,j) for j in range(k,n+1))/(2**n)

def main():
    m=json.loads(MAN.read_text())
    analyzed=[];excluded=[]
    for e in m["events"]:
        symbol=e["asset"]+"USDT"
        eff=datetime.fromisoformat(e["effective_utc"].replace("Z","+00:00"))
        cluster=e["article_code"]+"@"+e["effective_utc"]
        if not has_30d_history(symbol,eff):
            excluded.append({"asset":e["asset"],"symbol":symbol,"cluster":cluster,"reason":"NO_SPOT_USDT_HISTORY_30D_BEFORE_EVENT"})
            continue
        try:
            a_pre=latest_close_before(symbol,eff-timedelta(hours=24))
            a_entry=latest_close_before(symbol,eff)
            a_4h=latest_close_before(symbol,eff+timedelta(hours=4))
            a_24h=latest_close_before(symbol,eff+timedelta(hours=24))
            b_pre=latest_close_before("BTCUSDT",eff-timedelta(hours=24))
            b_entry=latest_close_before("BTCUSDT",eff)
            b_4h=latest_close_before("BTCUSDT",eff+timedelta(hours=4))
            b_24h=latest_close_before("BTCUSDT",eff+timedelta(hours=24))
            vals=[a_pre,a_entry,a_4h,a_24h,b_pre,b_entry,b_4h,b_24h]
            if any(v is None or v<=0 for v in vals):
                excluded.append({"asset":e["asset"],"symbol":symbol,"cluster":cluster,"reason":"MISSING_REQUIRED_5M_BAR"})
                continue
            ar24=math.log(a_24h/a_entry); br24=math.log(b_24h/b_entry)
            ar4=math.log(a_4h/a_entry); br4=math.log(b_4h/b_entry)
            apre=math.log(a_entry/a_pre); bpre=math.log(b_entry/b_pre)
            mar24=ar24-br24; mar4=ar4-br4; pre_mar=apre-bpre
            sgn=1 if e["delta_pp"]>0 else -1
            analyzed.append({
              "asset":e["asset"],"symbol":symbol,"cluster":cluster,"article_code":e["article_code"],
              "effective_utc":e["effective_utc"],"before_pct":e["before_pct"],"after_pct":e["after_pct"],"delta_pp":e["delta_pp"],
              "shock_sign":sgn,"mar24":mar24,"signed_mar24":sgn*mar24,"mar4":mar4,"signed_mar4":sgn*mar4,"pre_mar24":pre_mar
            })
        except Exception as ex:
            excluded.append({"asset":e["asset"],"symbol":symbol,"cluster":cluster,"reason":"SOURCE_EXCEPTION","error_type":type(ex).__name__})

    n=len(analyzed); clusters=sorted({x["cluster"] for x in analyzed})
    tight=[x for x in analyzed if x["delta_pp"]<0]; loose=[x for x in analyzed if x["delta_pp"]>0]
    xs=[x["signed_mar24"] for x in analyzed]
    ci=bootstrap_cluster(analyzed) if analyzed else [None,None]
    p=sign_p(xs) if xs else None
    loo={}
    for c in clusters:
        ys=[x["signed_mar24"] for x in analyzed if x["cluster"]!=c]
        loo[c]=sum(ys)/len(ys) if ys else None
    enough=(n>=20 and len(clusters)>=4 and len(tight)>=5 and len(loose)>=5)
    mean_all=sum(xs)/n if n else None
    mean_t=sum(x["signed_mar24"] for x in tight)/len(tight) if tight else None
    mean_l=sum(x["signed_mar24"] for x in loose)/len(loose) if loose else None
    passed=bool(enough and mean_all>0 and ci[0]>0 and p is not None and p<0.05 and mean_t>0 and mean_l>0 and all(v is not None and v>0 for v in loo.values()))
    classification="DISCOVERY_MECHANISM_SURVIVES" if passed else ("DISCOVERY_INSUFFICIENT_SAMPLE" if not enough else "DISCOVERY_NO_SIGNAL")

    per_cluster={}
    for c in clusters:
        es=[x for x in analyzed if x["cluster"]==c]
        per_cluster[c]={"n":len(es),"mean_signed_mar24":sum(x["signed_mar24"] for x in es)/len(es),"positive_fraction":sum(x["signed_mar24"]>0 for x in es)/len(es)}
    bundle=hashlib.sha256("".join(PROV[k]["sha256"] for k in sorted(PROV)).encode()).hexdigest()

    receipt={
      "lab_id":"BINANCE-COLLATERAL-HAIRCUT-001",
      "scope":"2024_DISCOVERY_ONLY",
      "classification":classification,
      "sample":{"source_events":36,"analyzable_asset_events":n,"independent_clusters":len(clusters),"tightening_analyzable":len(tight),"loosening_analyzable":len(loose),"excluded":len(excluded)},
      "primary":{
        "mean_signed_mar24":mean_all,
        "median_signed_mar24":statistics.median(xs) if xs else None,
        "cluster_bootstrap95_mean_signed_mar24":ci,
        "positive_count":sum(x>0 for x in xs),
        "negative_count":sum(x<0 for x in xs),
        "one_sided_sign_test_p":p,
        "mean_signed_mar24_tightening":mean_t,
        "mean_signed_mar24_loosening":mean_l,
        "leave_one_cluster_out_means":loo
      },
      "diagnostics":{
        "mean_signed_mar4":sum(x["signed_mar4"] for x in analyzed)/n if n else None,
        "median_signed_mar4":statistics.median([x["signed_mar4"] for x in analyzed]) if analyzed else None,
        "mean_pre_mar24":sum(x["pre_mar24"] for x in analyzed)/n if n else None,
        "per_cluster":per_cluster
      },
      "events":analyzed,
      "exclusions":excluded,
      "source_bundle_sha256":bundle,
      "source_files":PROV,
      "safety":{"2025_opened":False,"2026_opened":False,"pnl_computed":False,"live_execution":False,"authenticated_api":False,"exchange_mutation":False,"merge_to_main":False}
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"classification":classification,"sample":receipt["sample"],"primary":receipt["primary"],"diagnostics":receipt["diagnostics"],"source_bundle_sha256":bundle},indent=2,allow_nan=False))
if __name__=="__main__":main()

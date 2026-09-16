#!/usr/bin/env python3
import csv, io, json, math, hashlib, random, statistics, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

LAB = "BTC-OPTIONS-VRP-001"
MVE = "OVRP-DVOL-RV30-001"
START = datetime(2021,4,1,tzinfo=timezone.utc)
END = datetime(2024,12,31,23,59,59,999000,tzinfo=timezone.utc)
EXPECTED_DVOL_SHA = "36a56f57411d187a97413f47a53cedb4afad7a0812a09f35d6a67483c6704cd7"
EXPECTED_BINANCE_MANIFEST_SHA = "a38782c5867d1b5dc538fe4b0a23f521775855e8dca4ff86679c241f0f7ddbbf"
OUT = Path("artifacts/btc_options_vrp_discovery_v01")
OUT.mkdir(parents=True, exist_ok=True)


def get_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent":"MSEL-Crypto-Lab/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ms(dt): return int(dt.timestamp()*1000)

def iso_date_from_ms(x): return datetime.fromtimestamp(int(x)/1000, tz=timezone.utc).date().isoformat()

def month_iter(y0,m0,y1,m1):
    y,m=y0,m0
    while (y,m) <= (y1,m1):
        yield y,m
        if m==12: y,m=y+1,1
        else: m+=1


def percentile(xs, p):
    ys=sorted(xs)
    if not ys: return float('nan')
    k=(len(ys)-1)*p
    lo=int(math.floor(k)); hi=int(math.ceil(k))
    if lo==hi: return ys[lo]
    w=k-lo
    return ys[lo]*(1-w)+ys[hi]*w


def mean(xs): return sum(xs)/len(xs)


def hac_ci_mean(xs, lag=5):
    n=len(xs); m=mean(xs)
    dev=[x-m for x in xs]
    gamma0=sum(d*d for d in dev)/n
    lrv=gamma0
    for l in range(1, lag+1):
        g=sum(dev[t]*dev[t-l] for t in range(l,n))/n
        w=1-l/(lag+1)
        lrv += 2*w*g
    lrv=max(lrv,0.0)
    se=math.sqrt(lrv/n)
    return m-1.96*se, m+1.96*se, se


def moving_block_bootstrap_ci(xs, block=5, reps=5000, seed=230911):
    rng=random.Random(seed); n=len(xs); starts=list(range(0,n-block+1)); means=[]
    for _ in range(reps):
        sample=[]
        while len(sample)<n:
            s=rng.choice(starts)
            sample.extend(xs[s:s+block])
        sample=sample[:n]
        means.append(mean(sample))
    return percentile(means,0.025), percentile(means,0.975)

result={
    "lab_id":LAB,"mve_id":MVE,"classification":None,
    "source_binding_pass":False,"access_2025":False,"access_2026":False,
    "strategy_pnl_opened":False,"directional_forward_returns_opened":False,
    "errors":[],"gates":{}
}

# ---- Rebind exact Deribit source before any BTC price outcome access ----
try:
    base="https://www.deribit.com/api/v2/public/get_volatility_index_data"
    cursor_end=ms(END); start_ms=ms(START); rows=[]; loops=0
    while True:
        loops+=1
        if loops>30: raise RuntimeError("Deribit pagination loop exceeded")
        q=urllib.parse.urlencode({"currency":"BTC","start_timestamp":start_ms,"end_timestamp":cursor_end,"resolution":"1D"})
        raw=get_bytes(base+"?"+q)
        obj=json.loads(raw.decode("utf-8"))
        if "error" in obj: raise RuntimeError(f"Deribit error: {obj['error']}")
        payload=obj.get("result",{}); data=payload.get("data",[]) or []; rows.extend(data)
        cont=payload.get("continuation")
        if cont is None: break
        cont=int(cont)
        if cont>=cursor_end: raise RuntimeError("Deribit continuation did not move backward")
        if cont<=start_ms: break
        cursor_end=cont
    norm={}
    for r in rows:
        if not isinstance(r,list) or len(r)!=5: raise RuntimeError("Unexpected Deribit candle shape")
        ts=int(r[0]); d=iso_date_from_ms(ts)
        if d >= "2025-01-01": result["access_2025"]=True; raise RuntimeError("Protected Deribit row")
        vals=[float(x) for x in r[1:]]
        if not all(math.isfinite(x) and x>0 for x in vals): raise RuntimeError("Invalid DVOL value")
        if ts in norm and norm[ts]!=vals: raise RuntimeError("Conflicting Deribit duplicate")
        norm[ts]=vals
    ledger=[]
    for ts,vals in sorted(norm.items()):
        d=iso_date_from_ms(ts)
        if "2021-04-01" <= d <= "2024-12-31":
            ledger.append({"timestamp_ms":ts,"utc_date":d,"open":vals[0],"high":vals[1],"low":vals[2],"close":vals[3]})
    b=("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in ledger)+"\n").encode()
    dvol_sha=hashlib.sha256(b).hexdigest()
    if dvol_sha != EXPECTED_DVOL_SHA: raise RuntimeError(f"DVOL binding mismatch {dvol_sha}")
    dvol_close={x["utc_date"]:float(x["close"]) for x in ledger}
except Exception as e:
    result["classification"]="SOURCE_BINDING_FAILURE"
    result["errors"].append("DERIBIT:"+repr(e))
    (OUT/"discovery_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0)

# ---- Rebind exact Binance timestamp manifest without reading prices ----
try:
    base="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/"
    manifest=[]; all_dates=[]; raw_months={}
    for y,m in month_iter(2021,4,2024,12):
        stem=f"BTCUSDT-1d-{y:04d}-{m:02d}.zip"; zurl=base+stem
        chk_raw=get_bytes(zurl+".CHECKSUM").decode("utf-8",errors="replace").strip()
        expected=chk_raw.split()[0].lower(); zraw=get_bytes(zurl); actual=hashlib.sha256(zraw).hexdigest()
        if actual!=expected: raise RuntimeError(f"Checksum mismatch {stem}")
        raw_months[stem]=zraw
        with zipfile.ZipFile(io.BytesIO(zraw)) as zf:
            names=zf.namelist()
            if len(names)!=1: raise RuntimeError(f"Unexpected members {stem}")
            text=zf.read(names[0]).decode("utf-8")
        dates=[]
        for row in csv.reader(io.StringIO(text)):
            if not row: continue
            d=iso_date_from_ms(int(row[0]))
            if d >= "2025-01-01": result["access_2025"]=True; raise RuntimeError("Protected Binance row")
            dates.append(d); all_dates.append(d)
        manifest.append({"file":stem,"archive_sha256":actual,"checksum_text_sha256":hashlib.sha256(chk_raw.encode()).hexdigest(),"rows":len(dates),"first_date":min(dates),"last_date":max(dates)})
    mb=("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in manifest)+"\n").encode()
    manifest_sha=hashlib.sha256(mb).hexdigest()
    if manifest_sha != EXPECTED_BINANCE_MANIFEST_SHA: raise RuntimeError(f"Binance manifest binding mismatch {manifest_sha}")
except Exception as e:
    result["classification"]="SOURCE_BINDING_FAILURE"
    result["errors"].append("BINANCE:"+repr(e))
    (OUT/"discovery_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0)

result["source_binding_pass"]=True

# ---- Only now open frozen 2021-2024 BTC closes ----
close_by_date={}
for stem,zraw in raw_months.items():
    with zipfile.ZipFile(io.BytesIO(zraw)) as zf:
        text=zf.read(zf.namelist()[0]).decode("utf-8")
    for row in csv.reader(io.StringIO(text)):
        if not row: continue
        d=iso_date_from_ms(int(row[0])); c=float(row[4])
        if d >= "2025-01-01": result["access_2025"]=True; raise RuntimeError("Protected price row")
        if not (math.isfinite(c) and c>0): raise RuntimeError(f"Invalid close {d}")
        close_by_date[d]=c

# ---- Frozen weekly schedule / future RV30 ----
obs=[]; t=date(2021,4,1); end_date=date(2024,12,31)
while t + timedelta(days=30) <= end_date:
    ds=t.isoformat()
    if ds not in dvol_close: raise RuntimeError(f"Missing DVOL signal date {ds}")
    needed=[(t+timedelta(days=i)).isoformat() for i in range(0,31)]
    if any(d not in close_by_date for d in needed): raise RuntimeError(f"Missing BTC close window {ds}")
    sumsq=0.0
    for i in range(1,31):
        r=math.log(close_by_date[needed[i]]/close_by_date[needed[i-1]])
        sumsq += r*r
    rv30=100.0*math.sqrt((365.0/30.0)*sumsq)
    iv30=dvol_close[ds]
    vrp=iv30*iv30-rv30*rv30
    gap=iv30-rv30
    obs.append({"date":ds,"year":t.year,"iv30":iv30,"rv30":rv30,"vrp":vrp,"vol_gap":gap})
    t += timedelta(days=7)

vrps=[x["vrp"] for x in obs]; gaps=[x["vol_gap"] for x in obs]
n=len(obs); m=mean(vrps); med=statistics.median(vrps); pos=sum(1 for x in vrps if x>0)/n
hac_lo,hac_hi,hac_se=hac_ci_mean(vrps,5)
boot_lo,boot_hi=moving_block_bootstrap_ci(vrps,5,5000,230911)
year_means={str(y):mean([x["vrp"] for x in obs if x["year"]==y]) for y in (2021,2022,2023,2024)}
nonneg_years=sum(1 for v in year_means.values() if v>=0)

result.update({
    "n":n,"mean_vrp":m,"median_vrp":med,"positive_fraction":pos,
    "mean_vol_gap":mean(gaps),"hac_lag":5,"hac_se":hac_se,"hac_95_ci":[hac_lo,hac_hi],
    "bootstrap":{"replications":5000,"block_observations":5,"seed":230911,"ci_95":[boot_lo,boot_hi]},
    "calendar_year_mean_vrp":year_means,"nonnegative_year_count":nonneg_years,
    "first_observation":obs[0]["date"],"last_observation":obs[-1]["date"]
})

gates={
    "n_gte_190":n>=190,
    "mean_vrp_gt_0":m>0,
    "median_vrp_gt_0":med>0,
    "positive_fraction_gte_055":pos>=0.55,
    "hac_lower_gt_0":hac_lo>0,
    "bootstrap_lower_gt_0":boot_lo>0,
    "nonnegative_years_gte_3":nonneg_years>=3,
    "year_2023_nonnegative":year_means["2023"]>=0,
    "year_2024_nonnegative":year_means["2024"]>=0,
    "source_binding":result["source_binding_pass"],
    "protected_period_clean":not result["access_2025"] and not result["access_2026"]
}
result["gates"]=gates
if result["access_2025"] or result["access_2026"]:
    result["classification"]="PROVENANCE_FAILURE"
elif all(gates.values()):
    result["classification"]="DISCOVERY_PASS_VRP_EXISTS"
    result["strategy_status"]="STRATEGY_NOT_YET_AUTHORIZED"
else:
    result["classification"]="DISCOVERY_FAIL_NO_PROMOTION"

(OUT/"observations.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in obs)+"\n")
(OUT/"discovery_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))

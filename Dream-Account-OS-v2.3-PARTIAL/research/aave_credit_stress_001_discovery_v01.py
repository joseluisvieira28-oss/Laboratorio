#!/usr/bin/env python3
import csv, hashlib, io, json, math, random, statistics, sys, urllib.request, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/research")
AUTH=json.loads((ROOT/"AAVE_CREDIT_STRESS_001_DISCOVERY_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/aave_credit_stress_discovery_v01"); OUT.mkdir(parents=True,exist_ok=True)
DV="https://data.binance.vision"
START=date(2023,1,1); END=date(2024,12,31)
LAST_T=date(2024,12,30)
SCALE=int(AUTH["predictor"]["positive_scale_divisor"])

def sha(b): return hashlib.sha256(b).hexdigest()

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"AAVE-CREDIT-STRESS-001/discovery-v0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read()

def month_iter():
    y,m=2023,1
    while (y,m)<=(2024,12):
        yield y,m
        m+=1
        if m==13:y+=1;m=1

def parse_checksum(raw,filename):
    p=raw.decode("utf-8","replace").strip().split()
    if len(p)<1 or len(p[0])!=64: raise RuntimeError("BAD_CHECKSUM")
    if len(p)>=2 and p[-1].lstrip("*")!=filename: raise RuntimeError("CHECKSUM_FILENAME_MISMATCH")
    return p[0].lower()

def load_btc():
    closes={}; receipts=[]
    for y,m in month_iter():
        ym=f"{y:04d}-{m:02d}"; fn=f"BTCUSDT-1d-{ym}.zip"
        path=f"data/spot/monthly/klines/BTCUSDT/1d/{fn}"
        c=get(f"{DV}/{path}.CHECKSUM"); expected=parse_checksum(c,fn)
        z=get(f"{DV}/{path}"); actual=sha(z)
        if actual!=expected: raise RuntimeError(f"BINANCE_SHA_MISMATCH:{ym}")
        receipts.append({"path":path,"sha256":actual})
        with zipfile.ZipFile(io.BytesIO(z)) as zz:
            if zz.testzip() is not None: raise RuntimeError(f"BINANCE_ZIP_CRC:{ym}")
            names=[n for n in zz.namelist() if not n.endswith("/")]
            if len(names)!=1: raise RuntimeError(f"BINANCE_MEMBER_COUNT:{ym}")
            with zz.open(names[0]) as f:
                text=io.TextIOWrapper(f,encoding="utf-8-sig",errors="strict",newline="")
                for row in csv.reader(text):
                    if not row: continue
                    if str(row[0]).lower() in ("open_time","opentime"): continue
                    if len(row)<5: raise RuntimeError(f"BINANCE_ROW_SHORT:{ym}")
                    n=int(row[0]); sec=n/1_000_000 if n>10**14 else n/1000 if n>10**11 else n
                    d=datetime.fromtimestamp(sec,tz=timezone.utc).date()
                    if START<=d<=END:
                        close=float(row[4])
                        if not math.isfinite(close) or close<=0: raise RuntimeError(f"BAD_BTC_CLOSE:{d}")
                        if d in closes: raise RuntimeError(f"DUP_BTC_DATE:{d}")
                        closes[d]=close
    expected=(END-START).days+1
    if len(closes)!=expected: raise RuntimeError(f"BTC_DATE_COVERAGE:{len(closes)}!={expected}")
    d=START
    while d<=END:
        if d not in closes: raise RuntimeError(f"BTC_DATE_MISSING:{d}")
        d+=timedelta(days=1)
    return closes,receipts

def load_decode():
    files=list(Path("artifacts/decode_parent").rglob("aggregate.json"))
    if len(files)!=1: raise RuntimeError(f"DECODE_AGGREGATE_COUNT:{len(files)}")
    obj=json.loads(files[0].read_text())
    p=AUTH["parent_decode"]
    if obj.get("classification")!="DECODE_DAILY_SERIES_PASS": raise RuntimeError("PARENT_DECODE_NOT_PASS")
    if obj.get("structural_sha256")!=p["structural_sha256"]: raise RuntimeError("PARENT_STRUCTURAL_SHA_MISMATCH")
    if obj.get("daily_rows")!=p["daily_rows"]: raise RuntimeError("PARENT_DAILY_ROWS_MISMATCH")
    rows=obj.get("daily_series") or []
    if len(rows)!=p["daily_rows"]: raise RuntimeError("PARENT_DAILY_SERIES_LENGTH")
    rates={}
    for x in rows:
        d=date.fromisoformat(x["date"]); raw=int(x["raw_variable_borrow_rate_ray"])
        if d in rates: raise RuntimeError(f"DUP_RATE_DATE:{d}")
        rates[d]=raw
    return rates,sha(files[0].read_bytes())

def slope(rows):
    n=len(rows)
    if n<3: return None
    mx=sum(r["x"] for r in rows)/n; my=sum(r["y"] for r in rows)/n
    sxx=sum((r["x"]-mx)**2 for r in rows)
    if sxx<=0:return None
    return sum((r["x"]-mx)*(r["y"]-my) for r in rows)/sxx

def ols(rows):
    b=slope(rows)
    if b is None: raise RuntimeError("ZERO_X_VARIANCE")
    mx=sum(r["x"] for r in rows)/len(rows); my=sum(r["y"] for r in rows)/len(rows)
    a=my-b*mx
    return a,b

def hac_slope_se(rows,lag):
    n=len(rows); a,b=ols(rows)
    xs=[[1.0,r["x"]] for r in rows]
    u=[r["y"]-(a+b*r["x"]) for r in rows]
    s00=s01=s10=s11=0.0
    for t in range(n):
        z0,z1=xs[t]; e=u[t]
        s00+=e*e*z0*z0; s01+=e*e*z0*z1; s10+=e*e*z1*z0; s11+=e*e*z1*z1
    for L in range(1,min(lag,n-1)+1):
        w=1.0-L/(lag+1.0)
        for t in range(L,n):
            e=u[t]*u[t-L]
            a0,a1=xs[t]; b0,b1=xs[t-L]
            s00+=w*e*(a0*b0+b0*a0)
            s01+=w*e*(a0*b1+b0*a1)
            s10+=w*e*(a1*b0+b1*a0)
            s11+=w*e*(a1*b1+b1*a1)
    sx=sum(r["x"] for r in rows); sxx=sum(r["x"]**2 for r in rows)
    det=n*sxx-sx*sx
    if det<=0: raise RuntimeError("SINGULAR_XTX")
    i00=sxx/det; i01=-sx/det; i10=-sx/det; i11=n/det
    # V = inv * S * inv
    a00=i00*s00+i01*s10; a01=i00*s01+i01*s11
    a10=i10*s00+i11*s10; a11=i10*s01+i11*s11
    v11=a10*i01+a11*i11
    if v11<=0 or not math.isfinite(v11): raise RuntimeError("BAD_HAC_VARIANCE")
    return math.sqrt(v11)

def bootstrap(rows,reps,seed):
    groups=defaultdict(list)
    for r in rows:
        iso=r["date"].isocalendar()
        groups[(iso.year,iso.week)].append(r)
    keys=sorted(groups); rng=random.Random(seed); vals=[]; attempts=0
    while len(vals)<reps and attempts<reps*2:
        attempts+=1
        sample=[]
        for _ in range(len(keys)):
            sample.extend(groups[keys[rng.randrange(len(keys))]])
        b=slope(sample)
        if b is not None and math.isfinite(b): vals.append(b)
    if len(vals)!=reps: raise RuntimeError(f"BOOTSTRAP_VALID:{len(vals)}")
    vals.sort()
    def q(p):
        pos=(len(vals)-1)*p; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
        if lo==hi:return vals[lo]
        w=pos-lo; return vals[lo]*(1-w)+vals[hi]*w
    return {
      "replications":reps,
      "fraction_beta_ge_zero":sum(1 for v in vals if v>=0)/len(vals),
      "p2_5":q(0.025),"p50":q(0.5),"p95":q(0.95),"p97_5":q(0.975),
      "unique_week_blocks":len(keys)
    }

result={"lab_id":AUTH["lab_id"],"discovery_id":AUTH["discovery_id"],"classification":None,
        "access_2025":False,"access_2026":False,"strategy_pnl":False,"live_trading":False,
        "exchange_mutation":False,"wallet_access":False,"merge_to_main":False}
try:
    rates,parent_sha=load_decode()
    btc,btc_receipts=load_btc()
    rows=[]; d=min(rates)
    while d<=LAST_T:
        prev=d-timedelta(days=1); nxt=d+timedelta(days=1)
        if d in rates and prev in rates and d in btc and nxt in btc:
            x=(rates[d]-rates[prev])/SCALE
            y=math.log(btc[nxt]/btc[d])
            rows.append({"date":d,"x":x,"y":y})
        d+=timedelta(days=1)
    nz=sum(1 for r in rows if r["x"]!=0)
    weeks=len({(r["date"].isocalendar().year,r["date"].isocalendar().week) for r in rows})
    years={r["date"].year for r in rows}
    sg=AUTH["sample_gates"]
    sample_checks={
      "minimum_regression_rows":len(rows)>=sg["minimum_regression_rows"],
      "minimum_nonzero_predictor_rows":nz>=sg["minimum_nonzero_predictor_rows"],
      "minimum_unique_utc_weeks":weeks>=sg["minimum_unique_utc_weeks"],
      "both_calendar_years_present":years=={2023,2024}
    }
    if not all(sample_checks.values()):
        cls=AUTH["classifications"]["insufficient"]; metrics={}
        gates={}
    else:
        alpha,beta=ols(rows)
        boot=bootstrap(rows,AUTH["inference"]["bootstrap_replications"],AUTH["inference"]["bootstrap_seed"])
        se=hac_slope_se(rows,AUTH["inference"]["hac_lag_days"])
        t=beta/se
        p_one=0.5*(1.0+math.erf(t/math.sqrt(2.0)))
        b23=slope([r for r in rows if r["date"].year==2023])
        b24=slope([r for r in rows if r["date"].year==2024])
        metrics={
          "n":len(rows),"nonzero_predictor_rows":nz,"unique_utc_weeks":weeks,
          "alpha":alpha,"beta":beta,
          "beta_interpretation":"BTC next-day log-return change per +1 percentage-point daily change in Aave USDC variable borrow rate",
          "bootstrap":boot,
          "hac_lag_days":AUTH["inference"]["hac_lag_days"],"hac_slope_se":se,"hac_t_stat":t,"hac_one_sided_p_beta_lt_zero":p_one,
          "beta_2023":b23,"beta_2024":b24,
          "predictor_mean":statistics.fmean(r["x"] for r in rows),
          "predictor_stdev":statistics.stdev(r["x"] for r in rows),
          "btc_outcome_mean_log_return":statistics.fmean(r["y"] for r in rows),
          "parent_decode_aggregate_sha256":parent_sha,
          "binance_archive_months":len(btc_receipts),
          "binance_receipts_sha256":sha(json.dumps(btc_receipts,sort_keys=True).encode())
        }
        gates={
          "sample_gates_all_pass":all(sample_checks.values()),
          "full_sample_beta_lt_zero":beta<0,
          "bootstrap_fraction_beta_ge_zero_lt_0_05":boot["fraction_beta_ge_zero"]<0.05,
          "bootstrap_95th_beta_lt_zero":boot["p95"]<0,
          "hac_one_sided_p_lt_0_05":p_one<0.05,
          "beta_2023_lt_zero":b23 is not None and b23<0,
          "beta_2024_lt_zero":b24 is not None and b24<0
        }
        cls=AUTH["classifications"]["pass"] if all(gates.values()) else AUTH["classifications"]["no_edge"]
    result.update({"classification":cls,"sample_checks":sample_checks,"discovery_gates":gates,"metrics":metrics})
except Exception as e:
    txt=repr(e)
    result["classification"]=AUTH["classifications"]["provenance_failure"] if ("PARENT_" in txt or "PROTECTED" in txt) else AUTH["classifications"]["technical_failure"]
    result["error"]=txt

p=OUT/"discovery_result.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
manifest={"authority_sha256":sha((ROOT/"AAVE_CREDIT_STRESS_001_DISCOVERY_AUTHORITY_V0.1.json").read_bytes()),
          "result_sha256":sha(p.read_bytes())}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
sys.exit(0 if result["classification"] not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2)

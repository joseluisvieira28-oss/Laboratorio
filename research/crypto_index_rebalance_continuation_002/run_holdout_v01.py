#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,shutil,tempfile,time,urllib.request,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

LAB_ID="CRYPTO-INDEX-REBALANCE-CONTINUATION-002"
BASE_URL="https://data.binance.vision/data/futures/um/daily/klines"
UA="CryptoLab-CIRC002-Holdout/0.1"
OUT=Path("artifacts/crypto_index_rebalance_continuation_002")
BASE_COST=30.0
STRESS_COST=50.0
BOOT_N=10000
BOOT_SEED=20261001

def normalize_ms(v):
    x=int(float(v));a=abs(x)
    if a<10**11:return x*1000
    if a<10**14:return x
    if a<10**17:return x//1000
    return x//1_000_000

def iso_ms(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()

def fetch(url,path):
    last=None
    for n in range(5):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=60) as r,open(path,"wb") as w:
                shutil.copyfileobj(r,w,1024*1024)
            return
        except Exception as e:
            last=e;time.sleep(min(2**n,8))
    raise RuntimeError(f"download failed {url}: {last}")

def load_opens(symbol,date,tmp,provenance):
    name=f"{symbol}-1m-{date}.zip";url=f"{BASE_URL}/{symbol}/1m/{name}"
    z=tmp/name;c=tmp/(name+".CHECKSUM")
    fetch(url,z);fetch(url+".CHECKSUM",c)
    expected=c.read_text().strip().split()[0].lower();actual=sha256_file(z)
    if expected!=actual:raise RuntimeError(f"checksum mismatch {symbol} {date}")
    provenance.append({"symbol":symbol,"date":date,"url":url,"zip_sha256":actual})
    out={}
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError(f"unexpected archive members {symbol} {date}")
        with zz.open(names[0],"r") as raw:
            rd=csv.reader((line.decode("utf-8") for line in raw))
            for row in rd:
                if not row or not str(row[0]).strip().lstrip("-").isdigit():continue
                t=normalize_ms(row[0]);out[t]=float(row[1])
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    return out

def median(v):
    a=sorted(v);n=len(a)
    if not n:return math.nan
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def q(a,p):
    x=(len(a)-1)*p;lo=int(math.floor(x));hi=int(math.ceil(x))
    if lo==hi:return a[lo]
    w=x-lo
    return a[lo]*(1-w)+a[hi]*w

def bootstrap_month_mean(month_values):
    rng=random.Random(BOOT_SEED);vals=list(month_values);n=len(vals);res=[]
    for _ in range(BOOT_N):
        s=[vals[rng.randrange(n)] for __ in range(n)]
        res.append(sum(s)/n)
    res.sort();return [q(res,.025),q(res,.975)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source",required=True);ap.add_argument("--route",required=True);a=ap.parse_args()
    src=json.loads(Path(a.source).read_text());route=json.loads(Path(a.route).read_text())
    assert src["lab_id"]==LAB_ID and src["classification"]=="SOURCE_CENSUS_PASS"
    assert route["lab_id"]==LAB_ID and route["classification"]=="ROUTE_FEASIBILITY_PASS"
    assert route["route_identity_sha256"]=="a5411273d65be311d40fea168f3b616375cb41f23cf4322f353abffdef7216f0"
    srcmap={(x["month_key"],x["ticker"],x["direction"]):x for x in src["events"]}
    elig=[x for x in route["rows"] if x["primary_confirmatory_eligible"]]
    assert len(elig)==32
    events=[];rejected=[];provenance=[];cache={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for r in elig:
            key=(r["month_key"],r["ticker"],r["direction"]);s=srcmap[key]
            date=r["implementation_date"]
            entry=iso_ms(date+"T06:00:00Z")
            exit_=iso_ms(s["implementation_timestamp_utc"])
            if not entry<exit_:raise RuntimeError(f"nonpositive window {key}")
            tok=r["token_symbol"];btc="BTCUSDT"
            for sym in (tok,btc):
                ck=(sym,date)
                if ck not in cache:cache[ck]=load_opens(sym,date,tmp,provenance)
            missing=[]
            for label,series in (("token",cache[(tok,date)]),("btc",cache[(btc,date)])):
                for tname,tv in (("entry",entry),("exit",exit_)):
                    if tv not in series:missing.append(f"{label}_{tname}")
            if missing:
                rejected.append({"month_key":r["month_key"],"ticker":r["ticker"],"direction":r["direction"],"reason":"MISSING_EXACT_BOUNDARY","missing":missing})
                continue
            te=cache[(tok,date)][entry];tx=cache[(tok,date)][exit_]
            be=cache[(btc,date)][entry];bx=cache[(btc,date)][exit_]
            if min(te,tx,be,bx)<=0:raise RuntimeError(f"nonpositive price {key}")
            sign=1 if r["direction"]=="ADD" else -1
            token_ret=math.log(tx/te);btc_ret=math.log(bx/be)
            gross=sign*(token_ret-btc_ret)*10000.0
            events.append({
              "month_key":r["month_key"],"ticker":r["ticker"],"direction":r["direction"],
              "implementation_date":date,
              "entry_timestamp_utc":datetime.fromtimestamp(entry/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
              "exit_timestamp_utc":s["implementation_timestamp_utc"],
              "token_symbol":tok,"btc_symbol":btc,
              "token_entry":te,"token_exit":tx,"btc_entry":be,"btc_exit":bx,
              "token_log_return":token_ret,"btc_log_return":btc_ret,
              "gross_signed_bps":gross,"fee_floor_net_bps":gross-20.0,
              "base_net_bps":gross-BASE_COST,"stress_net_bps":gross-STRESS_COST,
              "trading_authority":"NONE"
            })
    month_groups=defaultdict(list)
    for x in events:month_groups[x["month_key"]].append(x)
    month_rows=[]
    for m in sorted(month_groups):
        xs=month_groups[m]
        month_rows.append({"month_key":m,"year":int(m[:4]),"n_legs":len(xs),
          "mean_gross_bps":sum(x["gross_signed_bps"] for x in xs)/len(xs),
          "mean_base_net_bps":sum(x["base_net_bps"] for x in xs)/len(xs),
          "mean_stress_net_bps":sum(x["stress_net_bps"] for x in xs)/len(xs)})
    dirs=Counter(x["direction"] for x in events);years=sorted({int(x["month_key"][:4]) for x in events})
    data_gates={
      "min_24_valid_legs":len(events)>=24,
      "min_5_valid_months":len(month_rows)>=5,
      "both_directions":dirs["ADD"]>0 and dirs["REMOVE"]>0,
      "both_2025_2026":years==[2025,2026],
      "min_2_legs_every_month":bool(month_rows) and min(x["n_legs"] for x in month_rows)>=2,
      "zero_source_conflicts":not src["contradictions"]
    }
    report={"lab_id":LAB_ID,"phase":"CONFIRMATORY_HOLDOUT_2025_2026_JUL",
      "valid_legs":len(events),"rejected_legs":len(rejected),"valid_months":len(month_rows),
      "direction_counts":dict(dirs),"years":years,"month_rows":month_rows,
      "data_gates":data_gates,"costs_bps":{"fee_floor":20,"base":30,"stress":50},
      "route_identity_sha256":route["route_identity_sha256"],"trading_authority":"NONE"}
    if not all(data_gates.values()):
        report["classification"]="HOLDOUT_DATA_INSUFFICIENT"
    else:
        gross=[x["gross_signed_bps"] for x in events]
        add=[x["gross_signed_bps"] for x in events if x["direction"]=="ADD"]
        rem=[x["gross_signed_bps"] for x in events if x["direction"]=="REMOVE"]
        mv=[x["mean_gross_bps"] for x in month_rows]
        boot=bootstrap_month_mean(mv)
        lomo=[]
        for i,m in enumerate(month_rows):
            other=[x["mean_gross_bps"] for j,x in enumerate(month_rows) if j!=i]
            lomo.append({"omitted":m["month_key"],"mean_other_gross_bps":sum(other)/len(other)})
        lomo_frac=sum(x["mean_other_gross_bps"]>0 for x in lomo)/len(lomo)
        year_means={}
        for y in years:
            v=[x["mean_gross_bps"] for x in month_rows if x["year"]==y]
            year_means[str(y)]=sum(v)/len(v)
        sumabs=sum(abs(x["mean_gross_bps"]) for x in month_rows)
        concentration=max(abs(x["mean_gross_bps"]) for x in month_rows)/sumabs if sumabs else 1.0
        metrics={
          "mean_month_gross_bps":sum(mv)/len(mv),
          "median_month_gross_bps":median(mv),
          "bootstrap95_mean_month_gross_bps":boot,
          "positive_gross_months":sum(x>0 for x in mv),
          "lomo_positive_fraction":lomo_frac,
          "lomo":lomo,
          "mean_add_gross_bps":sum(add)/len(add),
          "mean_remove_gross_bps":sum(rem)/len(rem),
          "mean_leg_gross_bps":sum(gross)/len(gross),
          "mean_leg_base_net_bps":sum(x["base_net_bps"] for x in events)/len(events),
          "mean_leg_stress_net_bps":sum(x["stress_net_bps"] for x in events)/len(events),
          "positive_stress_months":sum(x["mean_stress_net_bps"]>0 for x in month_rows),
          "year_mean_month_gross_bps":year_means,
          "max_abs_month_contribution":concentration
        }
        gates={
          "A_mean_month_gross_ge_50":metrics["mean_month_gross_bps"]>=50,
          "B_bootstrap_lower_gt_0":boot[0]>0,
          "C_median_month_gross_gt_0":metrics["median_month_gross_bps"]>0,
          "D_positive_gross_months_ge_4":metrics["positive_gross_months"]>=4,
          "E_lomo_positive_ge_80pct":lomo_frac>=0.8,
          "F_add_and_remove_mean_positive":metrics["mean_add_gross_bps"]>0 and metrics["mean_remove_gross_bps"]>0,
          "G_mean_base_net_positive":metrics["mean_leg_base_net_bps"]>0,
          "H_mean_stress_net_positive":metrics["mean_leg_stress_net_bps"]>0,
          "I_positive_stress_months_ge_3":metrics["positive_stress_months"]>=3,
          "J_both_year_means_positive":all(v>0 for v in year_means.values()),
          "K_month_concentration_le_40pct":concentration<=0.40
        }
        gross_keys=["A_mean_month_gross_ge_50","B_bootstrap_lower_gt_0","C_median_month_gross_gt_0","D_positive_gross_months_ge_4","E_lomo_positive_ge_80pct","F_add_and_remove_mean_positive","J_both_year_means_positive","K_month_concentration_le_40pct"]
        econ_keys=["G_mean_base_net_positive","H_mean_stress_net_positive","I_positive_stress_months_ge_3"]
        if all(gates.values()):cl="HOLDOUT_CONTINUATION_SURVIVES"
        elif all(gates[k] for k in gross_keys) and not all(gates[k] for k in econ_keys):cl="HOLDOUT_MECHANISM_ONLY_COST_BLOCKED"
        else:cl="HOLDOUT_CONTINUATION_FAILED"
        report.update({"classification":cl,"metrics":metrics,"survival_gates":gates})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"HOLDOUT_REPORT_V0.1.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
    (OUT/"HOLDOUT_REJECTED_V0.1.json").write_text(json.dumps(rejected,indent=2,sort_keys=True))
    (OUT/"HOLDOUT_PROVENANCE_V0.1.json").write_text(json.dumps(provenance,indent=2,sort_keys=True))
    fields=["month_key","ticker","direction","implementation_date","entry_timestamp_utc","exit_timestamp_utc",
      "token_symbol","btc_symbol","token_entry","token_exit","btc_entry","btc_exit","token_log_return","btc_log_return",
      "gross_signed_bps","fee_floor_net_bps","base_net_bps","stress_net_bps","trading_authority"]
    with (OUT/"HOLDOUT_EVENTS_V0.1.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(events)
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()

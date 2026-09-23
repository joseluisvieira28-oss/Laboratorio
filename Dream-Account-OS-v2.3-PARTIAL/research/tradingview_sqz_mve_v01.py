#!/usr/bin/env python3
import csv, io, json, math, random, statistics, hashlib, urllib.request, zipfile
from pathlib import Path

SYMBOLS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
YEARS = [2022, 2023]
MONTHS = range(1,13)
BB_LEN=20; BB_MULT=2.0; KC_LEN=20; KC_MULT=1.5
COST_BPS=10.0
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/tvsqz001_discovery_receipt.json")

def mean(xs): return sum(xs)/len(xs) if xs else float("nan")
def popstd(xs):
    m=mean(xs)
    return math.sqrt(sum((x-m)**2 for x in xs)/len(xs))
def percentile(xs,p):
    if not xs: return float("nan")
    ys=sorted(xs); k=(len(ys)-1)*p; f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)
def bootstrap_ci(xs, stat_fn, reps, seed):
    rng=random.Random(seed); n=len(xs); vals=[]
    for _ in range(reps):
        vals.append(stat_fn([xs[rng.randrange(n)] for __ in range(n)]))
    return [percentile(vals,.025), percentile(vals,.975)]
def linreg_last(xs):
    n=len(xs); sx=n*(n-1)/2; sxx=(n-1)*n*(2*n-1)/6
    sy=sum(xs); sxy=sum(i*y for i,y in enumerate(xs))
    den=n*sxx-sx*sx
    slope=(n*sxy-sx*sy)/den if den else 0.0
    intercept=(sy-slope*sx)/n
    return intercept+slope*(n-1)
def fetch_month(symbol,year,month):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1h/{symbol}-1h-{year}-{month:02d}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-TVSQZ-001/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    h=hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=z.namelist()[0]
        txt=io.TextIOWrapper(z.open(name),encoding="utf-8")
        rows=[]
        for row in csv.reader(txt):
            if not row or not row[0].isdigit(): continue
            rows.append({
                "t":int(row[0]),"o":float(row[1]),"h":float(row[2]),"l":float(row[3]),"c":float(row[4]),"v":float(row[5])
            })
    return rows, {"url":url,"sha256":h,"rows":len(rows)}
def load_symbol(symbol):
    allr=[]; prov=[]
    for y in YEARS:
        for m in MONTHS:
            rows,p=fetch_month(symbol,y,m); allr.extend(rows); prov.append(p)
    allr.sort(key=lambda x:x["t"])
    ded=[]; last=None
    for r in allr:
        if r["t"]!=last: ded.append(r); last=r["t"]
    return ded,prov
def compute_events(rows):
    n=len(rows); closes=[r["c"] for r in rows]; highs=[r["h"] for r in rows]; lows=[r["l"] for r in rows]
    sq=[False]*n; off=[False]*n; mom=[None]*n; lrets=[None]*n
    for i in range(1,n):
        lrets[i]=math.log(closes[i]/closes[i-1])
    for i in range(max(BB_LEN,KC_LEN)-1,n):
        cw=closes[i-BB_LEN+1:i+1]
        basis=mean(cw); dev=BB_MULT*popstd(cw)
        upperBB=basis+dev; lowerBB=basis-dev
        tr=[]
        for j in range(i-KC_LEN+1,i+1):
            prev=closes[j-1] if j>0 else closes[j]
            tr.append(max(highs[j]-lows[j],abs(highs[j]-prev),abs(lows[j]-prev)))
        ma=mean(closes[i-KC_LEN+1:i+1]); rangema=mean(tr)
        upperKC=ma+KC_MULT*rangema; lowerKC=ma-KC_MULT*rangema
        sq[i]=(lowerBB>lowerKC and upperBB<upperKC)
        off[i]=(lowerBB<lowerKC and upperBB>upperKC)
        hh=max(highs[i-KC_LEN+1:i+1]); ll=min(lows[i-KC_LEN+1:i+1]); sma=mean(closes[i-KC_LEN+1:i+1])
        src=[]
        for j in range(i-KC_LEN+1,i+1):
            jj0=j-KC_LEN+1
            if jj0<0: src=[]; break
            hhv=max(highs[jj0:j+1]); llv=min(lows[jj0:j+1]); sm=mean(closes[jj0:j+1])
            src.append(closes[j]-(((hhv+llv)/2+sm)/2))
        if len(src)==KC_LEN: mom[i]=linreg_last(src)
    ev=[]
    for i in range(40,n-5):
        if not (sq[i-1] and off[i]): continue
        trail=[x for x in lrets[i-19:i+1] if x is not None]
        fut=[x for x in lrets[i+1:i+5] if x is not None]
        if len(trail)!=20 or len(fut)!=4 or mom[i] is None: continue
        exp4=4*mean([x*x for x in trail]); fut4=sum(x*x for x in fut)
        if exp4<=0: continue
        ratio=fut4/exp4
        side=1 if mom[i]>0 else (-1 if mom[i]<0 else 0)
        entry=rows[i+1]["o"]; exitp=rows[i+4]["c"]
        gross=side*((exitp/entry)-1)*10000 if side else 0.0
        ev.append({"t":rows[i]["t"],"ratio":ratio,"side":side,"gross_bps":gross,"net_bps":gross-COST_BPS if side else None})
    return ev
def profit_factor(vals):
    pos=sum(x for x in vals if x>0); neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else (float("inf") if pos>0 else 0.0)

def main():
    receipt={"lab_id":"TVSQZ-001","run_scope":"DISCOVERY_2022_2023_ONLY","symbols":{},"provenance":[]}
    all_events=[]
    for s in SYMBOLS:
        rows,prov=load_symbol(s)
        ev=compute_events(rows)
        receipt["symbols"][s]={"rows":len(rows),"events":len(ev)}
        receipt["provenance"].extend([{"symbol":s,**p} for p in prov])
        for e in ev: e["symbol"]=s
        all_events.extend(ev)
    ratios=[e["ratio"] for e in all_events]
    counted=[s for s in SYMBOLS if sum(1 for e in all_events if e["symbol"]==s)>=50]
    per_med={s:statistics.median([e["ratio"] for e in all_events if e["symbol"]==s]) for s in SYMBOLS if any(e["symbol"]==s for e in all_events)}
    stage_a={
      "events":len(ratios),
      "counted_symbols":counted,
      "overall_median_ratio":statistics.median(ratios) if ratios else None,
      "bootstrap95":bootstrap_ci(ratios,statistics.median,2000,20260923) if ratios else [None,None],
      "per_symbol_median":per_med
    }
    enough=len(ratios)>=500 and len(counted)>=4
    stage_a["classification"]="INSUFFICIENT_SAMPLE" if not enough else "PENDING_RULE"
    if enough:
        stage_a["pass"]=(stage_a["overall_median_ratio"]>=1.20 and stage_a["bootstrap95"][0]>1.05 and sum(v>1.0 for v in per_med.values())>=4)
        stage_a["classification"]="MECHANISM_DISCOVERY_SURVIVES" if stage_a["pass"] else "NO_EDGE"
    else: stage_a["pass"]=False
    receipt["stage_a"]=stage_a

    if stage_a["pass"]:
        trades=[e for e in all_events if e["side"]!=0]
        nets=[e["net_bps"] for e in trades]
        per_mean={s:mean([e["net_bps"] for e in trades if e["symbol"]==s]) for s in SYMBOLS if any(e["symbol"]==s for e in trades)}
        ci=bootstrap_ci(nets,mean,2000,20260924) if nets else [None,None]
        stage_b={"trades":len(nets),"mean_net_bps":mean(nets) if nets else None,"profit_factor":profit_factor(nets),"bootstrap95":ci,"per_symbol_mean_net_bps":per_mean}
        enough_b=len(nets)>=300
        stage_b["pass"]=bool(enough_b and stage_b["mean_net_bps"]>0 and stage_b["profit_factor"]>1.0 and ci[0]>0 and sum(v>0 for v in per_mean.values())>=4)
        stage_b["classification"]="DIRECTIONAL_DISCOVERY_SURVIVES" if stage_b["pass"] else ("INSUFFICIENT_SAMPLE" if not enough_b else "NO_EDGE")
        receipt["stage_b"]=stage_b
        receipt["terminal_state"]="DISCOVERY_SURVIVES_ONLY" if stage_b["pass"] else "DIRECTIONAL_EXACT_NO_EDGE"
    else:
        receipt["stage_b"]={"opened":False,"reason":"Stage A did not pass; directional outcomes intentionally not evaluated."}
        receipt["terminal_state"]=stage_a["classification"]

    combined="".join(p["sha256"] for p in receipt["provenance"]).encode()
    receipt["source_bundle_sha256"]=hashlib.sha256(combined).hexdigest()
    receipt["protected_periods_opened"]=[]
    receipt["live_execution"]=False
    receipt["merge_to_main"]=False
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"terminal_state":receipt["terminal_state"],"stage_a":receipt["stage_a"],"stage_b":receipt["stage_b"]},indent=2,allow_nan=False))
if __name__=="__main__": main()

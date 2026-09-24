#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, math, random, statistics, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/wbtc_btc_peg_reversion_001_discovery_receipt.json")
BASE="https://data.binance.vision/data/spot/monthly/klines/WBTCBTC/1h"
THRESH=0.995
BASE_COST=0.0020
STRESS_COST=0.0030

def pct(xs,p):
    ys=sorted(xs)
    k=(len(ys)-1)*p
    f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def bootstrap(xs,reps=10000,seed=20261004):
    rng=random.Random(seed); n=len(xs); vals=[]
    for _ in range(reps):
        vals.append(sum(xs[rng.randrange(n)] for __ in range(n))/n)
    return [pct(vals,.025),pct(vals,.975)]

def pf(xs):
    pos=sum(x for x in xs if x>0); neg=-sum(x for x in xs if x<0)
    if neg==0:return "INF" if pos>0 else None
    return pos/neg

def sign_p(xs):
    nz=[x for x in xs if x!=0]; n=len(nz); k=sum(x>0 for x in nz)
    if n==0:return None
    return sum(math.comb(n,j) for j in range(k,n+1))/(2**n)

def load():
    rows=[]; prov=[]
    for y in (2022,2023):
        for m in range(1,13):
            ym=f"{y}-{m:02d}"
            url=f"{BASE}/WBTCBTC-1h-{ym}.zip"
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-WBTC-MR-001/1.0"})
            with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
            sha=hashlib.sha256(raw).hexdigest()
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                name=z.namelist()[0]
                with io.TextIOWrapper(z.open(name),encoding="utf-8") as fh:
                    n=0
                    for a in csv.reader(fh):
                        if not a or not a[0].isdigit():continue
                        rows.append({
                          "open_ms":int(a[0]),"open":float(a[1]),"high":float(a[2]),"low":float(a[3]),"close":float(a[4]),
                          "quote_volume":float(a[7]),"trades":int(a[8]),"close_ms":int(a[6])
                        });n+=1
            prov.append({"url":url,"sha256":sha,"rows":n})
    rows.sort(key=lambda x:x["open_ms"])
    # deterministic de-dupe
    d={x["open_ms"]:x for x in rows}
    rows=[d[k] for k in sorted(d)]
    return rows,prov

def valid_bar(b):
    return b["trades"]>=3 and b["quote_volume"]>=0.05 and b["open"]>0 and b["close"]>0

def continuous(seq):
    return all(seq[i+1]["open_ms"]-seq[i]["open_ms"]==3600000 for i in range(len(seq)-1))

def main():
    rows,prov=load()
    trades=[]; excluded=[]; i=1
    while i<len(rows)-50:
        prev=rows[i-1]; sig=rows[i]
        cross=(prev["close"]>THRESH and sig["close"]<=THRESH)
        if not cross:
            i+=1;continue
        if not valid_bar(sig):
            excluded.append({"signal_open_ms":sig["open_ms"],"reason":"SIGNAL_BAR_LIQUIDITY_FILTER"})
            i+=1;continue
        entry_i=i+1; exit_i=entry_i+23
        if exit_i>=len(rows):
            excluded.append({"signal_open_ms":sig["open_ms"],"reason":"RIGHT_CENSORED"});break
        seq=rows[i:exit_i+1]
        if not continuous(seq):
            excluded.append({"signal_open_ms":sig["open_ms"],"reason":"HOURLY_GAP"})
            i+=1;continue
        entry=rows[entry_i]; exitb=rows[exit_i]
        if not valid_bar(entry) or not valid_bar(exitb):
            excluded.append({"signal_open_ms":sig["open_ms"],"reason":"ENTRY_OR_EXIT_LIQUIDITY_FILTER"})
            i+=1;continue
        gross=exitb["close"]/entry["open"]-1
        base=gross-BASE_COST; stress=gross-STRESS_COST

        def mark(h):
            j=entry_i+h-1
            if j>=len(rows):return None
            q=rows[entry_i:j+1]
            if not continuous(q):return None
            return rows[j]["close"]/entry["open"]-1
        first_touch=None
        for j in range(entry_i,exit_i+1):
            if rows[j]["high"]>=0.999:
                first_touch=j-entry_i+1;break

        dt=datetime.fromtimestamp(sig["close_ms"]/1000,tz=timezone.utc)
        trades.append({
          "signal_time_utc":dt.isoformat(),"year":dt.year,
          "signal_close":sig["close"],"entry_open":entry["open"],"exit_close_24h":exitb["close"],
          "entry_discount_bps":(1-entry["open"])*10000,
          "gross_return":gross,"base_net_return":base,"stress_net_return":stress,
          "markout_4h":mark(4),"markout_12h":mark(12),"markout_48h":mark(48),
          "hours_to_first_touch_0_999_within_24h":first_touch
        })
        # no overlap: resume after the completed exit bar
        i=exit_i+1

    base=[x["base_net_return"] for x in trades]; stress=[x["stress_net_return"] for x in trades]
    byyear={y:[x["base_net_return"] for x in trades if x["year"]==y] for y in (2022,2023)}
    ci=bootstrap(base) if base else [None,None]
    p=sign_p(base) if base else None
    pfb=pf(base) if base else None; pfs=pf(stress) if stress else None
    pos=sum(x for x in base if x>0)
    maxshare=max([x for x in base if x>0],default=0)/pos if pos>0 else None
    enough=len(trades)>=30 and all(len(byyear[y])>=8 for y in byyear)
    def pfn(v): return float("inf") if v=="INF" else (-1 if v is None else v)
    passed=bool(enough and statistics.mean(base)>0 and ci[0]>0 and pfn(pfb)>=1.20 and p is not None and p<0.05 and all(statistics.mean(byyear[y])>0 for y in byyear) and statistics.mean(stress)>0 and pfn(pfs)>1 and maxshare is not None and maxshare<=0.25)
    classification="DISCOVERY_MECHANISM_SURVIVES" if passed else ("DISCOVERY_INSUFFICIENT_SAMPLE" if not enough else "DISCOVERY_NO_EDGE")
    bundle=hashlib.sha256("".join(x["sha256"] for x in prov).encode()).hexdigest()
    receipt={
      "lab_id":"WBTC-BTC-PEG-REVERSION-001","scope":"2022_2023_DISCOVERY_ONLY","classification":classification,
      "sample":{"completed_nonoverlap_episodes":len(trades),"by_year":{str(y):len(byyear[y]) for y in byyear},"excluded_candidates":len(excluded)},
      "primary":{
        "mean_gross_return":statistics.mean([x["gross_return"] for x in trades]) if trades else None,
        "mean_base_net_return":statistics.mean(base) if base else None,
        "median_base_net_return":statistics.median(base) if base else None,
        "bootstrap95_mean_base_net_return":ci,
        "base_profit_factor":pfb,
        "positive_count":sum(x>0 for x in base),"negative_count":sum(x<0 for x in base),
        "one_sided_sign_test_p":p,
        "mean_base_net_2022":statistics.mean(byyear[2022]) if byyear[2022] else None,
        "mean_base_net_2023":statistics.mean(byyear[2023]) if byyear[2023] else None,
        "mean_stress_net_return":statistics.mean(stress) if stress else None,
        "stress_profit_factor":pfs,
        "max_single_positive_episode_share":maxshare
      },
      "diagnostics":{
        "mean_entry_discount_bps":statistics.mean([x["entry_discount_bps"] for x in trades]) if trades else None,
        "mean_markout_4h":statistics.mean([x["markout_4h"] for x in trades if x["markout_4h"] is not None]) if trades else None,
        "mean_markout_12h":statistics.mean([x["markout_12h"] for x in trades if x["markout_12h"] is not None]) if trades else None,
        "mean_markout_48h":statistics.mean([x["markout_48h"] for x in trades if x["markout_48h"] is not None]) if trades else None,
        "touch_0_999_within_24h_fraction":sum(x["hours_to_first_touch_0_999_within_24h"] is not None for x in trades)/len(trades) if trades else None
      },
      "trades":trades,"exclusions":excluded,"source_files":prov,"source_bundle_sha256":bundle,
      "safety":{"2024_opened":False,"2025_opened":False,"2026_opened":False,"authenticated_api":False,"live_execution":False,"exchange_mutation":False,"merge_to_main":False}
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"classification":classification,"sample":receipt["sample"],"primary":receipt["primary"],"diagnostics":receipt["diagnostics"],"source_bundle_sha256":bundle},indent=2,allow_nan=False))
if __name__=="__main__":main()

#!/usr/bin/env python3
import csv, hashlib, io, json, math, random, statistics, sys, time, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

ROOT=Path("research/binance_premium_compression")
AUTH=json.loads((ROOT/"BPC_DISCOVERY_AUTHORITY_V0_1.json").read_text())
OUT=Path("artifacts/binance_premium_compression_discovery_v01")
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://data.binance.vision"
S=requests.Session()
S.headers.update({"User-Agent":"SRC-Crypto-Lab-BPC-Discovery/0.1","Accept":"*/*"})
BAR=300
ROLL=2016
START=datetime(2021,1,1,tzinfo=timezone.utc)
END=datetime(2024,1,1,tzinfo=timezone.utc)
ASSETS={"BTC":"BTCUSDT","ETH":"ETHUSDT"}

def sha(b): return hashlib.sha256(b).hexdigest()

def month_iter(start,end):
    y,m=start.year,start.month
    while (y,m)<(end.year,end.month):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13: y+=1; m=1

def get(url,attempts=6):
    last=None
    for i in range(attempts):
        try:
            r=S.get(url,timeout=45)
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f"HTTP {r.status_code} {url}")
                if i<attempts-1: time.sleep(min(8,0.5*(2**i))); continue
                raise last
            if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code} {url}")
            return r.content
        except (requests.RequestException,RuntimeError) as e:
            last=e
            if i<attempts-1 and isinstance(e,requests.RequestException):
                time.sleep(min(8,0.5*(2**i))); continue
            raise
    raise last or RuntimeError("unreachable")

def parse_checksum(raw,filename):
    parts=raw.decode("utf-8","replace").strip().split()
    if len(parts)<2: raise RuntimeError(f"BAD_CHECKSUM_LINE:{filename}")
    dg=parts[0].lower(); name=parts[-1].lstrip("*")
    if len(dg)!=64 or any(c not in "0123456789abcdef" for c in dg): raise RuntimeError(f"BAD_CHECKSUM_DIGEST:{filename}")
    if name!=filename: raise RuntimeError(f"BAD_CHECKSUM_FILENAME:{filename}:{name}")
    return dg

def to_sec(v):
    n=int(v)
    if n>10**14: return n//1_000_000
    if n>10**11: return n//1000
    return n

def load_month(path,kind):
    fn=path.rsplit("/",1)[-1]
    cs=get(f"{BASE}/{path}.CHECKSUM")
    expected=parse_checksum(cs,fn)
    raw=get(f"{BASE}/{path}")
    actual=sha(raw)
    if actual!=expected: raise RuntimeError(f"SHA_MISMATCH:{path}")
    z=zipfile.ZipFile(io.BytesIO(raw))
    bad=z.testzip()
    if bad: raise RuntimeError(f"ZIP_CRC:{path}:{bad}")
    names=[n for n in z.namelist() if not n.endswith("/")]
    if len(names)!=1: raise RuntimeError(f"ZIP_MEMBER_COUNT:{path}:{len(names)}")
    rows={}
    with z.open(names[0]) as fh:
        txt=io.TextIOWrapper(fh,encoding="utf-8-sig",errors="replace",newline="")
        for row in csv.reader(txt):
            if not row: continue
            if str(row[0]).lower() in {"open_time","opentime"}: continue
            if len(row)<5: raise RuntimeError(f"ROW_SHORT:{path}")
            ts=to_sec(row[0])
            if ts<int(START.timestamp()) or ts>=int(END.timestamp()): continue
            if kind=="premium":
                val=float(row[4])
                item=(val,)
            else:
                item=(float(row[1]),float(row[2]),float(row[3]),float(row[4]))
            prev=rows.get(ts)
            if prev is not None and prev!=item:
                raise RuntimeError(f"CONFLICTING_DUPLICATE:{path}:{ts}")
            rows[ts]=item
    return rows,{"path":path,"sha256":actual,"rows":len(rows)}

def merge_months(symbol):
    premium={};perp={};spot={};receipts=[]
    for ym in month_iter(START,END):
        specs=[
          ("premium",f"data/futures/um/monthly/premiumIndexKlines/{symbol}/5m/{symbol}-5m-{ym}.zip"),
          ("perp",f"data/futures/um/monthly/klines/{symbol}/5m/{symbol}-5m-{ym}.zip"),
          ("spot",f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{ym}.zip"),
        ]
        for kind,path in specs:
            rows,rc=load_month(path,kind);receipts.append(rc)
            target={"premium":premium,"perp":perp,"spot":spot}[kind]
            for ts,val in rows.items():
                prev=target.get(ts)
                if prev is not None and prev!=val: raise RuntimeError(f"CROSS_MONTH_DUPLICATE_CONFLICT:{kind}:{symbol}:{ts}")
                target[ts]=val
        print(f"LOAD_PROGRESS {symbol} {ym}",flush=True)
    return premium,perp,spot,receipts

def expected_ts():
    return list(range(int(START.timestamp()),int(END.timestamp()),BAR))

def coverage(d):
    return len(d)/len(expected_ts())

def funding_cross(entry_ts,exit_ts):
    a=datetime.fromtimestamp(entry_ts,tz=timezone.utc)
    b=datetime.fromtimestamp(exit_ts,tz=timezone.utc)
    d=a.date()-timedelta(days=1)
    while d<=b.date()+timedelta(days=1):
        for h in (0,8,16):
            t=int(datetime(d.year,d.month,d.day,h,0,tzinfo=timezone.utc).timestamp())
            if entry_ts<=t<=exit_ts: return True
        d+=timedelta(days=1)
    return False

def pf(vals):
    gp=sum(x for x in vals if x>0); gl=-sum(x for x in vals if x<0)
    if gl==0: return 1e9 if gp>0 else 0.0
    return gp/gl

def metrics(trades,key):
    vals=[t[key] for t in trades]
    return {
      "n":len(vals),
      "mean_bps":statistics.fmean(vals) if vals else None,
      "profit_factor":pf(vals) if vals else None,
      "sum_bps":sum(vals),
      "win_rate":sum(x>0 for x in vals)/len(vals) if vals else None
    }

def bootstrap_daily(trades,key):
    byday=defaultdict(float)
    for t in trades:
        d=datetime.fromtimestamp(t["entry_ts"],tz=timezone.utc).date().isoformat()
        byday[d]+=t[key]
    days=[];d=START.date();end=END.date()
    while d<end:
        days.append(byday.get(d.isoformat(),0.0));d+=timedelta(days=1)
    rng=random.Random(AUTH["discovery"]["bootstrap"]["seed"]);means=[];n=len(days)
    for _ in range(AUTH["discovery"]["bootstrap"]["resamples"]):
        means.append(sum(days[rng.randrange(n)] for __ in range(n))/n)
    means.sort()
    lo=means[int(0.025*(len(means)-1))];hi=means[int(0.975*(len(means)-1))]
    return {"days":n,"mean_daily_portfolio_bps":statistics.fmean(days),"bootstrap_95_lower":lo,"bootstrap_95_upper":hi}

def concentration(trades,key):
    pos=defaultdict(float)
    for t in trades:
        if t[key]>0:
            m=datetime.fromtimestamp(t["entry_ts"],tz=timezone.utc).strftime("%Y-%m")
            pos[m]+=t[key]
    total=sum(pos.values())
    return max(pos.values())/total if total>0 and pos else 1.0

def leave_one_min_mean(trades,key):
    vals=[t[key] for t in trades];n=len(vals)
    if n<=1:return None
    s=sum(vals);return min((s-x)/(n-1) for x in vals)

def simulate(asset,premium,perp,spot):
    tslist=expected_ts()
    prem_cov=coverage(premium);perp_cov=coverage(perp);spot_cov=coverage(spot)
    mincov=AUTH["data_integrity"]["minimum_bar_coverage_fraction_each_dataset_asset"]
    source_failures=[]
    for name,cov in (("premium",prem_cov),("perp",perp_cov),("spot",spot_cov)):
        if cov<mincov:source_failures.append(f"{asset}:{name}:COVERAGE_LT_{mincov}")
    signals=[];unresolved=0;funding_excluded=0;busy_until=-1
    base_cost=AUTH["execution"]["base_round_trip_pair_cost_fraction"]
    stress_cost=AUTH["execution"]["stress_round_trip_pair_cost_fraction"]
    for i in range(ROLL,len(tslist)-13):
        ts=tslist[i]
        if ts not in premium: continue
        prior=tslist[i-ROLL:i]
        if any(x not in premium for x in prior): continue
        vals=[premium[x][0] for x in prior]
        sd=statistics.stdev(vals)
        if not math.isfinite(sd) or sd<=0: continue
        cur=premium[ts][0];mu=statistics.fmean(vals);z=(cur-mu)/sd
        if cur<=0 or z<AUTH["signal"]["threshold"]: continue
        entry_ts=ts+BAR
        exit_ts=entry_ts+AUTH["execution"]["max_hold_bars"]*BAR
        if entry_ts<=busy_until: continue
        if funding_cross(entry_ts,exit_ts):
            funding_excluded+=1;continue
        if entry_ts not in spot or exit_ts not in spot or entry_ts not in perp or exit_ts not in perp:
            unresolved+=1;continue
        so=spot[entry_ts][0];sx=spot[exit_ts][0];po=perp[entry_ts][0];px=perp[exit_ts][0]
        if min(so,sx,po,px)<=0: unresolved+=1;continue
        spot_ret=sx/so-1.0
        perp_ret=px/po-1.0
        gross=spot_ret-perp_ret
        base=(gross-base_cost)*10000.0
        stress=(gross-stress_cost)*10000.0
        signals.append({
          "asset":asset,"signal_ts":ts,"entry_ts":entry_ts,"exit_ts":exit_ts,
          "premium":cur,"z":z,"spot_entry":so,"spot_exit":sx,"perp_entry":po,"perp_exit":px,
          "gross_bps":gross*10000.0,"base_net_bps":base,"stress_net_bps":stress
        })
        busy_until=exit_ts
    return signals,{
      "premium_coverage":prem_cov,"perp_coverage":perp_cov,"spot_coverage":spot_cov,
      "source_failures":source_failures,"execution_unresolved":unresolved,"funding_cross_exclusions":funding_excluded
    }

def main():
    assert AUTH["status"]=="PRE_OUTCOME_FROZEN"
    assert AUTH["signal"]["threshold"]==3.0 and AUTH["signal"]["rolling_window_bars"]==2016
    assert AUTH["execution"]["max_hold_bars"]==12
    assert AUTH["data"]["no_2024_access_before_discovery_classification"] is True
    assert AUTH["data"]["no_2025_access"] is True and AUTH["data"]["no_2026_access"] is True

    result={
      "lab_id":AUTH["lab_id"],"discovery_id":AUTH["discovery_id"],"classification":None,
      "year_2024_opened":False,"year_2025_opened":False,"year_2026_opened":False,
      "live_trading":False,"exchange_mutation":False,"orders":False,"merge_to_main":False
    }
    source_receipts=[];coverage_doc={};all_trades=[];source_failures=[];execution_unresolved=0
    try:
        for asset,sym in ASSETS.items():
            prem,perp,spot,rc=merge_months(sym);source_receipts.extend(rc)
            trades,diag=simulate(asset,prem,perp,spot)
            all_trades.extend(trades);coverage_doc[asset]=diag
            source_failures.extend(diag["source_failures"])
            execution_unresolved+=diag["execution_unresolved"]
        all_trades=sorted(all_trades,key=lambda x:(x["entry_ts"],x["asset"]))
        if source_failures or execution_unresolved:
            cls=AUTH["classifications"]["data_failure"]
            reason=";".join(source_failures+[f"EXECUTION_UNRESOLVED={execution_unresolved}"])
            gates=None
        elif len(all_trades)<AUTH["discovery"]["sample_floor_resolved_trades"]:
            cls=AUTH["classifications"]["insufficient_sample"];reason="resolved trades below frozen floor";gates=None
        else:
            bm=metrics(all_trades,"base_net_bps");sm=metrics(all_trades,"stress_net_bps");boot=bootstrap_daily(all_trades,"base_net_bps")
            byyear={str(y):metrics([t for t in all_trades if datetime.fromtimestamp(t["entry_ts"],tz=timezone.utc).year==y],"base_net_bps") for y in (2021,2022,2023)}
            byasset={a:metrics([t for t in all_trades if t["asset"]==a],"base_net_bps") for a in ASSETS}
            conc=concentration(all_trades,"base_net_bps");loo=leave_one_min_mean(all_trades,"base_net_bps")
            gates={
              "resolved_trades_gte":bm["n"]>=100,
              "base_mean_net_bps_gt":bm["mean_bps"]>0,
              "base_profit_factor_gt":bm["profit_factor"]>1.10,
              "bootstrap_95_lower_mean_daily_portfolio_bps_gt":boot["bootstrap_95_lower"]>0,
              "stress_mean_net_bps_gt":sm["mean_bps"]>0,
              "stress_profit_factor_gt":sm["profit_factor"]>1.0,
              "calendar_year_2021_mean_net_bps_gt":byyear["2021"]["mean_bps"] is not None and byyear["2021"]["mean_bps"]>0,
              "calendar_year_2022_mean_net_bps_gt":byyear["2022"]["mean_bps"] is not None and byyear["2022"]["mean_bps"]>0,
              "calendar_year_2023_mean_net_bps_gt":byyear["2023"]["mean_bps"] is not None and byyear["2023"]["mean_bps"]>0,
              "btc_only_mean_net_bps_gt":byasset["BTC"]["mean_bps"] is not None and byasset["BTC"]["mean_bps"]>0,
              "eth_only_mean_net_bps_gt":byasset["ETH"]["mean_bps"] is not None and byasset["ETH"]["mean_bps"]>0,
              "max_positive_month_share_lte":conc<=0.25,
              "minimum_leave_one_trade_out_mean_net_bps_gt":loo is not None and loo>0,
              "source_integrity_failures_eq":True,
              "execution_unresolved_eq":True
            }
            cls=AUTH["classifications"]["discovery_survives"] if all(gates.values()) else AUTH["classifications"]["discovery_no_edge"]
            reason="all frozen gates passed" if cls==AUTH["classifications"]["discovery_survives"] else "one or more frozen gates failed"
        bm=metrics(all_trades,"base_net_bps");sm=metrics(all_trades,"stress_net_bps")
        boot=bootstrap_daily(all_trades,"base_net_bps") if all_trades else None
        byyear={str(y):metrics([t for t in all_trades if datetime.fromtimestamp(t["entry_ts"],tz=timezone.utc).year==y],"base_net_bps") for y in (2021,2022,2023)}
        byasset={a:metrics([t for t in all_trades if t["asset"]==a],"base_net_bps") for a in ASSETS}
        result.update({
          "classification":cls,"reason":reason,"coverage":coverage_doc,
          "base_metrics":bm,"stress_metrics":sm,"bootstrap_daily":boot,
          "by_year":byyear,"by_asset":byasset,
          "max_positive_month_share":concentration(all_trades,"base_net_bps") if all_trades else None,
          "minimum_leave_one_trade_out_mean_net_bps":leave_one_min_mean(all_trades,"base_net_bps") if all_trades else None,
          "promotion_gates":gates,"source_failures":source_failures,"execution_unresolved":execution_unresolved,
          "source_receipt_sha256":sha(json.dumps(source_receipts,sort_keys=True).encode()),
          "trades_base":all_trades
        })
    except Exception as e:
        result["classification"]=AUTH["classifications"]["technical_failure"]
        result["reason"]=f"{type(e).__name__}:{e}"
    p=OUT/"discovery_result.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/"manifest.json").write_text(json.dumps({
      "authority_sha256":sha((ROOT/"BPC_DISCOVERY_AUTHORITY_V0_1.json").read_bytes()),
      "result_sha256":sha(p.read_bytes())
    },indent=2,sort_keys=True)+"\n")
    summary={k:v for k,v in result.items() if k!="trades_base"}
    print(json.dumps(summary,indent=2,sort_keys=True,allow_nan=False))
    return 0 if result["classification"]!=AUTH["classifications"]["technical_failure"] else 2

if __name__=="__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — ENTRY FINGERPRINT PROBE V0.1

NON-ADJUDICATING forensic reconstruction only.
No parameter optimization. No edge/promotion credit.

Uses:
- frozen seed trade ledger from user TradingView exports;
- official public Binance USD-M monthly BTCUSDT kline archives;
- a predeclared small set of standard indicator fingerprints.

Goal: identify whether entries resemble a known mechanism strongly enough
to guide source-code recovery. This is NOT a backtest of a new strategy.
"""
from __future__ import annotations
import base64, csv, gzip, io, json, math, statistics, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
LEDGER_B64=EVID/"SEED_TRADE_LEDGER_V0.1.csv.gz.b64"
EXPECTED_LEDGER_SHA="419a17f00bb1ad265888c3649f99f92dbb7f2d649aa9c3e987d7a3f71abfe8a3"

def sha256(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()

raw=gzip.decompress(base64.b64decode(LEDGER_B64.read_text().strip()))
if sha256(raw)!=EXPECTED_LEDGER_SHA:
    raise SystemExit("FAIL_CLOSED ledger hash mismatch")
rows=list(csv.DictReader(io.StringIO(raw.decode())))
for r in rows:
    r["trade_no"]=int(r["trade_no"]); r["entry_price"]=float(r["entry_price"])
    r["exit_price"]=None if r["exit_dt"]=="OPEN" or not r["exit_price"] else float(r["exit_price"])
    r["entry_ms"]=int(datetime.fromisoformat(r["entry_dt"]).replace(tzinfo=timezone.utc).timestamp()*1000)
    r["exit_ms"]=None if r["exit_dt"]=="OPEN" else int(datetime.fromisoformat(r["exit_dt"]).replace(tzinfo=timezone.utc).timestamp()*1000)

TF_MIN={"5m":5,"15m":15,"4h":240}
START={"5m":(2019,9),"15m":(2019,9),"4h":(2019,11)}
END={"5m":(2026,6),"15m":(2026,7),"4h":(2026,7)}

def months(a,b):
    y,m=a
    while (y,m)<=b:
        yield y,m
        m+=1
        if m==13:y+=1;m=1

def load_tf(tf):
    out=[]
    failures=[]
    for y,m in months(START[tf],END[tf]):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/{tf}/BTCUSDT-{tf}-{ym}.zip"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-BTC-CONVEX-001/1.0"})
            with urllib.request.urlopen(req,timeout=45) as resp: body=resp.read()
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                name=zf.namelist()[0]
                text=zf.read(name).decode()
            for q in csv.reader(io.StringIO(text)):
                if not q: continue
                try:t=int(q[0])
                except ValueError:continue
                if t>10**14:t//=1000
                out.append([t,float(q[1]),float(q[2]),float(q[3]),float(q[4])])
        except Exception as e:
            failures.append({"month":ym,"error":str(e),"url":url})
    out.sort(key=lambda x:x[0])
    return out,failures

def ema(vals,n):
    a=2/(n+1); out=[None]*len(vals); x=None
    for i,v in enumerate(vals):
        x=v if x is None else a*v+(1-a)*x
        out[i]=x
    return out

def rsi(vals,n=14):
    out=[None]*len(vals); ag=al=None
    gains=[0.0]*len(vals); losses=[0.0]*len(vals)
    for i in range(1,len(vals)):
        d=vals[i]-vals[i-1]; gains[i]=max(d,0); losses[i]=max(-d,0)
    if len(vals)<=n:return out
    ag=sum(gains[1:n+1])/n; al=sum(losses[1:n+1])/n
    out[n]=100 if al==0 else 100-100/(1+ag/al)
    for i in range(n+1,len(vals)):
        ag=(ag*(n-1)+gains[i])/n; al=(al*(n-1)+losses[i])/n
        out[i]=100 if al==0 else 100-100/(1+ag/al)
    return out

def atr(high,low,close,n=14):
    tr=[None]*len(close)
    for i in range(len(close)):
        tr[i]=high[i]-low[i] if i==0 else max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1]))
    out=[None]*len(close)
    if len(close)<n:return out
    x=sum(tr[:n])/n; out[n-1]=x
    for i in range(n,len(close)):
        x=(x*(n-1)+tr[i])/n; out[i]=x
    return out

def supertrend(high,low,close,period=10,mult=3.0):
    at=atr(high,low,close,period); n=len(close)
    trend=[None]*n; upper=[None]*n; lower=[None]*n
    prev_fu=prev_fl=None; prev_trend=1
    for i in range(n):
        if at[i] is None: continue
        mid=(high[i]+low[i])/2
        bu=mid+mult*at[i]; bl=mid-mult*at[i]
        if prev_fu is None:
            fu,fl=bu,bl
        else:
            fu=bu if (bu<prev_fu or close[i-1]>prev_fu) else prev_fu
            fl=bl if (bl>prev_fl or close[i-1]<prev_fl) else prev_fl
        if i==0 or trend[i-1] is None:
            cur=1
        elif trend[i-1]==-1 and close[i]>fu:
            cur=1
        elif trend[i-1]==1 and close[i]<fl:
            cur=-1
        else:
            cur=trend[i-1]
        trend[i]=cur; upper[i]=fu; lower[i]=fl
        prev_fu,prev_fl=fu,fl
    return trend

def build_features(bars):
    ts=[x[0] for x in bars]; op=[x[1] for x in bars]; hi=[x[2] for x in bars]; lo=[x[3] for x in bars]; cl=[x[4] for x in bars]
    e9,e21,e20,e50,e200=ema(cl,9),ema(cl,21),ema(cl,20),ema(cl,50),ema(cl,200)
    e12,e26=ema(cl,12),ema(cl,26); mac=[a-b for a,b in zip(e12,e26)]; msig=ema(mac,9)
    rs=rsi(cl,14); st=supertrend(hi,lo,cl,10,3.0)
    feats=[{} for _ in bars]
    for i in range(len(bars)):
        f=feats[i]
        def ok(x):return x is not None
        f["ema9_gt_21"]=e9[i]>e21[i]
        f["ema20_gt_50"]=e20[i]>e50[i]
        f["ema50_gt_200"]=e50[i]>e200[i]
        f["close_gt_ema200"]=cl[i]>e200[i]
        f["macd_gt_signal"]=mac[i]>msig[i]
        f["rsi14_gt_50"]=ok(rs[i]) and rs[i]>50
        f["rsi14_gt_55"]=ok(rs[i]) and rs[i]>55
        f["momentum20_pos"]=i>=20 and cl[i]>cl[i-20]
        f["close_gt_prev_high"]=i>=1 and cl[i]>hi[i-1]
        f["donchian20_breakout"]=i>=20 and cl[i]>max(hi[i-20:i])
        f["donchian55_breakout"]=i>=55 and cl[i]>max(hi[i-55:i])
        f["supertrend10x3_long"]=st[i]==1
        if i:
            p=feats[i-1]
            f["ema9_cross_21_up"]=f["ema9_gt_21"] and not p.get("ema9_gt_21",False)
            f["ema20_cross_50_up"]=f["ema20_gt_50"] and not p.get("ema20_gt_50",False)
            f["ema50_cross_200_up"]=f["ema50_gt_200"] and not p.get("ema50_gt_200",False)
            f["close_cross_ema200_up"]=f["close_gt_ema200"] and not p.get("close_gt_ema200",False)
            f["macd_cross_up"]=f["macd_gt_signal"] and not p.get("macd_gt_signal",False)
            f["rsi_cross_50_up"]=f["rsi14_gt_50"] and not p.get("rsi14_gt_50",False)
            f["rsi_cross_55_up"]=f["rsi14_gt_55"] and not p.get("rsi14_gt_55",False)
            f["supertrend_flip_long"]=f["supertrend10x3_long"] and not p.get("supertrend10x3_long",False)
        else:
            for k in ["ema9_cross_21_up","ema20_cross_50_up","ema50_cross_200_up","close_cross_ema200_up","macd_cross_up","rsi_cross_50_up","rsi_cross_55_up","supertrend_flip_long"]:f[k]=False
    return {"ts":ts,"open":op,"high":hi,"low":lo,"close":cl,"features":feats}

CANDIDATES=[
"ema9_gt_21","ema20_gt_50","ema50_gt_200","close_gt_ema200","macd_gt_signal",
"rsi14_gt_50","rsi14_gt_55","momentum20_pos","close_gt_prev_high",
"donchian20_breakout","donchian55_breakout","supertrend10x3_long",
"ema9_cross_21_up","ema20_cross_50_up","ema50_cross_200_up","close_cross_ema200_up",
"macd_cross_up","rsi_cross_50_up","rsi_cross_55_up","supertrend_flip_long"
]

result={"lab":"BTC-CONVEX-TREND-CAPTURE-001","probe":"ENTRY_FINGERPRINT_PROBE_V0.1",
"role":"NON_ADJUDICATING_FORENSIC_DIAGNOSTIC","promotion_credit":0,
"parameter_optimization":False,"candidate_families":CANDIDATES,"timeframes":{}}

for tf in ["5m","15m","4h"]:
    bars,fail=load_tf(tf); d=build_features(bars); index={t:i for i,t in enumerate(d["ts"])}
    trades=sorted([r for r in rows if r["timeframe"]==tf],key=lambda r:r["trade_no"])
    matched=[]; missing=[]
    prev_counts=defaultdict(int); same_counts=defaultdict(int)
    control_counts=defaultdict(int); control_n=0

    # entry observations
    for tr in trades:
        i=index.get(tr["entry_ms"])
        if i is None:
            missing.append({"trade_no":tr["trade_no"],"entry_dt":tr["entry_dt"]}); continue
        nearest={
            "open":abs(tr["entry_price"]/d["open"][i]-1)*10000,
            "close":abs(tr["entry_price"]/d["close"][i]-1)*10000,
            "high":abs(tr["entry_price"]/d["high"][i]-1)*10000,
            "low":abs(tr["entry_price"]/d["low"][i]-1)*10000,
        }
        rec={"trade_no":tr["trade_no"],"entry_dt":tr["entry_dt"],"entry_price":tr["entry_price"],
             "entry_bar_open":d["open"][i],"entry_bar_close":d["close"][i],
             "abs_bps_to_open":nearest["open"],"abs_bps_to_close":nearest["close"],
             "inside_bar":d["low"][i]-1e-9<=tr["entry_price"]<=d["high"][i]+1e-9}
        if i>0:
            for k in CANDIDATES:
                v=bool(d["features"][i-1][k]); prev_counts[k]+=int(v)
            rec["prev_bar_features"]={k:bool(d["features"][i-1][k]) for k in CANDIDATES}
        for k in CANDIDATES:
            v=bool(d["features"][i][k]); same_counts[k]+=int(v)
        rec["same_bar_features"]={k:bool(d["features"][i][k]) for k in CANDIDATES}
        matched.append(rec)

    # flat controls: bars strictly between previous exit and next entry; condition evaluated previous bar
    for j in range(1,len(trades)):
        px=trades[j-1]["exit_ms"]; en=trades[j]["entry_ms"]
        if px is None or en is None or en<=px: continue
        # walk only timestamps present in continuous data
        # use binary-ish index bounds
        import bisect
        a=bisect.bisect_right(d["ts"],px); b=bisect.bisect_left(d["ts"],en)
        for fill_i in range(a,b):
            sig_i=fill_i-1
            if sig_i<0: continue
            control_n+=1
            for k in CANDIDATES: control_counts[k]+=int(bool(d["features"][sig_i][k]))

    n=len(matched)
    rankings=[]
    for k in CANDIDATES:
        er=prev_counts[k]/n if n else 0
        cr=control_counts[k]/control_n if control_n else 0
        lift=(er/cr) if cr>0 else (999.0 if er>0 else 0.0)
        rankings.append({"feature":k,"entry_recall_prev_bar":er,"flat_control_rate":cr,"lift":lift,
                         "entry_recall_same_bar":same_counts[k]/n if n else 0})
    rankings.sort(key=lambda x:(x["entry_recall_prev_bar"],math.log10(1+x["lift"])),reverse=True)

    open_bps=[x["abs_bps_to_open"] for x in matched]; close_bps=[x["abs_bps_to_close"] for x in matched]
    result["timeframes"][tf]={
        "bars_loaded":len(bars),"source_failures":fail,"entry_count_expected":len(trades),
        "entry_count_matched":n,"missing_entries":missing,"flat_control_bars":control_n,
        "entry_fill_fingerprint":{
            "median_abs_bps_to_bar_open":statistics.median(open_bps) if open_bps else None,
            "median_abs_bps_to_bar_close":statistics.median(close_bps) if close_bps else None,
            "pct_entries_within_1bp_of_open":sum(x<=1 for x in open_bps)/n if n else None,
            "pct_entries_inside_reported_bar_range":sum(x["inside_bar"] for x in matched)/n if n else None,
        },
        "candidate_rankings":rankings,
        "entries":matched
    }

out=EVID/"ENTRY_FINGERPRINT_PROBE_V0.1.json"
out.write_text(json.dumps(result,indent=2),encoding="utf-8")
for tf,v in result["timeframes"].items():
    print("\n==",tf,"==")
    print("matched",v["entry_count_matched"],"/",v["entry_count_expected"],"controls",v["flat_control_bars"])
    print("fill",v["entry_fill_fingerprint"])
    for x in v["candidate_rankings"][:10]:
        print(x["feature"],"recall",round(x["entry_recall_prev_bar"],3),"control",round(x["flat_control_rate"],3),"lift",round(x["lift"],2),"same",round(x["entry_recall_same_bar"],3))
print("WROTE",out)

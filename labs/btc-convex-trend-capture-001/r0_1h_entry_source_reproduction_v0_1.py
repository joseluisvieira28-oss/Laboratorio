#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — R0 1H ENTRY SOURCE REPRODUCTION V0.1

Goal: verify that the recovered Pine entry source explains the observed 1h
TradingView entry timestamps using official Binance USD-M BTCUSDT 1h klines.

This is reproduction/integrity work, not an edge test.
"""
from __future__ import annotations
import base64, csv, gzip, io, json, math, statistics, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, deque

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
LEDGER_B64=EVID/"SEED_TRADE_LEDGER_1H_V0.1.csv.gz.b64"
EXPECTED_SHA="ca6903faf7d4f42a40d0b76d4e7d106edec36007075d2da4600c4800b08583fa"

def sha256(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()

raw=gzip.decompress(base64.b64decode(LEDGER_B64.read_text().strip()))
if sha256(raw)!=EXPECTED_SHA:
    raise SystemExit("FAIL_CLOSED: 1h ledger hash mismatch")
ledger=list(csv.DictReader(io.StringIO(raw.decode())))
for r in ledger:
    r["n"]=int(r["n"])
    r["entry_ms"]=int(datetime.fromisoformat(r["entry_dt"].replace("Z","+00:00")).timestamp()*1000)
    r["exit_ms"]=None if r["exit_dt"]=="OPEN" else int(datetime.fromisoformat(r["exit_dt"].replace("Z","+00:00")).timestamp()*1000)
    for k in ["entry","qty","value","pnl","ret","comm","mfe_usdt","mfe_pct","mae_usdt","mae_pct","cum_pnl","cum_pct"]:
        if r[k]!="": r[k]=float(r[k])
    r["exit"]=None if r["exit"]=="" else float(r["exit"])
    r["bars"]=int(r["bars"])

def months(start,end):
    y,m=start
    while (y,m)<=end:
        yield y,m
        m+=1
        if m==13:y+=1;m=1

def load_bars():
    bars=[]; failures=[]
    for y,m in months((2019,9),(2026,7)):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{ym}.zip"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-BTC-CONVEX-R0/1.0"})
            with urllib.request.urlopen(req,timeout=45) as resp: body=resp.read()
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                name=zf.namelist()[0]
                txt=zf.read(name).decode()
            for q in csv.reader(io.StringIO(txt)):
                if not q: continue
                try:t=int(q[0])
                except ValueError:continue
                if t>10**14:t//=1000
                bars.append({
                    "t":t,"open":float(q[1]),"high":float(q[2]),"low":float(q[3]),
                    "close":float(q[4]),"volume":float(q[5]),
                })
        except Exception as e:
            failures.append({"month":ym,"url":url,"error":str(e)})
    bars.sort(key=lambda x:x["t"])
    return bars,failures

def sma(vals,n):
    out=[None]*len(vals); s=0.0; q=deque()
    for i,v in enumerate(vals):
        q.append(v); s+=v
        if len(q)>n:s-=q.popleft()
        if len(q)==n:out[i]=s/n
    return out

def stdev_biased(vals,n):
    out=[None]*len(vals); q=deque()
    for i,v in enumerate(vals):
        q.append(v)
        if len(q)>n:q.popleft()
        if len(q)==n:
            mu=sum(q)/n
            out[i]=math.sqrt(sum((x-mu)**2 for x in q)/n)
    return out

def rma(vals,n):
    out=[None]*len(vals)
    window=[]; prev=None
    for i,v in enumerate(vals):
        if v is None: continue
        if prev is None:
            window.append(v)
            if len(window)==n:
                prev=sum(window)/n
                out[i]=prev
        else:
            prev=(prev*(n-1)+v)/n
            out[i]=prev
    return out

def rsi(close,n=14):
    up=[None]*len(close); dn=[None]*len(close)
    for i in range(1,len(close)):
        ch=close[i]-close[i-1]
        up[i]=max(ch,0.0); dn[i]=max(-ch,0.0)
    au=rma(up,n); ad=rma(dn,n)
    out=[None]*len(close)
    for i in range(len(close)):
        if au[i] is None or ad[i] is None: continue
        if ad[i]==0: out[i]=100.0
        else:
            rs=au[i]/ad[i]; out[i]=100.0-100.0/(1.0+rs)
    return out

bars,failures=load_bars()
ts=[b["t"] for b in bars]
idx={t:i for i,t in enumerate(ts)}
cl=[b["close"] for b in bars]; vol=[b["volume"] for b in bars]

sma20=sma(cl,20); sd20=stdev_biased(cl,20); sma200=sma(cl,200)
vma20=sma(vol,20); rs14=rsi(cl,14)

sig=[]
for i,b in enumerate(bars):
    if None in (sma20[i],sd20[i],sma200[i],vma20[i],rs14[i]) or sd20[i]==0:
        sig.append(None); continue
    z=(cl[i]-sma20[i])/sd20[i]
    s_rsi=rs14[i] < 30
    s_z=z < -2.0
    s_bb=cl[i] < sma20[i]-2.0*sd20[i]
    s_vol=vol[i] > vma20[i]
    score=int(s_rsi)+int(s_z)+int(s_bb)+int(s_vol)
    sig.append({
        "z":z,"rsi":rs14[i],"s_rsi":s_rsi,"s_z":s_z,"s_bb":s_bb,"s_vol":s_vol,
        "score":score,"regime":cl[i]>sma200[i],"enter":score>=3 and cl[i]>sma200[i],
        "close":cl[i],"sma20":sma20[i],"sd20":sd20[i],"sma200":sma200[i],
        "volume":vol[i],"vma20":vma20[i],
    })

records=[]
prev_exit=None
ordinary_pass=ordinary_total=0
same_current_pass=same_prev_pass=same_total=0
branch_counts=Counter()
zbb_mismatches=0
price_open_match=0
same_ohlc=Counter()
missing=[]

for r in ledger:
    i=idx.get(r["entry_ms"])
    same=prev_exit is not None and r["entry_ms"]==prev_exit
    if i is None:
        missing.append({"n":r["n"],"entry_dt":r["entry_dt"]})
        prev_exit=r["exit_ms"]; continue
    for j in [i-1,i]:
        if 0<=j<len(sig) and sig[j] is not None and sig[j]["s_z"]!=sig[j]["s_bb"]:
            zbb_mismatches+=1
    if same:
        same_total+=1
        cur=sig[i] if i<len(sig) else None
        prv=sig[i-1] if i>0 else None
        same_current_pass += int(bool(cur and cur["enter"]))
        same_prev_pass += int(bool(prv and prv["enter"]))
        vals={k:bars[i][k] for k in ["open","high","low","close"]}
        dist={k:abs(r["entry"]/v-1)*10000 for k,v in vals.items()}
        nearest=min(dist,key=dist.get); same_ohlc[nearest]+=1
        prev_enter=bool(prv and prv["enter"])
        decision=cur
        decision_bar="same_bar_final_values"
    else:
        ordinary_total+=1
        prv=sig[i-1] if i>0 else None
        ordinary_pass += int(bool(prv and prv["enter"]))
        price_open_match += int(abs(r["entry"]/bars[i]["open"]-1)*10000 <= 1.0)
        prev_enter=None
        nearest=None
        decision=prv
        decision_bar="previous_closed_bar"
    if decision:
        if decision["s_rsi"] and decision["s_vol"]: branch_counts["RSI_AND_VOLUME"]+=1
        elif decision["s_rsi"]: branch_counts["RSI_ONLY"]+=1
        elif decision["s_vol"]: branch_counts["VOLUME_ONLY"]+=1
        else: branch_counts["NEITHER"]+=1
    records.append({
        "n":r["n"],"entry_dt":r["entry_dt"],"same_bar_reentry":same,
        "previous_bar_enter_for_samebar":prev_enter,
        "samebar_nearest_ohlc":nearest,
        "pnl":r["pnl"],"ret":r["ret"],
        "decision_bar":decision_bar,"decision":decision,
    })
    prev_exit=r["exit_ms"]

out={
    "lab":"BTC-CONVEX-TREND-CAPTURE-001",
    "probe":"R0_1H_ENTRY_SOURCE_REPRODUCTION_V0.1",
    "role":"SOURCE_REPRODUCTION_NOT_EDGE_TEST",
    "source_failures":failures,
    "bars_loaded":len(bars),
    "ledger_entries":len(ledger),
    "missing_entries":missing,
    "ordinary":{
        "count":ordinary_total,
        "source_signal_pass":ordinary_pass,
        "pass_rate":ordinary_pass/ordinary_total if ordinary_total else None,
        "entry_price_within_1bp_of_next_bar_open":price_open_match,
    },
    "same_bar_reentries":{
        "count":same_total,
        "current_bar_final_signal_pass":same_current_pass,
        "previous_bar_signal_pass":same_prev_pass,
        "nearest_ohlc_counts":dict(same_ohlc),
    },
    "entry_confirmation_branch_counts":dict(branch_counts),
    "zscore_vs_bb_boolean_mismatches":zbb_mismatches,
    "records":records,
}
path=EVID/"R0_1H_ENTRY_SOURCE_REPRODUCTION_V0.1.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in out.items() if k!="records"},indent=2))
print("WROTE",path)

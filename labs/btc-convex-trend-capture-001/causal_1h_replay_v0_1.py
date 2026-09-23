#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — CAUSAL 1H REPLAY V0.1
Protocol: CAUSAL_1H_REPLAY_PROTOCOL_V0.1.md

Execution-integrity diagnostic only. ZERO promotion credit.
"""
from __future__ import annotations
import base64, csv, gzip, io, json, math, urllib.request, zipfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
LEDGER_B64=EVID/"SEED_TRADE_LEDGER_1H_V0.1.csv.gz.b64"
EXPECTED_LEDGER_SHA="ca6903faf7d4f42a40d0b76d4e7d106edec36007075d2da4600c4800b08583fa"

START_MS=int(datetime(2020,3,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2026,6,30,23,0,tzinfo=timezone.utc).timestamp()*1000)
START_EQUITY=10489.94
EXPOSURE=0.95
FEE=0.001
STOP=0.04
TRAIL=0.12
ACT=0.05

def sha256(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()

raw=gzip.decompress(base64.b64decode(LEDGER_B64.read_text().strip()))
if sha256(raw)!=EXPECTED_LEDGER_SHA:
    raise SystemExit("FAIL_CLOSED: ledger hash mismatch")
ledger=list(csv.DictReader(io.StringIO(raw.decode())))
for r in ledger:
    r["n"]=int(r["n"])
    r["pnl"]=float(r["pnl"])
    r["ret"]=float(r["ret"])
    r["entry_ms"]=int(datetime.fromisoformat(r["entry_dt"].replace("Z","+00:00")).timestamp()*1000)
    r["exit_ms"]=None if r["exit_dt"]=="OPEN" else int(datetime.fromisoformat(r["exit_dt"].replace("Z","+00:00")).timestamp()*1000)

def months(a,b):
    y,m=a
    while (y,m)<=b:
        yield y,m
        m+=1
        if m==13:y+=1;m=1

def load_bars():
    out=[]; failures=[]
    for y,m in months((2020,2),(2026,6)):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{ym}.zip"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-BTC-CONVEX-Causal/1.0"})
            with urllib.request.urlopen(req,timeout=45) as resp: body=resp.read()
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                txt=zf.read(zf.namelist()[0]).decode()
            for q in csv.reader(io.StringIO(txt)):
                if not q: continue
                try:t=int(q[0])
                except ValueError:continue
                if t>10**14:t//=1000
                out.append({
                    "t":t,"open":float(q[1]),"high":float(q[2]),"low":float(q[3]),
                    "close":float(q[4]),"volume":float(q[5]),
                })
        except Exception as e:
            failures.append({"month":ym,"url":url,"error":str(e)})
    out.sort(key=lambda x:x["t"])
    return out,failures

def sma(vals,n):
    out=[None]*len(vals); q=deque(); s=0.0
    for i,v in enumerate(vals):
        q.append(v); s+=v
        if len(q)>n:s-=q.popleft()
        if len(q)==n:out[i]=s/n
    return out

def stdev(vals,n):
    out=[None]*len(vals); q=deque()
    for i,v in enumerate(vals):
        q.append(v)
        if len(q)>n:q.popleft()
        if len(q)==n:
            mu=sum(q)/n
            out[i]=math.sqrt(sum((x-mu)**2 for x in q)/n)
    return out

def rma(vals,n):
    out=[None]*len(vals); buf=[]; prev=None
    for i,v in enumerate(vals):
        if v is None: continue
        if prev is None:
            buf.append(v)
            if len(buf)==n:
                prev=sum(buf)/n; out[i]=prev
        else:
            prev=(prev*(n-1)+v)/n; out[i]=prev
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
        out[i]=100.0 if ad[i]==0 else 100.0-100.0/(1.0+au[i]/ad[i])
    return out

bars,failures=load_bars()
close=[b["close"] for b in bars]; vol=[b["volume"] for b in bars]
s20=sma(close,20); sd20=stdev(close,20); s200=sma(close,200); v20=sma(vol,20); r14=rsi(close,14)

signals=[False]*len(bars)
details=[None]*len(bars)
for i,b in enumerate(bars):
    if None in (s20[i],sd20[i],s200[i],v20[i],r14[i]) or sd20[i]==0:
        continue
    z=(close[i]-s20[i])/sd20[i]
    sr=r14[i]<30
    sz=z<-2.0
    sb=close[i]<s20[i]-2.0*sd20[i]
    sv=vol[i]>v20[i]
    score=int(sr)+int(sz)+int(sb)+int(sv)
    regime=close[i]>s200[i]
    signals[i]=score>=3 and regime
    details[i]={"z":z,"rsi":r14[i],"score":score,"rsi_flag":sr,"z_flag":sz,"bb_flag":sb,"vol_flag":sv,"regime":regime}

equity=START_EQUITY
peak_equity=equity
max_dd=0.0
pending_entry=False
position=None
active_stop=None
trades=[]
equity_points=[{"t":START_MS,"equity":equity}]
entry_signal_count=0

for i,b in enumerate(bars):
    t=b["t"]
    if t<START_MS or t>END_MS:
        continue

    # Fill pending market entry at this bar's open.
    if pending_entry and position is None:
        entry=b["open"]
        notional=equity*EXPOSURE
        qty=notional/entry
        entry_fee=notional*FEE
        equity-=entry_fee
        position={
            "entry_t":t,"entry":entry,"qty":qty,"entry_fee":entry_fee,
            "peak":entry,"initial_stop":entry*(1-STOP),
        }
        active_stop=position["initial_stop"]
        pending_entry=False

    # Process the stop already known before/currently at the start of this bar.
    exited=False
    if position is not None:
        fill=None
        if b["open"]<=active_stop:
            fill=b["open"]
        elif b["low"]<=active_stop:
            fill=active_stop
        if fill is not None:
            exit_fee=position["qty"]*fill*FEE
            price_pnl=position["qty"]*(fill-position["entry"])
            net_pnl=price_pnl-position["entry_fee"]-exit_fee
            equity += price_pnl-exit_fee
            trades.append({
                "entry_t":position["entry_t"],"exit_t":t,
                "entry":position["entry"],"exit":fill,
                "qty":position["qty"],"net_pnl":net_pnl,
                "position_return_pct":100.0*net_pnl/(position["qty"]*position["entry"]),
                "reason":"STOP",
            })
            position=None; active_stop=None; exited=True
            peak_equity=max(peak_equity,equity)
            max_dd=min(max_dd,equity/peak_equity-1.0)
            equity_points.append({"t":t,"equity":equity})

    # At confirmed close, update only with information now causally known.
    if position is not None:
        position["peak"]=max(position["peak"],b["high"])
        lucro=(b["close"]-position["entry"])/position["entry"]
        if lucro>=ACT:
            active_stop=max(position["initial_stop"],position["peak"]*(1-TRAIL))
        else:
            active_stop=position["initial_stop"]

    # If flat at confirmed close, exact recovered source may schedule next-bar entry.
    if position is None and signals[i]:
        pending_entry=True
        entry_signal_count+=1

# end mark
open_mark=None
if position is not None:
    last=next(b for b in reversed(bars) if b["t"]<=END_MS)
    mark=last["close"]
    unreal=position["qty"]*(mark-position["entry"])
    hypothetical_exit_fee=position["qty"]*mark*FEE
    open_mark={
        "entry_t":position["entry_t"],"entry":position["entry"],"mark_t":last["t"],"mark":mark,
        "unrealized_before_exit_fee":unreal,
        "hypothetical_net_if_closed_now":unreal-position["entry_fee"]-hypothetical_exit_fee,
    }

wins=[x for x in trades if x["net_pnl"]>0]
losses=[x for x in trades if x["net_pnl"]<0]
gross_win=sum(x["net_pnl"] for x in wins)
gross_loss=-sum(x["net_pnl"] for x in losses)
pf=gross_win/gross_loss if gross_loss>0 else None

# observed comparator from supplied ledger after frozen boundary, closed by replay end
obs=[r for r in ledger if r["entry_ms"]>=START_MS and r["exit_ms"] is not None and r["exit_ms"]<=END_MS]
obs_net=sum(r["pnl"] for r in obs)
obs_end=START_EQUITY+obs_net

# closed-trade tail dependence
sorted_wins=sorted(wins,key=lambda x:x["net_pnl"],reverse=True)
net_realized=equity-START_EQUITY
net_without_top1=net_realized-(sorted_wins[0]["net_pnl"] if sorted_wins else 0)
net_without_top3=net_realized-sum(x["net_pnl"] for x in sorted_wins[:3])

out={
    "lab":"BTC-CONVEX-TREND-CAPTURE-001",
    "probe":"CAUSAL_1H_REPLAY_V0.1",
    "classification":"EXECUTION_INTEGRITY_DIAGNOSTIC_ONLY",
    "source_failures":failures,
    "start":{"time":"2020-03-01T00:00:00Z","equity":START_EQUITY},
    "end":"2026-06-30T23:00:00Z",
    "rules":{"exposure":EXPOSURE,"fee_each_side":FEE,"hard_stop":STOP,"trail":TRAIL,"activation_close_profit":ACT,"same_bar_reentry":False},
    "causal_result":{
        "closed_trades":len(trades),
        "wins":len(wins),"losses":len(losses),
        "win_rate":len(wins)/len(trades) if trades else None,
        "ending_realized_equity":equity,
        "realized_net_pnl":net_realized,
        "realized_return_on_start":equity/START_EQUITY-1.0,
        "profit_factor":pf,
        "max_closed_equity_drawdown":max_dd,
        "entry_signals_while_flat":entry_signal_count,
        "net_without_top1":net_without_top1,
        "net_without_top3":net_without_top3,
        "open_mark":open_mark,
    },
    "supplied_ledger_comparator":{
        "closed_trades_after_boundary":len(obs),
        "net_pnl_after_boundary":obs_net,
        "ending_equity_from_same_start":obs_end,
        "return_on_same_start":obs_end/START_EQUITY-1.0,
        "note":"retrospective TradingView ledger; not a causal counterfactual"
    },
    "trades":trades,
    "equity_points":equity_points,
}
path=EVID/"CAUSAL_1H_REPLAY_V0.1.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in out.items() if k not in ("trades","equity_points")},indent=2))
print("WROTE",path)

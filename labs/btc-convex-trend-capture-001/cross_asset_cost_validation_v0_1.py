#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001
CROSS-ASSET COST VALIDATION V0.1

Authority:
- CROSS_ASSET_COST_VALIDATION_FREEZE_V0.1.md
- CROSS_ASSET_SOURCE_AMENDMENT_001.md
- CHILD_HYPOTHESIS_STICKY_TRAIL_H1_FREEZE.md

This script MUST run only after source gate PASS.
"""
from __future__ import annotations
import csv, io, json, math, hashlib, urllib.request, zipfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)

SYMBOLS=["ETHUSDT","SOLUSDT","BNBUSDT"]
START_MS=int(datetime(2021,1,1,0,0,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2025,12,31,23,0,tzinfo=timezone.utc).timestamp()*1000)
FEE=0.001
EXPOSURE=0.95
STOP=0.04
TRAIL=0.12
ACT=0.05
LAYERS={"REPRO":0.0,"BASE":0.0002,"STRESS":0.0005}
MODES=["PARENT","STICKY_H1"]

def months(y0,m0,y1,m1):
    y,m=y0,m0
    while (y,m)<=(y1,m1):
        yield y,m
        m+=1
        if m==13:y+=1;m=1

def get_bytes(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CrossAsset/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.read()

def parse_kline_zip(symbol,y,m,manifest):
    ym=f"{y:04d}-{m:02d}"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1h/{symbol}-1h-{ym}.zip"
    body=get_bytes(url)
    manifest.append({"kind":"kline","symbol":symbol,"month":ym,"url":url,"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)})
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        names=zf.namelist()
        if len(names)!=1: raise RuntimeError(f"{symbol} {ym} kline zip members {names}")
        text=zf.read(names[0]).decode("utf-8-sig")
    out=[]
    for q in csv.reader(io.StringIO(text)):
        if not q: continue
        try:t=int(q[0])
        except ValueError:continue
        if t>10**14:t//=1000
        out.append({"t":t,"open":float(q[1]),"high":float(q[2]),"low":float(q[3]),"close":float(q[4]),"volume":float(q[5])})
    return out

def parse_funding_zip(symbol,y,m,manifest):
    ym=f"{y:04d}-{m:02d}"
    url=f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"
    body=get_bytes(url)
    manifest.append({"kind":"funding","symbol":symbol,"month":ym,"url":url,"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)})
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        names=zf.namelist()
        if len(names)!=1: raise RuntimeError(f"{symbol} {ym} funding zip members {names}")
        text=zf.read(names[0]).decode("utf-8-sig")
    rd=csv.DictReader(io.StringIO(text))
    header=rd.fieldnames or []
    time_col=next((x for x in header if x.lower() in ("calc_time","fundingtime","funding_time")),None)
    rate_col=next((x for x in header if x.lower() in ("last_funding_rate","fundingrate","funding_rate")),None)
    if not time_col or not rate_col:
        raise RuntimeError(f"{symbol} {ym} funding schema unsupported: {header}")
    out=[]
    for r in rd:
        if not r.get(time_col): continue
        t=int(float(r[time_col]))
        if t>10**14:t//=1000
        rate=float(r[rate_col])
        out.append({"t":t,"rate":rate})
    return out

def load_symbol(symbol):
    manifest=[]; bars=[]; funds=[]
    for y,m in months(2020,12,2025,12):
        bars.extend(parse_kline_zip(symbol,y,m,manifest))
    for y,m in months(2021,1,2025,12):
        funds.extend(parse_funding_zip(symbol,y,m,manifest))
    # dedupe exact timestamps; duplicate disagreement fails closed
    bd={}
    for b in bars:
        if b["t"] in bd and bd[b["t"]]!=b: raise RuntimeError(f"{symbol} duplicate conflicting kline {b['t']}")
        bd[b["t"]]=b
    fd={}
    for x in funds:
        if x["t"] in fd and abs(fd[x["t"]]-x["rate"])>1e-15: raise RuntimeError(f"{symbol} duplicate conflicting funding {x['t']}")
        fd[x["t"]]=x["rate"]
    bars=[bd[k] for k in sorted(bd)]
    manifest_hash=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return bars,fd,manifest,manifest_hash

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
    au=rma(up,n); ad=rma(dn,n); out=[None]*len(close)
    for i in range(len(close)):
        if au[i] is None or ad[i] is None: continue
        out[i]=100.0 if ad[i]==0 else 100.0-100.0/(1+au[i]/ad[i])
    return out

def build_signals(bars):
    close=[b["close"] for b in bars]; vol=[b["volume"] for b in bars]
    s20=sma(close,20); sd=stdev(close,20); s200=sma(close,200); v20=sma(vol,20); r14=rsi(close,14)
    out=[False]*len(bars); details=[None]*len(bars)
    for i,b in enumerate(bars):
        if None in (s20[i],sd[i],s200[i],v20[i],r14[i]) or sd[i]==0: continue
        z=(close[i]-s20[i])/sd[i]
        sr=r14[i]<30; sz=z<-2.0; sb=close[i]<(s20[i]-2*sd[i]); sv=vol[i]>v20[i]
        score=int(sr)+int(sz)+int(sb)+int(sv)
        regime=close[i]>s200[i]
        out[i]=(score>=3 and regime)
        details[i]={"z":z,"rsi":r14[i],"score":score,"rsi_flag":sr,"z_flag":sz,"bb_flag":sb,"vol_flag":sv,"regime":regime}
    return out,details

def year_from_ms(t):
    return datetime.fromtimestamp(t/1000,tz=timezone.utc).year

def simulate(symbol,bars,funding,mode,slip):
    signals,_=build_signals(bars)
    index_by_t={b["t"]:i for i,b in enumerate(bars)}
    # Funding coverage integrity: every event in window must have a matching market bar.
    for t in funding:
        if START_MS<=t<=END_MS and t not in index_by_t:
            raise RuntimeError(f"{symbol} funding timestamp missing kline fallback {t}")

    equity=10000.0
    peak_mark=equity
    max_dd=0.0
    position=None
    pending=False
    active_stop=None
    trades=[]
    total_funding=0.0; total_commission=0.0; total_slippage=0.0
    signal_count=0
    losing_streak=max_losing_streak=0
    year_pnl={y:0.0 for y in range(2021,2026)}
    forced_end=False

    # Warmup bars are present; strategy starts FLAT at START_MS.
    for i,b in enumerate(bars):
        t=b["t"]
        if t<START_MS: continue
        if t>END_MS: break

        # 1) funding applies only to positions carried into this timestamp.
        if position is not None and position["entry_t"]<t and t in funding:
            mark=b["open"]  # frozen fallback from official market bar OPEN
            cf=-position["qty"]*mark*funding[t]
            equity+=cf
            position["funding"]+=cf
            total_funding+=cf

        # 2) fill pending causal entry at bar OPEN after funding event ordering.
        if pending and position is None:
            raw_entry=b["open"]
            exec_entry=raw_entry*(1+slip)
            # Match TradingView-style 95% allocation including entry commission.
            target=equity*EXPOSURE
            notional=target/(1+FEE)
            qty=notional/exec_entry
            entry_fee=qty*exec_entry*FEE
            equity-=entry_fee
            total_commission+=entry_fee
            entry_slip=qty*(exec_entry-raw_entry)
            total_slippage+=entry_slip
            position={
                "entry_t":t,"entry":exec_entry,"raw_entry":raw_entry,"qty":qty,
                "entry_fee":entry_fee,"funding":0.0,"slippage":entry_slip,
                "peak":exec_entry,"initial_stop":exec_entry*(1-STOP),
                "sticky":False,
            }
            active_stop=position["initial_stop"]
            pending=False

        # 3) execute the stop known before this bar's path.
        if position is not None:
            raw_exit=None
            if b["open"]<=active_stop:
                raw_exit=b["open"]
            elif b["low"]<=active_stop:
                raw_exit=active_stop
            if raw_exit is not None:
                exec_exit=raw_exit*(1-slip)
                exit_fee=position["qty"]*exec_exit*FEE
                price_pnl=position["qty"]*(exec_exit-position["entry"])
                exit_slip=position["qty"]*(raw_exit-exec_exit)
                total_commission+=exit_fee
                total_slippage+=exit_slip
                equity+=price_pnl-exit_fee
                net=price_pnl-position["entry_fee"]-exit_fee+position["funding"]
                tr={
                    "entry_t":position["entry_t"],"exit_t":t,"entry":position["entry"],"exit":exec_exit,
                    "net_pnl":net,"funding":position["funding"],
                    "commission":position["entry_fee"]+exit_fee,
                    "slippage_cost":position["slippage"]+exit_slip,
                    "return_pct":100*net/(position["qty"]*position["entry"]),
                    "reason":"STOP",
                }
                trades.append(tr)
                year_pnl[year_from_ms(t)]+=net
                if net<0:
                    losing_streak+=1; max_losing_streak=max(max_losing_streak,losing_streak)
                else: losing_streak=0
                position=None; active_stop=None

        # 4) at confirmed close, update state only with now-known information.
        if position is not None:
            position["peak"]=max(position["peak"],b["high"])
            lucro=(b["close"]-position["entry"])/position["entry"]
            if mode=="STICKY_H1":
                if lucro>=ACT: position["sticky"]=True
                if position["sticky"]:
                    active_stop=max(position["initial_stop"],position["peak"]*(1-TRAIL))
                else:
                    active_stop=position["initial_stop"]
            else:
                active_stop=max(position["initial_stop"],position["peak"]*(1-TRAIL)) if lucro>=ACT else position["initial_stop"]

        # 5) mark-to-market drawdown at completed bar close.
        marked=equity
        if position is not None:
            marked += position["qty"]*(b["close"]-position["entry"])
        peak_mark=max(peak_mark,marked)
        max_dd=min(max_dd,marked/peak_mark-1.0)

        # 6) flat confirmed-close signal schedules next-bar entry, except final bar.
        if position is None and t<END_MS and signals[i]:
            pending=True; signal_count+=1

        # 7) frozen forced end liquidation.
        if t==END_MS and position is not None:
            raw_exit=b["close"]
            exec_exit=raw_exit*(1-slip)
            exit_fee=position["qty"]*exec_exit*FEE
            price_pnl=position["qty"]*(exec_exit-position["entry"])
            exit_slip=position["qty"]*(raw_exit-exec_exit)
            total_commission+=exit_fee
            total_slippage+=exit_slip
            equity+=price_pnl-exit_fee
            net=price_pnl-position["entry_fee"]-exit_fee+position["funding"]
            trades.append({
                "entry_t":position["entry_t"],"exit_t":t,"entry":position["entry"],"exit":exec_exit,
                "net_pnl":net,"funding":position["funding"],
                "commission":position["entry_fee"]+exit_fee,
                "slippage_cost":position["slippage"]+exit_slip,
                "return_pct":100*net/(position["qty"]*position["entry"]),
                "reason":"FORCED_END",
            })
            year_pnl[2025]+=net
            forced_end=True
            if net<0:
                losing_streak+=1; max_losing_streak=max(max_losing_streak,losing_streak)
            else: losing_streak=0
            position=None; active_stop=None

    wins=[x for x in trades if x["net_pnl"]>0]
    losses=[x for x in trades if x["net_pnl"]<0]
    gross_win=sum(x["net_pnl"] for x in wins)
    gross_loss=-sum(x["net_pnl"] for x in losses)
    pf=(gross_win/gross_loss) if gross_loss>0 else None
    sorted_wins=sorted(wins,key=lambda x:x["net_pnl"],reverse=True)
    net=equity-10000.0
    years=5.0
    cagr=(equity/10000.0)**(1/years)-1 if equity>0 else -1.0
    return {
        "mode":mode,"slippage_bps_per_side":slip*10000,
        "closed_trades":len(trades),"wins":len(wins),"losses":len(losses),
        "win_rate":len(wins)/len(trades) if trades else None,
        "ending_equity":equity,"net_pnl":net,"net_return":equity/10000.0-1.0,
        "cagr":cagr,"profit_factor":pf,"max_mark_to_market_drawdown":max_dd,
        "max_losing_streak":max_losing_streak,
        "funding_cashflow":total_funding,
        "commission_paid":total_commission,
        "slippage_cost":total_slippage,
        "net_without_top1":net-(sorted_wins[0]["net_pnl"] if sorted_wins else 0.0),
        "net_without_top3":net-sum(x["net_pnl"] for x in sorted_wins[:3]),
        "top1_winner":sorted_wins[0]["net_pnl"] if sorted_wins else None,
        "top3_winners":sum(x["net_pnl"] for x in sorted_wins[:3]),
        "year_pnl":year_pnl,"forced_end_liquidation":forced_end,
        "entry_signals_while_flat":signal_count,
        "trades":trades,
    }

out={
    "lab":"BTC-CONVEX-TREND-CAPTURE-001",
    "experiment":"CROSS_ASSET_COST_VALIDATION_V0.1",
    "freeze":"CROSS_ASSET_COST_VALIDATION_FREEZE_V0.1",
    "source_amendment":"CROSS_ASSET_SOURCE_AMENDMENT_001",
    "period":["2021-01-01T00:00:00Z","2025-12-31T23:00:00Z"],
    "symbols":{},
    "family":{},
}
for symbol in SYMBOLS:
    bars,funding,manifest,mhash=load_symbol(symbol)
    # coverage checks before simulations
    window_bars=[b for b in bars if START_MS<=b["t"]<=END_MS]
    if not window_bars or window_bars[0]["t"]!=START_MS or window_bars[-1]["t"]!=END_MS:
        raise SystemExit(f"FAIL_CLOSED {symbol}: economic bar boundary missing")
    # all hourly timestamps must exist
    expected=((END_MS-START_MS)//3600000)+1
    if len(window_bars)!=expected:
        raise SystemExit(f"FAIL_CLOSED {symbol}: expected {expected} hourly bars, got {len(window_bars)}")
    if not funding:
        raise SystemExit(f"FAIL_CLOSED {symbol}: no funding records")
    sym={"provenance":{"manifest_sha256":mhash,"manifest_entries":manifest,
                       "bar_count_economic":len(window_bars),"funding_event_count":sum(1 for t in funding if START_MS<=t<=END_MS)},
         "results":{}}
    for mode in MODES:
        sym["results"][mode]={}
        for lname,slip in LAYERS.items():
            sym["results"][mode][lname]=simulate(symbol,bars,funding,mode,slip)
    out["symbols"][symbol]=sym

# Family summaries (do not pool dollars; normalized independent accounts).
for mode in MODES:
    fam={}
    for lname in LAYERS:
        rs=[out["symbols"][s]["results"][mode][lname] for s in SYMBOLS]
        fam[lname]={
            "equal_weight_mean_return":sum(r["net_return"] for r in rs)/len(rs),
            "median_asset_return":sorted(r["net_return"] for r in rs)[1],
            "positive_assets":sum(r["net_return"]>0 for r in rs),
            "pf_gt_1_assets":sum((r["profit_factor"] or 0)>1 for r in rs),
            "positive_after_remove_top1_assets":sum(r["net_without_top1"]>0 for r in rs),
        }
    out["family"][mode]=fam

pbase=out["family"]["PARENT"]["BASE"]
pstress=out["family"]["PARENT"]["STRESS"]
gate=(pbase["positive_assets"]>=2 and pbase["pf_gt_1_assets"]>=2 and pstress["equal_weight_mean_return"]>0 and pbase["positive_after_remove_top1_assets"]>=1)
out["parent_cross_asset_gate"]="SURVIVES" if gate else "CROSS_ASSET_REPLICATION_FAIL"

# Compact child deltas versus parent.
deltas={}
for s in SYMBOLS:
    deltas[s]={}
    for lname in LAYERS:
        p=out["symbols"][s]["results"]["PARENT"][lname]
        h=out["symbols"][s]["results"]["STICKY_H1"][lname]
        deltas[s][lname]={
            "net_return_delta":h["net_return"]-p["net_return"],
            "profit_factor_delta":(h["profit_factor"] or 0)-(p["profit_factor"] or 0),
            "max_drawdown_delta":h["max_mark_to_market_drawdown"]-p["max_mark_to_market_drawdown"],
            "net_without_top1_delta":h["net_without_top1"]-p["net_without_top1"],
        }
out["sticky_h1_deltas"]=deltas

# Persist full receipt.
path=EVID/"CROSS_ASSET_COST_VALIDATION_V0.1.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")

# Print compact outcome only.
compact={"gate":out["parent_cross_asset_gate"],"parent":{},"sticky":{},"family":out["family"]}
for s in SYMBOLS:
    compact["parent"][s]={k:{x:out["symbols"][s]["results"]["PARENT"][k][x] for x in ["closed_trades","net_return","cagr","profit_factor","max_mark_to_market_drawdown","funding_cashflow","net_without_top1"]} for k in LAYERS}
    compact["sticky"][s]={k:{x:out["symbols"][s]["results"]["STICKY_H1"][k][x] for x in ["closed_trades","net_return","cagr","profit_factor","max_mark_to_market_drawdown","funding_cashflow","net_without_top1"]} for k in LAYERS}
print(json.dumps(compact,indent=2))
print("WROTE",path)

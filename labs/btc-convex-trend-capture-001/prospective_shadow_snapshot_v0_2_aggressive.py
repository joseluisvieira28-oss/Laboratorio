#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — PROSPECTIVE SHADOW SNAPSHOT V0.2 AGGRESSIVE

Research-only. Public Binance data only. No orders, no private API, no exchange mutation.
Authority: PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE.md
"""
from __future__ import annotations
import hashlib, json, math, urllib.parse, urllib.request
from collections import deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)

SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT"]
BASE="https://www.binance.com"
FORWARD_START=datetime(2026,9,24,7,0,0,tzinfo=timezone.utc)
FORWARD_START_MS=int(FORWARD_START.timestamp()*1000)
WARMUP_START=FORWARD_START-timedelta(hours=1000)
WARMUP_START_MS=int(WARMUP_START.timestamp()*1000)
HOUR_MS=3_600_000

FEE=0.001
SLIP=0.0002
EXPOSURE=0.95
STOP=0.04
TRAIL=0.12
ACT=0.05

def get_raw(path,params):
    qs=urllib.parse.urlencode(params)
    url=BASE+path+"?"+qs
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-ForwardShadow/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
    return url,raw

def get_json(path,params):
    url,raw=get_raw(path,params)
    return url,raw,json.loads(raw.decode())

def fetch_klines(symbol,now_ms):
    out=[]; manifest=[]
    cursor=WARMUP_START_MS
    while cursor<now_ms:
        url,raw,arr=get_json("/fapi/v1/klines",{
            "symbol":symbol,"interval":"1h","startTime":cursor,
            "endTime":now_ms,"limit":1500,
        })
        manifest.append({"url":url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
        if not isinstance(arr,list):
            raise RuntimeError(f"{symbol}: invalid kline payload")
        if not arr: break
        for q in arr:
            if not isinstance(q,list) or len(q)<7: raise RuntimeError(f"{symbol}: invalid kline row")
            t=int(q[0]); ct=int(q[6])
            out.append({
                "t":t,"close_t":ct,"open":float(q[1]),"high":float(q[2]),
                "low":float(q[3]),"close":float(q[4]),"volume":float(q[5]),
            })
        nxt=int(arr[-1][0])+HOUR_MS
        if nxt<=cursor: raise RuntimeError(f"{symbol}: kline pagination stalled")
        cursor=nxt
        if len(arr)<1500: break

    dedup={}
    for b in out:
        if b["t"] in dedup and dedup[b["t"]]!=b:
            raise RuntimeError(f"{symbol}: conflicting duplicate kline {b['t']}")
        dedup[b["t"]]=b
    bars=[dedup[t] for t in sorted(dedup)]
    complete=[b for b in bars if b["close_t"]<now_ms]
    return complete,manifest

def normalize_hour(raw_t):
    norm=((raw_t+HOUR_MS//2)//HOUR_MS)*HOUR_MS
    dev=abs(raw_t-norm)
    if dev>1000:
        raise RuntimeError(f"funding timestamp deviation {dev}ms > 1000ms")
    return norm,dev

def fetch_funding(symbol,now_ms):
    seen={}; manifest=[]; cursor=FORWARD_START_MS
    if now_ms<FORWARD_START_MS:
        return {},manifest,{"count":0,"max_deviation_ms":0}
    while cursor<=now_ms:
        url,raw,arr=get_json("/fapi/v1/fundingRate",{
            "symbol":symbol,"startTime":cursor,"endTime":now_ms,"limit":1000,
        })
        manifest.append({"url":url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
        if not isinstance(arr,list): raise RuntimeError(f"{symbol}: invalid funding payload")
        if not arr: break
        for x in arr:
            raw_t=int(x["fundingTime"])
            t,dev=normalize_hour(raw_t)
            if t<FORWARD_START_MS or t>now_ms: continue
            rate=float(x["fundingRate"])
            mark=x.get("markPrice")
            if mark in (None,""):
                raise RuntimeError(f"{symbol}: forward funding record missing direct markPrice at {raw_t}")
            mark=float(mark)
            if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
                raise RuntimeError(f"{symbol}: invalid forward funding record")
            rec={"rate":rate,"mark":mark,"raw_t":raw_t,"t":t,"deviation_ms":dev}
            if t in seen:
                p=seen[t]
                if abs(p["rate"]-rate)>1e-15 or abs(p["mark"]-mark)>1e-10:
                    raise RuntimeError(f"{symbol}: conflicting funding duplicate {t}")
            else:
                seen[t]=rec
        nxt=int(arr[-1]["fundingTime"])+1
        if nxt<=cursor: raise RuntimeError(f"{symbol}: funding pagination stalled")
        cursor=nxt
        if len(arr)<1000: break
    return {t:seen[t] for t in sorted(seen)},manifest,{
        "count":len(seen),
        "max_deviation_ms":max([x["deviation_ms"] for x in seen.values()] or [0]),
    }

def sma(vals,n):
    out=[None]*len(vals); q=deque(); s=0.0
    for i,v in enumerate(vals):
        q.append(v); s+=v
        if len(q)>n: s-=q.popleft()
        if len(q)==n: out[i]=s/n
    return out

def stdev(vals,n):
    out=[None]*len(vals); q=deque()
    for i,v in enumerate(vals):
        q.append(v)
        if len(q)>n: q.popleft()
        if len(q)==n:
            m=sum(q)/n
            out[i]=math.sqrt(sum((x-m)**2 for x in q)/n)
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
        d=close[i]-close[i-1]
        up[i]=max(d,0.0); dn[i]=max(-d,0.0)
    au=rma(up,n); ad=rma(dn,n); out=[None]*len(close)
    for i in range(len(close)):
        if au[i] is None or ad[i] is None: continue
        out[i]=100.0 if ad[i]==0 else 100.0-100.0/(1+au[i]/ad[i])
    return out

def build_signals(bars):
    close=[b["close"] for b in bars]; vol=[b["volume"] for b in bars]
    s20=sma(close,20); sd=stdev(close,20); s200=sma(close,200); v20=sma(vol,20); r14=rsi(close,14)
    signals=[False]*len(bars); details=[None]*len(bars)
    for i in range(len(bars)):
        if None in (s20[i],sd[i],s200[i],v20[i],r14[i]) or sd[i]==0: continue
        z=(close[i]-s20[i])/sd[i]
        sr=r14[i]<30
        sz=z<-2.0
        sb=close[i]<(s20[i]-2*sd[i])
        sv=vol[i]>v20[i]
        score=int(sr)+int(sz)+int(sb)+int(sv)
        regime=close[i]>s200[i]
        signals[i]=score>=3 and regime
        details[i]={
            "z":z,"rsi":r14[i],"score":score,"rsi_flag":sr,
            "z_flag":sz,"bb_flag":sb,"vol_flag":sv,"regime":regime,
        }
    return signals,details

def replay(symbol,bars,funding):
    if len([b for b in bars if b["t"]<FORWARD_START_MS])<400:
        raise RuntimeError(f"{symbol}: insufficient forward warmup")

    # No gaps are allowed for completed post-boundary bars.
    fbars=[b for b in bars if b["t"]>=FORWARD_START_MS]
    if fbars:
        expected=list(range(FORWARD_START_MS,fbars[-1]["t"]+HOUR_MS,HOUR_MS))
        got=[b["t"] for b in fbars]
        if got!=expected:
            missing=sorted(set(expected)-set(got))
            raise RuntimeError(f"{symbol}: forward completed-bar gaps {missing[:5]}")

    sig,details=build_signals(bars)
    idx={b["t"]:i for i,b in enumerate(bars)}

    equity=10000.0
    peak_mark=equity
    max_dd=0.0
    pending=False
    position=None
    active_stop=None
    trades=[]
    total_funding=total_commission=total_slippage=0.0
    signals_seen=[]

    for i,b in enumerate(bars):
        t=b["t"]
        if t<FORWARD_START_MS: continue

        # Funding only if carried into timestamp.
        if position is not None and position["entry_t"]<t and t in funding:
            x=funding[t]
            cf=-position["qty"]*x["mark"]*x["rate"]
            equity+=cf; position["funding"]+=cf; total_funding+=cf

        if pending and position is None:
            raw=b["open"]; ep=raw*(1+SLIP)
            target=equity*EXPOSURE
            notional=target/(1+FEE)
            qty=notional/ep
            fee=qty*ep*FEE
            sl=qty*(ep-raw)
            equity-=fee
            total_commission+=fee; total_slippage+=sl
            position={
                "entry_t":t,"entry":ep,"raw_entry":raw,"qty":qty,
                "entry_fee":fee,"funding":0.0,"slippage":sl,
                "peak":ep,"initial_stop":ep*(1-STOP),
            }
            active_stop=position["initial_stop"]
            pending=False

        if position is not None:
            raw_exit=None
            if b["open"]<=active_stop: raw_exit=b["open"]
            elif b["low"]<=active_stop: raw_exit=active_stop
            if raw_exit is not None:
                xp=raw_exit*(1-SLIP)
                fee=position["qty"]*xp*FEE
                price_pnl=position["qty"]*(xp-position["entry"])
                sl=position["qty"]*(raw_exit-xp)
                equity+=price_pnl-fee
                total_commission+=fee; total_slippage+=sl
                net=price_pnl-position["entry_fee"]-fee+position["funding"]
                trades.append({
                    "entry_t":position["entry_t"],"exit_t":t,
                    "entry":position["entry"],"exit":xp,
                    "net_pnl":net,"funding":position["funding"],
                    "commission":position["entry_fee"]+fee,
                    "slippage_cost":position["slippage"]+sl,
                    "return_pct":100*net/(position["qty"]*position["entry"]),
                })
                position=None; active_stop=None

        if position is not None:
            position["peak"]=max(position["peak"],b["high"])
            lucro=(b["close"]-position["entry"])/position["entry"]
            active_stop=max(position["initial_stop"],position["peak"]*(1-TRAIL)) if lucro>=ACT else position["initial_stop"]

        marked=equity
        if position is not None:
            marked+=position["qty"]*(b["close"]-position["entry"])
        peak_mark=max(peak_mark,marked)
        max_dd=min(max_dd,marked/peak_mark-1)

        if position is None and sig[i]:
            pending=True
            signals_seen.append({
                "decision_bar_open_t":t,
                "decision_bar_close_t":b["close_t"],
                "signal_detail":details[i],
            })

    latest=fbars[-1] if fbars else None
    marked_equity=equity
    open_state=None
    if position is not None and latest is not None:
        marked_equity+=position["qty"]*(latest["close"]-position["entry"])
        open_state={
            "entry_t":position["entry_t"],
            "entry":position["entry"],
            "qty":position["qty"],
            "peak":position["peak"],
            "initial_stop":position["initial_stop"],
            "active_stop":active_stop,
            "funding":position["funding"],
            "marked_price":latest["close"],
        }

    wins=sum(1 for x in trades if x["net_pnl"]>0)
    return {
        "status":"FORWARD_COLLECTING_ONLY",
        "completed_forward_bars":len(fbars),
        "first_forward_bar_t":fbars[0]["t"] if fbars else None,
        "latest_forward_bar_t":latest["t"] if latest else None,
        "signals":signals_seen,
        "signal_count":len(signals_seen),
        "closed_trades":len(trades),
        "wins":wins,
        "losses":len(trades)-wins,
        "realized_equity":equity,
        "marked_equity":marked_equity,
        "realized_return":equity/10000-1,
        "marked_return":marked_equity/10000-1,
        "max_mtm_drawdown":max_dd,
        "funding_cashflow":total_funding,
        "commission_paid":total_commission,
        "slippage_cost":total_slippage,
        "pending_entry":pending,
        "open_position":open_state,
        "trades":trades,
    }

def main():
    now=datetime.now(timezone.utc)
    now_ms=int(now.timestamp()*1000)
    out={
        "lab":"BTC-CONVEX-TREND-CAPTURE-001",
        "snapshot":"PROSPECTIVE_SHADOW_SNAPSHOT_V0.2_AGGRESSIVE",
        "authority":"PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE",
        "snapshot_time_utc":now.isoformat(),
        "forward_start_utc":FORWARD_START.isoformat(),
        "symbols":{},
        "family":{},
        "source_manifest":{},
    }
    blocked=[]
    for s in SYMBOLS:
        try:
            bars,kman=fetch_klines(s,now_ms)
            funding,fman,fmeta=fetch_funding(s,now_ms)
            res=replay(s,bars,funding)
            out["symbols"][s]={"source_status":"PASS","funding_meta":fmeta,"result":res}
            out["source_manifest"][s]={"klines":kman,"funding":fman}
        except Exception as e:
            blocked.append(s)
            out["symbols"][s]={"source_status":"FORWARD_DATA_BLOCKED","error":repr(e),"result":None}

    valid=[s for s in SYMBOLS if s not in blocked]
    closed=sum(out["symbols"][s]["result"]["closed_trades"] for s in valid)
    marked_returns=[out["symbols"][s]["result"]["marked_return"] for s in valid]
    age_days=max(0.0,(now-FORWARD_START).total_seconds()/86400)
    assets_5=sum(out["symbols"][s]["result"]["closed_trades"]>=5 for s in valid)
    assets_5_ge2=assets_5>=2
    assets_5_ge3=assets_5>=3
    gap_ok=(len(blocked)==0)
    causal_blocker=False
    checkpoint_a=(closed>=10)
    checkpoint_b=(closed>=25 and assets_5_ge2 and gap_ok and not causal_blocker)
    checkpoint_c=(closed>=50 and assets_5_ge3 and gap_ok and not causal_blocker)
    out["family"]={
        "valid_symbols":valid,
        "blocked_symbols":blocked,
        "collection_age_days":age_days,
        "closed_trades_total":closed,
        "assets_with_ge_5_closed_trades":assets_5,
        "equal_weight_marked_return":sum(marked_returns)/len(marked_returns) if marked_returns else None,
        "v3_aggressive_checkpoints":{
            "A_10_trades_operational_audit":checkpoint_a,
            "B_25_trades_fragility_audit":checkpoint_b,
            "C_50_trades_v3_readjudication":checkpoint_c,
            "source_coverage_clean":gap_ok,
            "causal_integrity_blocker":causal_blocker,
        },
        "current_state":(
            "CHECKPOINT_C_READY_FOR_V3_READJUDICATION" if checkpoint_c else
            "CHECKPOINT_B_REACHED" if checkpoint_b else
            "CHECKPOINT_A_REACHED" if checkpoint_a else
            "FORWARD_COLLECTING_ONLY"
        ),
        "tier_promotion_automatic":False,
    }
    p=EVID/"PROSPECTIVE_SHADOW_SNAPSHOT_V0.2_AGGRESSIVE.json"
    p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    compact={
        "snapshot_time_utc":out["snapshot_time_utc"],
        "family":out["family"],
        "symbols":{
            s:{
                "source_status":out["symbols"][s]["source_status"],
                "completed_forward_bars":(out["symbols"][s]["result"] or {}).get("completed_forward_bars"),
                "signal_count":(out["symbols"][s]["result"] or {}).get("signal_count"),
                "closed_trades":(out["symbols"][s]["result"] or {}).get("closed_trades"),
                "pending_entry":(out["symbols"][s]["result"] or {}).get("pending_entry"),
                "open_position":(out["symbols"][s]["result"] or {}).get("open_position"),
            } for s in SYMBOLS
        }
    }
    print(json.dumps(compact,indent=2))
    print("WROTE",p)
    if blocked:
        raise SystemExit("FORWARD_DATA_BLOCKED")

if __name__=="__main__":
    main()

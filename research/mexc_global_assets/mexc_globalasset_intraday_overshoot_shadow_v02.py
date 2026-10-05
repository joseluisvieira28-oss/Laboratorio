#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,time,math
from datetime import datetime,timezone,timedelta
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_RULE_V1.0.json").read_text())
B=json.loads((HERE/"MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SOURCE_BINDING_V1.0.json").read_text())
UA="CryptoLab-Overshoot-Shadow/0.2"
MEXC="https://api.mexc.com/api/v1/contract"
BINANCE="https://fapi.binance.com/fapi/v1/klines"
BITGET="https://api.bitget.com/api/v2/mix/market/history-candles"
NOTIONALS=[10.0,25.0,50.0,100.0]
FEES=[12.0,14.0,16.0,20.0]

def req(url,params=None,timeout=12,retries=3):
    last=None
    for i in range(retries):
        t=time.perf_counter()
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            ms=(time.perf_counter()-t)*1000
            if r.status_code==200:return r,ms
            last=RuntimeError(f"HTTP_{r.status_code}:{r.url}")
        except Exception as e:last=e
        time.sleep(.2*(i+1))
    raise last

def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)

def parse_hm(day,hm):
    h,m=map(int,hm.split(":"))
    d=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return d.replace(hour=h,minute=m,second=0,microsecond=0)

def mexc_closes(symbol,now):
    start=int((now-timedelta(minutes=8)).timestamp())
    end=int((now+timedelta(minutes=1)).timestamp())
    r,ms=req(f"{MEXC}/kline/{symbol}",{"interval":"Min1","start":str(start),"end":str(end)})
    j=r.json();z=j.get("data") or {}
    if j.get("success") is not True:raise RuntimeError("MEXC_SUCCESS_FALSE")
    out={}
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try:out[int(t)+60]=float(p)
        except:pass
    return out,ms

def binance_closes(symbol,now):
    st=int((now-timedelta(minutes=8)).timestamp()*1000)
    r,ms=req(BINANCE,{"symbol":symbol,"interval":"1m","startTime":st,"limit":"12"})
    out={}
    for row in r.json() or []:
        try:out[int(row[0])//1000+60]=float(row[4])
        except:pass
    return out,ms

def bitget_closes(symbol,now):
    st=int((now-timedelta(minutes=8)).timestamp()*1000)
    en=int((now+timedelta(minutes=1)).timestamp()*1000)
    r,ms=req(BITGET,{"symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(st),"endTime":str(en),"limit":"12"})
    j=r.json()
    if j.get("code")!="00000":raise RuntimeError("BITGET_"+str(j.get("code")))
    out={}
    for row in j.get("data") or []:
        try:out[int(row[0])//1000+60]=float(row[4])
        except:pass
    return out,ms

def level(x):
    if isinstance(x,(list,tuple)) and len(x)>=2:return float(x[0]),float(x[1])
    if isinstance(x,dict):
        p=x.get("price",x.get("p"));v=x.get("vol",x.get("v",x.get("quantity",x.get("q"))))
        return float(p),float(v)
    raise ValueError("BAD_LEVEL")

def depth(symbol):
    r,ms=req(f"{MEXC}/depth/{symbol}")
    j=r.json();d=j.get("data") or {}
    if j.get("success") is not True:raise RuntimeError("DEPTH_SUCCESS_FALSE")
    bids=[level(x) for x in (d.get("bids") or [])]
    asks=[level(x) for x in (d.get("asks") or [])]
    if not bids or not asks:raise RuntimeError("EMPTY_BOOK")
    bids=sorted(bids,key=lambda x:x[0],reverse=True)
    asks=sorted(asks,key=lambda x:x[0])
    return {"captured_at_utc":datetime.now(timezone.utc).isoformat(),
            "latency_ms":ms,"bids":bids,"asks":asks}

def contract_sizes():
    r,_=req(f"{MEXC}/detail")
    j=r.json();out={}
    for x in j.get("data") or []:
        if isinstance(x,dict) and x.get("symbol"):
            try:out[x["symbol"]]=float(x.get("contractSize") or 1.0)
            except:out[x["symbol"]]=1.0
    return out

def fill(book,action,notional,contract_size):
    levels=book["asks"] if action=="BUY" else book["bids"]
    remain=notional;quote=0.0;base=0.0;used=0
    for p,v in levels:
        cap=max(0.0,p*v*contract_size)
        take=min(remain,cap)
        if take<=0:continue
        quote+=take;base+=take/p;remain-=take;used+=1
        if remain<=1e-9:break
    if remain>1e-6:return {"fillable":False,"requested_usdt":notional,"unfilled_usdt":remain,"levels_used":used}
    avg=quote/base if base>0 else None
    top=levels[0][0]
    slip=(avg/top-1)*10000 if action=="BUY" else (top/avg-1)*10000
    return {"fillable":True,"requested_usdt":notional,"avg_price":avg,"top_price":top,
            "book_slippage_bps":slip,"levels_used":used}

def signal_for(c,t):
    m,ml=mexc_closes(c["target"],datetime.fromtimestamp(t,timezone.utc))
    b,bl=binance_closes(c["external_binance"],datetime.fromtimestamp(t,timezone.utc))
    g,gl=bitget_closes(c["external_bitget"],datetime.fromtimestamp(t,timezone.utc))
    t0=t-5*60
    if not all(x in m for x in (t0,t)) or not all(x in b for x in (t0,t)) or not all(x in g for x in (t0,t)):
        return None,{"mexc_ms":ml,"binance_ms":bl,"bitget_ms":gl,"exact_points":False}
    rb=10000*(b[t]/b[t0]-1);rg=10000*(g[t]/g[t0]-1);ext=(rb+rg)/2;rm=10000*(m[t]/m[t0]-1);exc=rm-ext
    trig=(abs(rb-rg)<=R["trigger"]["max_external_leader_dispersion_bps"] and
          abs(rm)>=R["trigger"]["abs_mexc_5m_return_gte_bps"] and
          abs(exc)>=R["trigger"]["abs_mexc_excess_gte_bps"] and sgn(exc)==sgn(rm))
    meta={"mexc_ms":ml,"binance_ms":bl,"bitget_ms":gl,"exact_points":True}
    if not trig:return None,meta
    return {"target":c["target"],"external_binance":c["external_binance"],"external_bitget":c["external_bitget"],
            "timestamp":t,"signal_utc":datetime.fromtimestamp(t,timezone.utc).isoformat(),
            "binance_5m_bps":rb,"bitget_5m_bps":rg,"external_5m_bps":ext,"mexc_5m_bps":rm,
            "mexc_excess_bps":exc,"side":-sgn(exc)},meta

def wait_until(dt):
    while True:
        now=datetime.now(timezone.utc)
        s=(dt-now).total_seconds()
        if s<=0:return
        time.sleep(min(s,5))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",required=True)
    ap.add_argument("--start",required=True)
    ap.add_argument("--end",required=True)
    ap.add_argument("--segment",required=True)
    a=ap.parse_args()
    start=parse_hm(a.date,a.start);end=parse_hm(a.date,a.end)
    outdir=Path("artifacts/mexc_global_assets/intraday_overshoot_shadow_v02")/a.date/a.segment
    outdir.mkdir(parents=True,exist_ok=True)
    sizes=contract_sizes()
    pending=[]
    rows=[]
    errors=[]
    wait_until(start+timedelta(seconds=2))
    minute=start
    while minute<=end:
        target=minute+timedelta(seconds=2)
        wait_until(target)
        now=datetime.now(timezone.utc)
        t=int(minute.timestamp())
        if (now-minute).total_seconds()>45:
            errors.append({"minute":minute.isoformat(),"error":"LATE_SCAN","observed_at":now.isoformat()})
        triggers=[]
        for c in B["candidates"]:
            try:
                sig,lat=signal_for(c,t)
                if sig:
                    sig["signal_query_latency_ms"]=lat
                    triggers.append(sig)
            except Exception as e:
                errors.append({"minute":minute.isoformat(),"target":c["target"],"error":str(e)})
        if triggers:
            event={"timestamp":t,"signal_utc":minute.isoformat(),"assets":[]}
            for sig in triggers:
                try:
                    book=depth(sig["target"])
                    side=sig["side"];action="BUY" if side>0 else "SELL"
                    fills={str(int(n)):fill(book,action,n,sizes.get(sig["target"],1.0)) for n in NOTIONALS}
                    event["assets"].append({**sig,"entry_book":book,"entry_action":action,"entry_fills":fills})
                except Exception as e:
                    event["assets"].append({**sig,"entry_error":str(e)})
            pending.append({"due":minute+timedelta(minutes=5),"event":event})
        due=[x for x in pending if x["due"]<=datetime.now(timezone.utc)]
        pending=[x for x in pending if x not in due]
        for p in due:
            ev=p["event"]
            for x in ev["assets"]:
                if "entry_book" not in x:continue
                try:
                    book=depth(x["target"])
                    action="SELL" if x["side"]>0 else "BUY"
                    x["exit_book"]=book;x["exit_action"]=action
                    x["exit_fills"]={str(int(n)):fill(book,action,n,sizes.get(x["target"],1.0)) for n in NOTIONALS}
                except Exception as e:x["exit_error"]=str(e)
            rows.append(ev)
        minute+=timedelta(minutes=1)
    # flush exits for last 5 minutes
    for p in sorted(pending,key=lambda z:z["due"]):
        wait_until(p["due"]+timedelta(seconds=2))
        ev=p["event"]
        for x in ev["assets"]:
            if "entry_book" not in x:continue
            try:
                book=depth(x["target"]);action="SELL" if x["side"]>0 else "BUY"
                x["exit_book"]=book;x["exit_action"]=action
                x["exit_fills"]={str(int(n)):fill(book,action,n,sizes.get(x["target"],1.0)) for n in NOTIONALS}
            except Exception as e:x["exit_error"]=str(e)
        rows.append(ev)
    receipt={"family_id":R["family_id"],"shadow_version":"0.2","date":a.date,"segment":a.segment,
             "start_utc":a.start,"end_utc":a.end,"raw_event_timestamps":len(rows),
             "events":rows,"errors":errors,"notionals_usdt":NOTIONALS,"fee_scenarios_rt_bps":FEES,
             "cooldown_applied_online":False,"cooldown_policy":"apply deterministic frozen 10m global cooldown in final aggregator across all segments",
             "orders":False,"account_reads":False,"private_endpoints_used":False,"exchange_mutation":False,"live_trading":False}
    p=outdir/f"shadow_{a.date}_{a.segment}.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print(json.dumps({"date":a.date,"segment":a.segment,"events":len(rows),"errors":len(errors),"path":str(p)},sort_keys=True))

if __name__=="__main__":main()

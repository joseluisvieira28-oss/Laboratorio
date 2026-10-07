#!/usr/bin/env python3
from __future__ import annotations

import json, math, statistics, time
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://contract.mexc.com/api/v1/contract"
UA={"User-Agent":"CryptoLab-MEXC-Universe-Trade-Radar/0.1"}
MIN_AMOUNT24=20_000_000.0
TOP_N=60
TARGET_USDT=75.0
MAX_SPREAD_BPS=5.0
MAX_ENTRY_IMPACT_BPS=2.0
TAKER_BPS=8.0
RT_FEE_BPS=16.0
MAX_ABS_FUNDING=0.0005
FUNDING_BLOCK_SEC=30*60

def req(path,params=None,retries=3):
    last=None
    for i in range(retries):
        try:
            r=requests.get(BASE+path,params=params,headers=UA,timeout=15)
            r.raise_for_status()
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"bad payload {path}: {str(j)[:200]}")
            return j.get("data")
        except Exception as exc:
            last=exc
            time.sleep(0.25*(i+1))
    raise last

def ema(xs,n):
    if len(xs)<n: return None
    alpha=2.0/(n+1.0)
    v=sum(xs[:n])/n
    for x in xs[n:]:
        v=alpha*x+(1-alpha)*v
    return v

def rsi(xs,n=14):
    if len(xs)<n+1:return None
    gains=[]; losses=[]
    for a,b in zip(xs[-(n+1):-1],xs[-n:]):
        d=b-a
        gains.append(max(d,0.0)); losses.append(max(-d,0.0))
    ag=sum(gains)/n; al=sum(losses)/n
    if al==0:return 100.0
    rs=ag/al
    return 100.0-(100.0/(1.0+rs))

def atr(highs,lows,closes,n=14):
    if len(closes)<n+1:return None
    trs=[]
    start=len(closes)-n
    for i in range(start,len(closes)):
        pc=closes[i-1]
        trs.append(max(highs[i]-lows[i],abs(highs[i]-pc),abs(lows[i]-pc)))
    return sum(trs)/n

def candles(symbol,interval,secs,count=120):
    now=int(time.time())
    last_open=(now//secs)*secs-secs
    start=last_open-(count-1)*secs
    d=req(f"/kline/{symbol}",{"interval":interval,"start":str(start),"end":str(last_open)})
    if not isinstance(d,dict):raise RuntimeError(f"kline dict missing {symbol} {interval}")
    fields={}
    for k in ("time","open","close","high","low","vol"):
        arr=d.get(k) or []
        if not isinstance(arr,list):raise RuntimeError(f"kline {k} bad {symbol}")
        fields[k]=arr
    rows=[]
    lengths={len(v) for v in fields.values()}
    if len(lengths)!=1:raise RuntimeError("unequal candle arrays")
    m=len(fields["time"])
    for i in range(m):
        try:
            t=int(fields["time"][i])
            if t>last_open:continue
            rows.append({
                "time":t,"open":float(fields["open"][i]),"close":float(fields["close"][i]),
                "high":float(fields["high"][i]),"low":float(fields["low"][i]),"vol":float(fields["vol"][i])
            })
        except Exception:
            raise RuntimeError("invalid candle row") from None
    rows.sort(key=lambda x:x["time"])
    if len(rows)<60:raise RuntimeError(f"insufficient candles {symbol} {interval}: {len(rows)}")
    if rows[-1]["time"]!=last_open:raise RuntimeError(f"latest closed candle missing {symbol} {interval}")
    times=[x["time"] for x in rows]
    if any(t % secs for t in times) or any(b-a!=secs for a,b in zip(times,times[1:])):
        raise RuntimeError("candle gaps or duplicates")
    for row in rows:
        if not all(math.isfinite(row[k]) for k in ("open","close","high","low","vol")):
            raise RuntimeError("nonfinite candle")
        if not 0 < row["low"] <= min(row["open"],row["close"]) <= max(row["open"],row["close"]) <= row["high"] or row["vol"]<0:
            raise RuntimeError("invalid OHLCV")
    return rows

def fresh_timestamp(value, max_age=60):
    stamp=float(value)/1000
    now=time.time()
    if not math.isfinite(stamp) or not -5 <= now-stamp <= max_age:
        raise RuntimeError("missing, stale or future source timestamp")
    return stamp

def parse_level(row):
    px,qty=float(row[0]),float(row[1])
    if not math.isfinite(px) or not math.isfinite(qty) or px<=0 or qty<0:
        raise RuntimeError("invalid depth level")
    return px,qty

def visible_fill(rows,contracts,contract_size,side):
    lvls=[parse_level(x) for x in rows]
    lvls=sorted(lvls,key=lambda z:z[0],reverse=(side=="SELL"))
    remaining=contracts; quote=0.0
    top=lvls[0][0]
    for px,avail in lvls:
        take=min(remaining,max(0.0,avail))
        if take<=0:continue
        quote += px*take*contract_size
        remaining -= take
        if remaining<=1e-12:break
    if remaining>1e-9:return None
    qty=contracts*contract_size
    avg=quote/qty
    impact=(avg/top-1.0)*10000.0 if side=="BUY" else (1.0-avg/top)*10000.0
    return {"avg":avg,"top":top,"impact_bps":max(0.0,impact),"contracts":contracts,"qty":qty,"quote":quote}

def quantize_contracts(target,price,contract_size,vol_unit,min_vol,max_vol):
    raw=target/(price*contract_size)
    units=math.ceil(raw/vol_unit-1e-12)
    q=max(min_vol,units*vol_unit)
    if q>max_vol:return None
    return q

def trend_features(rows):
    c=[x["close"] for x in rows]; h=[x["high"] for x in rows]; l=[x["low"] for x in rows]; v=[x["vol"] for x in rows]
    e20=ema(c,20); e50=ema(c,50); rr=rsi(c,14); aa=atr(h,l,c,14)
    prev20=rows[-21:-1]
    return {
        "close":c[-1],"open":rows[-1]["open"],"high":h[-1],"low":l[-1],
        "ema20":e20,"ema50":e50,"rsi14":rr,"atr14":aa,
        "prior20_high":max(x["high"] for x in prev20),
        "prior20_low":min(x["low"] for x in prev20),
        "median_prev20_vol":statistics.median(x["vol"] for x in prev20),
        "last_vol":v[-1],
        "swing5_low":min(x["low"] for x in rows[-5:]),
        "swing5_high":max(x["high"] for x in rows[-5:]),
        "last_time":rows[-1]["time"],
    }

def signal(f15,f60):
    vol_ratio=f15["last_vol"]/f15["median_prev20_vol"] if f15["median_prev20_vol"]>0 else 0.0
    long_trend=f60["close"]>f60["ema20"]>f60["ema50"] and f15["close"]>f15["ema20"]>f15["ema50"]
    short_trend=f60["close"]<f60["ema20"]<f60["ema50"] and f15["close"]<f15["ema20"]<f15["ema50"]
    ext=(f15["close"]-f15["ema20"])/f15["atr14"] if f15["atr14"] else 99
    # A: breakout
    if long_trend and f15["close"]>f15["prior20_high"] and vol_ratio>=1.5 and 55<=f15["rsi14"]<=72 and 0<=ext<=1.5:
        return "LONG","BREAKOUT",vol_ratio
    if short_trend and f15["close"]<f15["prior20_low"] and vol_ratio>=1.5 and 28<=f15["rsi14"]<=45 and -1.5<=ext<=0:
        return "SHORT","BREAKOUT",vol_ratio
    # B: trend retest
    dist=abs(f15["close"]-f15["ema20"])/(f15["atr14"] or 1e-9)
    if f60["close"]>f60["ema20"]>f60["ema50"] and f15["ema20"]>f15["ema50"] and dist<=0.35 and f15["close"]>f15["open"] and 48<=f15["rsi14"]<=62 and vol_ratio>=1.0:
        return "LONG","TREND_RETEST",vol_ratio
    if f60["close"]<f60["ema20"]<f60["ema50"] and f15["ema20"]<f15["ema50"] and dist<=0.35 and f15["close"]<f15["open"] and 38<=f15["rsi14"]<=52 and vol_ratio>=1.0:
        return "SHORT","TREND_RETEST",vol_ratio
    return None,None,vol_ratio

def scan():
    observed=datetime.now(timezone.utc)
    tickers=req("/ticker")
    details=req("/detail")
    if isinstance(tickers,dict):tickers=[tickers]
    if isinstance(details,dict):details=[details]
    if not isinstance(tickers,list) or not tickers or not isinstance(details,list) or not details:
        raise RuntimeError("empty universe source")
    detail={str(x.get("symbol")):x for x in details if isinstance(x,dict)}
    universe=[]
    universe_source_errors=0
    source_error_counts={}
    for t in tickers:
        try:
            stage="UNIVERSE_DETAIL_JOIN"
            s=str(t["symbol"]); d=detail[s]
            if d.get("quoteCoin")!="USDT" or d.get("state")!=0 or d.get("futureType")!=1 or d.get("apiAllowed") is not True:continue
            stage="UNIVERSE_TICKER_SCHEMA"
            amount=float(t.get("amount24") or 0)
            bid=float(t["bid1"]); ask=float(t["ask1"]); last=float(t["lastPrice"])
            if not all(math.isfinite(x) for x in (amount,bid,ask,last)):raise RuntimeError("invalid ticker")
            if amount<MIN_AMOUNT24 or not(0<bid<=ask and last>0):continue
            stage="UNIVERSE_TICKER_TIMESTAMP"
            fresh_timestamp(t.get("timestamp"))
            spread=(ask-bid)/((ask+bid)/2)*10000
            if spread>MAX_SPREAD_BPS:continue
            universe.append((amount,s,t,d,spread))
        except Exception:
            universe_source_errors+=1
            source_error_counts[stage]=source_error_counts.get(stage,0)+1
    universe.sort(reverse=True,key=lambda x:x[0])
    universe=universe[:TOP_N]
    rejects={"UNIVERSE_SOURCE":universe_source_errors} if universe_source_errors else {}; passes=[]; scanned=[]
    for amount,s,t,d,spread in universe:
        rec={"symbol":s,"amount24":amount,"spread_bps":spread}
        try:
            c15=candles(s,"Min15",900,120); c60=candles(s,"Min60",3600,100)
            f15=trend_features(c15); f60=trend_features(c60)
            side,family,vol_ratio=signal(f15,f60)
            rec.update({"side":side,"family":family,"vol_ratio":vol_ratio,"f15":f15,"f60":f60})
            if not side:
                rejects["NO_SIGNAL"]=rejects.get("NO_SIGNAL",0)+1; scanned.append(rec); continue
            funding=req(f"/funding_rate/{s}")
            fr=float(funding["fundingRate"]); next_settle=int(funding["nextSettleTime"])/1000
            now=time.time()
            fresh_timestamp(funding.get("timestamp"))
            if not math.isfinite(fr) or next_settle<=now:raise RuntimeError("invalid funding")
            funding_favorable=(side=="LONG" and fr<0) or (side=="SHORT" and fr>0)
            if abs(fr)>MAX_ABS_FUNDING and not funding_favorable:
                rejects["FUNDING_EXTREME"]=rejects.get("FUNDING_EXTREME",0)+1; scanned.append(rec); continue
            if now<next_settle<=now+FUNDING_BLOCK_SEC:
                rejects["FUNDING_WINDOW"]=rejects.get("FUNDING_WINDOW",0)+1; scanned.append(rec); continue
            book=req(f"/depth/{s}",{"limit":20})
            book_timestamp=fresh_timestamp(book.get("timestamp"))
            asks=book.get("asks") or []; bids=book.get("bids") or []
            if not asks or not bids:raise RuntimeError("empty book")
            book_bid=max(parse_level(x)[0] for x in bids); book_ask=min(parse_level(x)[0] for x in asks)
            spread=(book_ask-book_bid)/((book_ask+book_bid)/2)*10000
            if spread<0 or spread>MAX_SPREAD_BPS:
                rejects["SPREAD"]=rejects.get("SPREAD",0)+1; scanned.append(rec); continue
            cs=float(d["contractSize"]); vu=float(d["volUnit"]); mv=float(d["minVol"]); mx=float(d.get("maxVol") or 1e18)
            entry_top=book_ask if side=="LONG" else book_bid
            contracts=quantize_contracts(TARGET_USDT,entry_top,cs,vu,mv,mx)
            if contracts is None:raise RuntimeError("size quantization")
            fill=visible_fill(asks if side=="LONG" else bids,contracts,cs,"BUY" if side=="LONG" else "SELL")
            if fill is None:
                rejects["DEPTH"]=rejects.get("DEPTH",0)+1; scanned.append(rec); continue
            if fill["impact_bps"]>MAX_ENTRY_IMPACT_BPS:
                rejects["IMPACT"]=rejects.get("IMPACT",0)+1; scanned.append(rec); continue
            entry=fill["avg"]; A=f15["atr14"]
            if side=="LONG":
                stop=min(f15["swing5_low"],entry-1.2*A)
                risk=(entry-stop)/entry
            else:
                stop=max(f15["swing5_high"],entry+1.2*A)
                risk=(stop-entry)/entry
            if not 0.006<=risk<=0.035:
                rejects["RISK_DISTANCE"]=rejects.get("RISK_DISTANCE",0)+1; scanned.append(rec); continue
            R=abs(entry-stop)
            if side=="LONG":
                tp1=entry+1.6*R; tp2=entry+2.5*R
                reward1=(tp1-entry)/entry*10000; reward2=(tp2-entry)/entry*10000
            else:
                tp1=entry-1.6*R; tp2=entry-2.5*R
                reward1=(entry-tp1)/entry*10000; reward2=(entry-tp2)/entry*10000
            risk_bps=risk*10000
            friction=RT_FEE_BPS+spread+2*fill["impact_bps"]
            rr1=max(0.0,reward1-friction)/(risk_bps+friction)
            rr2=max(0.0,reward2-friction)/(risk_bps+friction)
            if rr1<1.25 or rr2<2.0:
                rejects["NET_RR"]=rejects.get("NET_RR",0)+1; scanned.append(rec); continue
            tick=float(d["priceUnit"])
            def qpx(x):
                return round(round(x/tick)*tick,10)
            candidate={
              "symbol":s,"side":side,"signal_family":family,
              "observed_at_utc":datetime.now(timezone.utc).isoformat(),
              "signal_candle_open":f15["last_time"],
              "confirmation_candle_open":f60["last_time"],
              "source_book_timestamp":book_timestamp,
              "expires_at_epoch":book_timestamp+60,
              "entry":qpx(entry),"stop":qpx(stop),"tp1":qpx(tp1),"tp2":qpx(tp2),
              "contracts":contracts,"contract_size":cs,"quantity_base":contracts*cs,
              "notional_usdt":contracts*cs*entry,"leverage":3,"margin_mode":"ISOLATED",
              "spread_bps":spread,"entry_impact_bps":fill["impact_bps"],
              "fee_roundtrip_bps":RT_FEE_BPS,"observable_friction_bps":friction,
              "funding_rate":fr,"funding_cycle_hours":int(funding["collectCycle"]),
              "next_funding_ms":int(funding["nextSettleTime"]),
              "risk_bps":risk_bps,"net_rr_tp1":rr1,"net_rr_tp2":rr2,
              "volume_ratio_15m":vol_ratio,"amount24_usdt":amount,
              "rsi15":f15["rsi14"],"rsi1h":f60["rsi14"],
              "ema20_15":f15["ema20"],"ema50_15":f15["ema50"],
              "ema20_1h":f60["ema20"],"ema50_1h":f60["ema50"],
              "invalidation":f"{side} setup invalid if closed 15m breaches stop {qpx(stop)} before fill; snapshot expires after 60s",
              "classification":"TRADEABLE_CANDIDATE",
              "orders":False,"authenticated":False
            }
            passes.append(candidate); scanned.append({**rec,"candidate":candidate})
        except Exception as exc:
            rec["error"]=type(exc).__name__
            rejects["SOURCE_OR_SCHEMA"]=rejects.get("SOURCE_OR_SCHEMA",0)+1
            scanned.append(rec)
    family_rank={"BREAKOUT":0,"TREND_RETEST":1}
    passes.sort(key=lambda x:(family_rank.get(x["signal_family"],9),-x["net_rr_tp2"],-x["amount24_usdt"],x["observable_friction_bps"]))
    blocked=bool(rejects.get("SOURCE_OR_SCHEMA") or universe_source_errors)
    top=[] if blocked else passes[:3]
    result={
      "source_error_counts":source_error_counts,
      "source_health":"BLOCKED" if blocked else "OK",
      "verdict":"TRADE" if top else "NO_TRADE",
      "classification":"TRADEABLE_CANDIDATE" if top else "RADAR_EMPTY",
      "observed_at_utc":observed.isoformat(),
      "universe_eligible_count":len(universe),
      "candidates":top,
      "candidate_count":len(passes),
      "reject_counts":rejects,
      "scanned_symbols":[x["symbol"] for x in scanned],
      "fee_authority":"Inherited V0.1 assumption: taker 8 bps/fill, 16 bps roundtrip; account fee unverified",
      "orders_created":False,"account_reads":False,"authenticated":False,"exchange_mutation":False
    }
    return result

def main():
    result=scan()
    Path("mexc_universe_trade_radar_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()

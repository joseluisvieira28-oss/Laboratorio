#!/usr/bin/env python3
from __future__ import annotations
import json, math, time, requests
from datetime import datetime, timezone

CBASE="https://contract.mexc.com/api/v1/contract"
SBASE="https://api.mexc.com/api/v3"
UA={"User-Agent":"CryptoLab-MultiStable-OperatorScout/0.1"}
ASSETS={
 "BTC":{"USDT":"BTC_USDT","USDC":"BTC_USDC","USD1":"BTC_USD1"},
 "ETH":{"USDT":"ETH_USDT","USDC":"ETH_USDC","USD1":"ETH_USD1"},
}
SPOT={"USDC":"USDCUSDT","USD1":"USD1USDT"}
FEE_BPS_PER_FILL=8.0
PAIR_ROUNDTRIP_FEE_BPS=16.0
NOTIONAL_PER_LEG=25.0

def get(url,params=None):
    r=requests.get(url,params=params,headers=UA,timeout=15)
    r.raise_for_status()
    return r.json()

def spot_mid(sym):
    j=get(f"{SBASE}/ticker/bookTicker",{"symbol":sym})
    bid=float(j["bidPrice"]); ask=float(j["askPrice"])
    return {"bid":bid,"ask":ask,"mid":(bid+ask)/2}

def depth(sym):
    j=get(f"{CBASE}/depth/{sym}",{"limit":20})
    d=j.get("data") or {}
    bids=sorted([(float(x[0]),float(x[1])) for x in d.get("bids",[])],reverse=True)
    asks=sorted([(float(x[0]),float(x[1])) for x in d.get("asks",[])])
    if not bids or not asks: raise RuntimeError(f"empty book {sym}")
    return {"bid":bids[0][0],"bid_vol":bids[0][1],"ask":asks[0][0],"ask_vol":asks[0][1],"bids":bids,"asks":asks}

def detail():
    j=get(f"{CBASE}/detail")
    out={}
    for x in j.get("data") or []:
        s=x.get("symbol")
        if any(s in m.values() for m in ASSETS.values()):
            out[s]={"contract_size":float(x["contractSize"]),"vol_unit":float(x["volUnit"]),"min_vol":float(x["minVol"])}
    return out

def funding(sym):
    j=get(f"{CBASE}/funding_rate/{sym}")
    d=j.get("data") or {}
    return {
      "funding_rate": float(d.get("fundingRate") or 0.0),
      "next_settle_ms": int(d.get("nextSettleTime") or 0)
    }

def quantized_qty(target, px, conv, meta):
    raw=target/(px*meta["contract_size"]*conv)
    units=math.ceil(raw/meta["vol_unit"]-1e-12)
    return max(meta["min_vol"],units*meta["vol_unit"])

def fill(levels, qty, contract_size):
    left=qty; quote=0.0; used=0
    for p,v in levels:
        take=min(left,v)
        if take<=0: continue
        quote += p*take*contract_size
        left -= take; used += 1
        if left<=1e-12: break
    if left>1e-9: return None
    base=qty*contract_size
    return {"avg":quote/base,"quote":quote,"levels":used}

def main():
    now=datetime.now(timezone.utc)
    conv={"USDT":1.0}
    sp={}
    for coin,sym in SPOT.items():
        sp[coin]=spot_mid(sym); conv[coin]=sp[coin]["mid"]
    meta=detail()
    out={"observed_at_utc":now.isoformat(),"notional_per_leg_usdt":NOTIONAL_PER_LEG,
         "fee_bps_per_fill":FEE_BPS_PER_FILL,"pair_roundtrip_fee_bps":PAIR_ROUNDTRIP_FEE_BPS,
         "assets":{},"orders":False,"authenticated":False}
    for asset,legs in ASSETS.items():
        books={coin:depth(sym) for coin,sym in legs.items()}
        # executable normalized entry surfaces
        normalized={}
        for coin,sym in legs.items():
            b=books[coin]
            normalized[coin]={
              "symbol":sym,
              "bid_norm":b["bid"]*conv[coin],
              "ask_norm":b["ask"]*conv[coin],
              "raw_bid":b["bid"],"raw_ask":b["ask"]
            }
        rich=max(normalized,key=lambda c:normalized[c]["bid_norm"])
        cheap=min(normalized,key=lambda c:normalized[c]["ask_norm"])
        rb=books[rich]; cb=books[cheap]
        rq=quantized_qty(NOTIONAL_PER_LEG,rb["bid"],conv[rich],meta[legs[rich]])
        cq=quantized_qty(NOTIONAL_PER_LEG,cb["ask"],conv[cheap],meta[legs[cheap]])
        rf=fill(rb["bids"],rq,meta[legs[rich]]["contract_size"])
        cf=fill(cb["asks"],cq,meta[legs[cheap]]["contract_size"])
        if rf is None or cf is None:
            verdict="NO_TRADE_NOW_DEPTH"
            gap=None; ceiling=None
        else:
            rich_exec=rf["avg"]*conv[rich]
            cheap_exec=cf["avg"]*conv[cheap]
            gap=10000.0*math.log(rich_exec/cheap_exec)
            # equal gross notionals: full convergence captures approximately half the cross-price gap
            ceiling=gap/2.0 - PAIR_ROUNDTRIP_FEE_BPS
            verdict="TRADEABLE_CANDIDATE" if rich!=cheap and ceiling>0 else "NO_TRADE_NOW"
        f_r=funding(legs[rich]); f_c=funding(legs[cheap])
        crosses=any(now.timestamp()*1000 < f["next_settle_ms"] <= (now.timestamp()+15*60)*1000 for f in [f_r,f_c])
        if crosses and verdict=="TRADEABLE_CANDIDATE":
            verdict="NO_TRADE_NOW_FUNDING_WINDOW"
        out["assets"][asset]={
          "long_coin":cheap,"long_symbol":legs[cheap],
          "short_coin":rich,"short_symbol":legs[rich],
          "entry_gap_bps_executable":gap,
          "fee_only_full_convergence_net_ceiling_bps_on_gross_pair":ceiling,
          "funding_crosses_15m":crosses,
          "long_funding_rate":f_c["funding_rate"],"short_funding_rate":f_r["funding_rate"],
          "long_qty_contracts":cq if cf else None,"short_qty_contracts":rq if rf else None,
          "long_entry_avg":cf["avg"] if cf else None,"short_entry_avg":rf["avg"] if rf else None,
          "long_conv_to_usdt":conv[cheap],"short_conv_to_usdt":conv[rich],
          "verdict":verdict
        }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()

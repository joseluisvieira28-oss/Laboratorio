#!/usr/bin/env python3
"""OKX public read-only 1-snapshot spot/perp cash-and-carry cost falsifier."""
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

ASSETS = ("BTC", "ETH", "SOL")
ROUNDTRIP_FEES_BPS = Decimal("30")  # hypothetical: 2*10 spot + 2*5 perp bps
STRESS_FEES_BPS = Decimal("60")
MAX_AGE_MS = 30000
MAX_WINDOW_MS = 30000
EIGHT_HOURS = 28800000

def dec(v):
    try: x = Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError) as e: raise ValueError("INVALID_DECIMAL") from e
    if not x.is_finite(): raise ValueError("NONFINITE_DECIMAL")
    return x

def millis(v):
    if v is None or str(v).strip() == "": raise ValueError("MISSING_TIME")
    return int(v)

def bbo(packet, now):
    if not 0 <= now - millis(packet["ts"]) <= MAX_AGE_MS:
        raise ValueError("STALE_OR_FUTURE_BBO")
    bids, asks = packet["bids"], packet["asks"]
    if not bids or not asks: raise ValueError("EMPTY_BOOK")
    bid, bq = dec(bids[0][0]), dec(bids[0][1])
    ask, aq = dec(asks[0][0]), dec(asks[0][1])
    if min(bid,bq,ask,aq) <= 0 or bid >= ask:
        raise ValueError("CROSSED_OR_EMPTY_BBO")
    mid=(bid+ask)/2
    return {"bid":bid,"ask":ask,"spread_bps":(ask-bid)/mid*10000,
            "top_bid_qty":bq,"top_ask_qty":aq}

def pair(asset, response, now):
    sp, sw = f"{asset}-USDT", f"{asset}-USDT-SWAP"
    si=response["spot_info"]["data"]
    fi=response["swap_info"]["data"]
    sb=response["spot_book"]["data"]
    fb=response["swap_book"]["data"]
    fr=response["swap_funding"]["data"]
    if any(len(x)!=1 for x in (si,fi,sb,fb,fr)):
        raise ValueError("BAD_SOURCE_CARDINALITY")
    si,fi,sb,fb,fr=(x[0] for x in (si,fi,sb,fb,fr))
    if si.get("instId")!=sp or fi.get("instId")!=sw or fr.get("instId")!=sw:
        raise ValueError("IDENTITY_MISMATCH")
    if si.get("state")!="live" or fi.get("state")!="live" or fi.get("ctType")!="linear":
        raise ValueError("INSTRUMENT_NOT_LIVE_LINEAR")
    if fi.get("ctValCcy")!=asset or fi.get("settleCcy")!="USDT":
        raise ValueError("INVALID_CONTRACT_UNITS")
    tm = millis(fr["fundingTime"])
    prev = millis(fr["prevFundingTime"])
    if tm <= now or tm-prev != EIGHT_HOURS:
        raise ValueError("SOURCE_BLOCKED_INTERVAL")
    if fr.get("nextFundingTime"):
        if millis(fr["nextFundingTime"])-tm!=EIGHT_HOURS:
            raise ValueError("SOURCE_BLOCKED_NEXT_INTERVAL")
    spot, perp=bbo(sb,now),bbo(fb,now)
    spot_min,spot_lot=dec(si["minSz"]),dec(si["lotSz"])
    swap_min,swap_lot=dec(fi["minSz"]),dec(fi["lotSz"])
    ctval=dec(fi["ctVal"])
    ctmult=dec(fi["ctMult"]) if fi.get("ctMult") else Decimal("1")
    if min(spot_min,spot_lot,swap_min,swap_lot,ctval,ctmult)<=0:
        raise ValueError("INVALID_MIN_LOT")
    # Neither min hedge notional nor top qty proves that both legs fill.
    min_qty=max(spot_min,swap_min*ctval*ctmult)
    min_spot_usdt=min_qty*spot["ask"]
    # Exactly the cost of crossing both books twice if FUTURE quotes equal CURRENT quotes.
    spread=spot["spread_bps"]+perp["spread_bps"]
    funding=dec(fr["fundingRate"])*10000
    eight=funding-ROUNDTRIP_FEES_BPS-spread
    stress=funding-STRESS_FEES_BPS-spread
    sensitivity24=3*funding-ROUNDTRIP_FEES_BPS-spread
    sensitivity7d=21*funding-ROUNDTRIP_FEES_BPS-spread
    basis=(perp["bid"]-spot["ask"])/spot["ask"]*10000
    def s(v): return str(v)
    return {
      "asset":asset,
      "verdict":"8H_ESTIMATE_COVERS_FROZEN_HURDLE_NOT_EDGE" if eight>0 else "8H_ESTIMATE_BELOW_FROZEN_HURDLE",
      "funding_time_ms":tm,"funding_rate":s(dec(fr["fundingRate"])),
      "one_funding_predicted_gross_bps":s(funding),
      "roundtrip_hypothetical_fees_bps":s(ROUNDTRIP_FEES_BPS),
      "stress_hypothetical_fees_bps":s(STRESS_FEES_BPS),
      "book_roundtrip_unchanged_proxy_bps":s(spread),
      "8h_net_estimate_bps":s(eight),"8h_stress_estimate_bps":s(stress),
      "24h_if_funding_constant_DIAGNOSTIC_bps":s(sensitivity24),
      "7d_if_funding_constant_DIAGNOSTIC_bps":s(sensitivity7d),
      "entry_basis_perp_bid_minus_spot_ask_bps":s(basis),
      "spot_bid":s(spot["bid"]),"spot_ask":s(spot["ask"]),
      "perp_bid":s(perp["bid"]),"perp_ask":s(perp["ask"]),
      "spot_min_base":s(spot_min),"perp_min_contracts":s(swap_min),
      "perp_contract_base_value":s(ctval*ctmult),
      "min_hedge_base_lower_bound":s(min_qty),
      "min_spot_capital_USDT_floor":s(min_spot_usdt),
      "top_bid_ask_depth_limited":True,
      "profit_usdt":None,"trade_fills":0,
      "not_certified":["account_eligibility_CH","real_fee_tier","lot_matched_fills",
                       "future_funding","future_exit_bbo","basis_drift",
                       "real_capital_and_margin","liquidation","tail_risk",
                       "USDT_EUR_CHF_fx","net_economic_edge"]
    }

def get(base, params, rawdir, label):
    url=base+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Research-ReadOnly/1.0","Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=8) as resp:
        if resp.status != 200: raise ValueError("HTTP_STATUS_NOT_200")
        body=resp.read(1048577)
    if len(body)>1048576: raise ValueError("SOURCE_TOO_LARGE")
    payload=json.loads(body)
    if str(payload.get("code"))!="0":raise ValueError("EXCHANGE_RESPONSE_NOT_OK")
    (rawdir/(label+".json")).write_bytes(body)
    return payload, hashlib.sha256(body).hexdigest()

def run(output):
    raw=pathlib.Path(output)
    raw.mkdir(parents=True,exist_ok=True)
    start=int(time.time()*1000)
    receipt={"freeze":"PRE_SOURCE_ECONOMIC_FREEZE_2026_10_20",
             "observed_start_utc":dt.datetime.fromtimestamp(start/1000,dt.timezone.utc).isoformat(),
             "read_only":True,"account_reads":0,"orders":0,"actual_pnl":None,"edge_proven":False,
             "results":[],"http_receipts":[]}
    for asset in ASSETS:
        sp,sw=f"{asset}-USDT",f"{asset}-USDT-SWAP"
        reqs={
          "spot_info":("/api/v5/public/instruments",{"instType":"SPOT","instId":sp}),
          "swap_info":("/api/v5/public/instruments",{"instType":"SWAP","instId":sw}),
          "spot_book":("/api/v5/market/books",{"instId":sp,"sz":5}),
          "swap_book":("/api/v5/market/books",{"instId":sw,"sz":5}),
          "swap_funding":("/api/v5/public/funding-rate",{"instId":sw})
        }
        data={}
        for name,(uri,params) in reqs.items():
            try:
                packet,sha=get("https://www.okx.com"+uri,params,raw,asset+"_"+name)
                data[name]=packet
                receipt["http_receipts"].append({"asset":asset,"source":name,"result":"OK","sha256":sha})
            except Exception as exc:
                receipt["http_receipts"].append({"asset":asset,"source":name,
                                                 "result":"SOURCE_BLOCKED","error":str(exc)[:180]})
                break
        if len(data)!=len(reqs):
            receipt["results"].append({"asset":asset,"verdict":"SOURCE_BLOCKED"})
            continue
        try:
            now=int(time.time()*1000)
            if now-start>MAX_WINDOW_MS:raise ValueError("SOURCE_WINDOW_EXCEEDED_30S")
            receipt["results"].append(pair(asset,data,now))
        except Exception as exc:
            receipt["results"].append({"asset":asset,"verdict":"SOURCE_BLOCKED","error":str(exc)[:180]})
    receipt["finished_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    receipt["source_valid_pairs"]=sum(x["verdict"].startswith("8H_") for x in receipt["results"])
    receipt["positive_eight_hour_screens"]=sum(x["verdict"]=="8H_ESTIMATE_COVERS_FROZEN_HURDLE_NOT_EDGE" for x in receipt["results"])
    (raw/"derived_result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("CARRY_FROZEN_SOURCE_RECEIPT="+json.dumps(receipt,sort_keys=True))
    return receipt

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="okx_carry_source_receipt")
    run(ap.parse_args().out)

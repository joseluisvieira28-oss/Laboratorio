#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, math, pathlib, urllib.parse, urllib.request

BASE="https://www.deribit.com/api/v2"
OUT=pathlib.Path("artifacts/btc_options_vrp_linear_usdc_probe")
DTE_MIN=14.0
DTE_MAX=60.0
TARGET_DTE=30.0
MIN_AMOUNT=0.01

def now_utc():
    return dt.datetime.now(dt.timezone.utc)

def api_get(method, params):
    url=f"{BASE}/{method}?{urllib.parse.urlencode(params)}"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-V2-USDC-SourceOnly/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        obj=json.loads(r.read().decode("utf-8"))
    if "error" in obj:
        raise RuntimeError(f"{method}: {obj['error']}")
    return obj["result"]

def first(book, side):
    rows=book.get(side) or []
    if not rows: return (None,None)
    return float(rows[0][0]), float(rows[0][1])

def book(name):
    b=api_get("public/get_order_book",{"instrument_name":name,"depth":1})
    bid,bid_amt=first(b,"bids"); ask,ask_amt=first(b,"asks")
    return {
        "instrument_name":name,
        "bid_price":bid,"bid_amount":bid_amt,
        "ask_price":ask,"ask_amount":ask_amt,
        "mark_price":b.get("mark_price"),
        "mark_iv":b.get("mark_iv"),
        "bid_iv":b.get("bid_iv"),
        "ask_iv":b.get("ask_iv"),
        "index_price":b.get("index_price"),
        "underlying_price":b.get("underlying_price"),
        "source_timestamp_ms":b.get("timestamp"),
        "greeks":b.get("greeks"),
    }

def main():
    now=now_utc(); now_ms=int(now.timestamp()*1000)
    idx=api_get("public/get_index_price",{"index_name":"btc_usdc"})
    index=float(idx["index_price"])
    insts=api_get("public/get_instruments",{"currency":"USDC","kind":"option","expired":"false"})
    btc=[x for x in insts if str(x.get("instrument_name","")).startswith("BTC_USDC-")]
    pairs={}
    for x in btc:
        exp=x.get("expiration_timestamp"); strike=x.get("strike"); typ=x.get("option_type")
        if exp is None or strike is None or typ not in {"call","put"}: continue
        dte=(float(exp)-now_ms)/86_400_000
        if not (DTE_MIN<=dte<=DTE_MAX): continue
        pairs.setdefault((int(exp),float(strike)),{})[typ]=x
    cands=[]
    for (exp,strike),legs in pairs.items():
        if "call" not in legs or "put" not in legs: continue
        dte=(exp-now_ms)/86_400_000
        cands.append((abs(dte-TARGET_DTE),exp,abs(math.log(strike/index)),strike,dte,legs))
    cands.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    if not cands:
        result={
          "classification":"SOURCE_ACCESSIBILITY_BLOCKED_NO_PAIR",
          "observed_at_utc":now.isoformat(),"btc_usdc_instrument_count":len(btc),
          "returns_computed":False,"pnl_computed":False,"authenticated":False,"orders":False
        }
    else:
        _,exp,_,strike,dte,legs=cands[0]
        cb=book(legs["call"]["instrument_name"]); pb=book(legs["put"]["instrument_name"])
        perp=None
        try: perp=book("BTC_USDC-PERPETUAL")
        except Exception as e: perp={"error":str(e)}
        cmin=float(legs["call"].get("min_trade_amount") or 0)
        pmin=float(legs["put"].get("min_trade_amount") or 0)
        ccs=legs["call"].get("contract_size"); pcs=legs["put"].get("contract_size")
        # Official BTC_USDC Standard Margin formulas, source-only estimate.
        under=float(cb.get("underlying_price") or cb.get("index_price") or index)
        cidx=float(cb.get("index_price") or index); pidx=float(pb.get("index_price") or index)
        cmark=float(cb.get("mark_price") or 0); pmark=float(pb.get("mark_price") or 0)
        call_otm=max(strike-under,0.0)
        put_otm=max(under-strike,0.0)
        call_im_per=max(0.15-call_otm/under,0.10)*cidx+cmark
        put_im_per=max((0.15-put_otm/under)*pidx,0.10*strike)+pmark
        call_im=call_im_per*MIN_AMOUNT
        put_im=put_im_per*MIN_AMOUNT
        source_ok=all([
          cb["bid_price"] is not None, cb["ask_price"] is not None,
          pb["bid_price"] is not None, pb["ask_price"] is not None,
          cb["bid_amount"] is not None and cb["bid_amount"]>=MIN_AMOUNT,
          pb["bid_amount"] is not None and pb["bid_amount"]>=MIN_AMOUNT,
          cmin>0 and cmin<=MIN_AMOUNT, pmin>0 and pmin<=MIN_AMOUNT,
          cb["source_timestamp_ms"] is not None, pb["source_timestamp_ms"] is not None,
        ])
        result={
          "classification":"SOURCE_ACCESSIBILITY_PASS" if source_ok else "SOURCE_ACCESSIBILITY_BLOCKED",
          "observed_at_utc":now.isoformat(),
          "index_price_btc_usdc":index,
          "btc_usdc_instrument_count":len(btc),
          "candidate_pair_count":len(cands),
          "selection":{"dte_days":dte,"expiration_timestamp":exp,"strike":strike},
          "call_instrument_meta":{
            "instrument_name":legs["call"]["instrument_name"],
            "min_trade_amount":cmin,"contract_size":ccs
          },
          "put_instrument_meta":{
            "instrument_name":legs["put"]["instrument_name"],
            "min_trade_amount":pmin,"contract_size":pcs
          },
          "call_book":cb,"put_book":pb,"perpetual_book":perp,
          "standard_margin_estimate_usdc":{
             "amount_each_leg":MIN_AMOUNT,
             "call_initial_margin_usdc":call_im,
             "put_initial_margin_usdc":put_im,
             "pair_initial_margin_usdc":call_im+put_im
          },
          "returns_computed":False,"pnl_computed":False,
          "authenticated":False,"orders":False,"wallets":False
        }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["classification"]!="SOURCE_ACCESSIBILITY_PASS":
        raise SystemExit(2)

if __name__=="__main__":
    main()

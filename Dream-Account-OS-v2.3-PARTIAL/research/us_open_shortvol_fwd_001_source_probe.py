#!/usr/bin/env python3
import json, math, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE="https://www.deribit.com/api/v2"
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usopen_shortvol_fwd_001_source_probe.json")

def call(method, params):
    q=urllib.parse.urlencode(params)
    url=f"{BASE}/{method}?{q}"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-USOPEN-SHORTVOL-FWD-001/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        x=json.loads(r.read().decode())
    if "error" in x:
        raise RuntimeError(x["error"])
    return x["result"]

def main():
    now=datetime.now(timezone.utc)
    idx=call("public/get_index_price",{"index_name":"btc_usd"})
    index=float(idx["index_price"])
    instruments=call("public/get_instruments",{"currency":"BTC","kind":"option","expired":"false"})

    rows=[]
    for x in instruments:
        exp=datetime.fromtimestamp(x["expiration_timestamp"]/1000,tz=timezone.utc)
        dte=(exp-now).total_seconds()/86400
        if not (7<=dte<=14): continue
        name=x["instrument_name"]
        parts=name.split("-")
        if len(parts)<4: continue
        try: strike=float(parts[-2])
        except: continue
        right=parts[-1]
        if right not in ("C","P"): continue
        rows.append({"name":name,"expiration_timestamp":x["expiration_timestamp"],"expiry":exp.isoformat(),"dte":dte,"strike":strike,"right":right})

    if not rows:
        result={"classification":"SOURCE_BLOCKED_NO_7_14_DTE_INSTRUMENTS","now_utc":now.isoformat(),"index_name":"btc_usd","index_price_observed":True}
    else:
        nearest=min(x["expiration_timestamp"] for x in rows)
        rs=[x for x in rows if x["expiration_timestamp"]==nearest]
        pairs={}
        for x in rs:
            pairs.setdefault(x["strike"],{})[x["right"]]=x
        pairlist=[]
        for k,v in pairs.items():
            if "C" in v and "P" in v:
                pairlist.append((abs(math.log(k/index)),k,v["C"],v["P"]))
        if not pairlist:
            result={"classification":"SOURCE_BLOCKED_NO_ATM_PAIR","now_utc":now.isoformat(),"eligible_instruments":len(rows)}
        else:
            pairlist.sort(key=lambda z:(z[0],z[1]))
            _,strike,call_i,put_i=pairlist[0]
            books={}
            for label,ins in [("call",call_i),("put",put_i)]:
                b=call("public/get_order_book",{"instrument_name":ins["name"],"depth":5})
                books[label]={
                    "instrument_name":ins["name"],
                    "best_bid_price_present":b.get("best_bid_price") is not None,
                    "best_ask_price_present":b.get("best_ask_price") is not None,
                    "best_bid_amount":b.get("best_bid_amount"),
                    "best_ask_amount":b.get("best_ask_amount"),
                    "timestamp":b.get("timestamp")
                }
            pass_bbo=all(
                books[k]["best_bid_price_present"] and books[k]["best_ask_price_present"] and
                (books[k]["best_bid_amount"] or 0)>=0.1 and (books[k]["best_ask_amount"] or 0)>=0.1
                for k in ("call","put")
            )
            result={
                "classification":"PUBLIC_BBO_SIZE_SOURCE_PASS" if pass_bbo else "PUBLIC_BBO_SIZE_SOURCE_INSUFFICIENT",
                "now_utc":now.isoformat(),
                "index_name":"btc_usd",
                "index_price_observed":True,
                "eligible_7_14_dte_instruments":len(rows),
                "nearest_expiry":call_i["expiry"],
                "nearest_expiry_dte":call_i["dte"],
                "atm_pair_strike":strike,
                "call":books["call"],
                "put":books["put"],
                "required_amount_per_leg":0.1,
                "private_endpoint_used":False,
                "order_endpoint_used":False,
                "pnl_computed":False,
                "return_computed":False
            }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()

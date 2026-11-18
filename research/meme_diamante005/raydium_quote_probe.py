#!/usr/bin/env python3
"""MEME005: quote-only Raydium router probe. NEVER signs, sends, or buys."""
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import sys

RAY="https://transaction-v1.raydium.io/compute/swap-base-in"
WSOL="So11111111111111111111111111111111111111112"
AMOUNT_LAMPORTS=50000000 # 0.05 SOL
UA="CryptoLab-005-Research-Quote-Only/1.0"
def utc():return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")
def quote(input_mint,output_mint,amount):
    args={"inputMint":input_mint,"outputMint":output_mint,
          "amount":str(amount),"slippageBps":"50","txVersion":"V0"}
    url=RAY+"?"+urllib.parse.urlencode(args)
    started=utc(); st=time.monotonic();status=None;err=None;payload=None;raw=None
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"},method="GET")
        with urllib.request.urlopen(req,timeout=20) as resp:
            status=resp.status;raw=resp.read(1500000)
        payload=json.loads(raw)
    except urllib.error.HTTPError as exc:
        status=exc.code;err="HTTP_"+str(exc.code)
    except (OSError,UnicodeDecodeError,ValueError) as exc:
        err=type(exc).__name__+":"+str(exc)[:130]
    receipt=dict(started_at=started,received_at=utc(),elapsed_ms=round(1000*(time.monotonic()-st)),
                 url=url,http_status=status,error=err,body_sha256=hashlib.sha256(raw).hexdigest() if raw else None)
    data=(payload or {}).get("data") if isinstance(payload,dict) else None
    if not isinstance(data,dict) or payload.get("success") is not True:
        return None,receipt
    result=dict(inputAmount=data.get("inputAmount"),outputAmount=data.get("outputAmount"),
                otherAmountThreshold=data.get("otherAmountThreshold"),slippageBps=data.get("slippageBps"),
                priceImpactPct=data.get("priceImpactPct"),
                routePools=[p.get("poolId") for p in (data.get("routePlan") or []) if isinstance(p,dict)])
    return result,receipt

def int_amt(x):
    try:
        v=int(x)
        return v if v>0 else None
    except (TypeError,ValueError):return None

def probe(previous):
    rows=[];receipts=[]
    for src in previous.get("selection") or []:
        if (src.get("screen") or {}).get("status")!="SCREEN_PASS_ONLY":continue
        mint=src.get("mint")
        if not mint:continue
        obj=dict(coingecko_id=src.get("coingecko_id"),mint=mint,status="UNKNOWN",size_sol=.05,
                 quotes=[],"instant_roundtrip_cost_pct":None,"worse_threshold_cost_pct":None)
        rows.append(obj)
        buy,r=quote(WSOL,mint,AMOUNT_LAMPORTS)
        receipts.append(dict(coin_id=src.get("coingecko_id"),direction="buy",**r))
        if not buy:
            obj["status"]="QUOTE_BUY_BLOCKED";continue
        obj["quotes"].append(dict(direction="SOL_TO_TOKEN",**buy))
        optimistic_tokens=int_amt(buy.get("outputAmount"))
        pessimistic_tokens=int_amt(buy.get("otherAmountThreshold"))
        if not optimistic_tokens:
            obj["status"]="QUOTE_BUY_INVALID";continue
        time.sleep(.4)
        sell,rr=quote(mint,WSOL,optimistic_tokens)
        receipts.append(dict(coin_id=src.get("coingecko_id"),direction="sell_expected",**rr))
        if sell:
            obj["quotes"].append(dict(direction="TOKEN_TO_SOL_AT_EXPECTED_TOKENS",**sell))
            sol_back=int_amt(sell.get("outputAmount"))
            if sol_back:
                obj["instant_roundtrip_cost_pct"]=round(100*(1-sol_back/AMOUNT_LAMPORTS),5)
        if pessimistic_tokens:
            time.sleep(.4)
            sell_stress,rs=quote(mint,WSOL,pessimistic_tokens)
            receipts.append(dict(coin_id=src.get("coingecko_id"),direction="sell_min_token_amount",**rs))
            if sell_stress:
                obj["quotes"].append(dict(direction="TOKEN_TO_SOL_AT_MIN_TOKENS",**sell_stress))
                sol_threshold=int_amt(sell_stress.get("otherAmountThreshold"))
                if sol_threshold:
                    obj["worse_threshold_cost_pct"]=round(100*(1-sol_threshold/AMOUNT_LAMPORTS),5)
        obj["status"]="COST_PROXIES_ONLY" if obj["instant_roundtrip_cost_pct"] is not None else "SELL_QUOTE_UNAVAILABLE"
    return dict(protocol="MEME005-ROUTER-QUOTE-ONLY-v0.1",
        snapshot_ref_sha256=hashlib.sha256(json.dumps(previous,sort_keys=True,ensure_ascii=False,indent=2).encode()).hexdigest(),
        started_at=utc(),quote_rows=rows,receipts=receipts,quote_count=len(rows),
        no_key=True,no_wallet=True,no_signing=True,no_orders=True,
        scientific_gate="NOT A FORWARD PROSPECTIVE TEST",
        economic_gate="NO-GO: two sequential indicative router quotes are not executable matched fills; base fees, priority, latency, MEV, failures and token inventories unverified")

def main():
    p=pathlib.Path(sys.argv[1])
    prior=json.loads(p.read_text(encoding="utf-8"))
    result=probe(prior)
    out=pathlib.Path("meme005-quote-evidence")
    out.mkdir(exist_ok=True)
    raw=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False).encode()
    (out/"quote_receipts.json").write_bytes(raw)
    (out/"quote_receipts.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  quote_receipts.json\n")
    print("MEME005_QUOTES="+json.dumps({"rows":[{k:v for k,v in x.items() if k in ("coingecko_id","status","instant_roundtrip_cost_pct","worse_threshold_cost_pct")} for x in result["quote_rows"]],
         "receipts":len(result["receipts"]),"report_sha256":hashlib.sha256(raw).hexdigest(),
         "economic_gate":"NO-GO","orders":0}))
if __name__=="__main__":main()

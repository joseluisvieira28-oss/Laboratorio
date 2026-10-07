#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, json, math, pathlib, urllib.parse, urllib.request

BASE="https://www.deribit.com/api/v2"
OUT=pathlib.Path("data/vrp_usdc_forward/entry_source_bank.jsonl")
RECEIPT_DIR=pathlib.Path("receipts/vrp_usdc_forward")
AMOUNT=0.01
FRESH_MS=30_000

def now(): return dt.datetime.now(dt.timezone.utc)
def ms(x): return int(x.timestamp()*1000)

def api(method,params):
    t0=now()
    url=f"{BASE}/{method}?{urllib.parse.urlencode(params)}"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-USDC-ForwardBank/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        obj=json.loads(r.read().decode("utf-8"))
    t1=now()
    if "error" in obj: raise RuntimeError(f"{method}: {obj['error']}")
    return obj["result"],ms(t0),ms(t1)

def top(book,side):
    rows=book.get(side) or []
    if not rows:return None,None
    return float(rows[0][0]),float(rows[0][1])

def capture_book(name):
    b,t0,t1=api("public/get_order_book",{"instrument_name":name,"depth":1})
    bid,bids=top(b,"bids"); ask,asks=top(b,"asks")
    src=b.get("timestamp")
    return {
      "instrument_name":name,
      "request_start_ms":t0,"response_received_ms":t1,"source_timestamp_ms":src,
      "fresh_30s":src is not None and abs(t1-int(src))<=FRESH_MS,
      "bid_price":bid,"bid_amount":bids,"ask_price":ask,"ask_amount":asks,
      "bid_iv":b.get("bid_iv"),"ask_iv":b.get("ask_iv"),"mark_iv":b.get("mark_iv"),
      "mark_price":b.get("mark_price"),"index_price":b.get("index_price"),
      "underlying_price":b.get("underlying_price"),"greeks":b.get("greeks"),
      "open_interest":b.get("open_interest")
    }

def existing_dates():
    if not OUT.exists():return set()
    dates=set()
    for line in OUT.read_text(encoding="utf-8").splitlines():
        if not line.strip():continue
        x=json.loads(line); dates.add(x["capture_date_utc"])
    return dates

def main():
    t=now()
    if t.weekday()!=3 or not (t.hour==8 and 0<=t.minute<=15):
        raise SystemExit(f"OUTSIDE_FROZEN_WINDOW {t.isoformat()}")
    day=t.date().isoformat()
    if day in existing_dates():
        raise SystemExit(f"DUPLICATE_CAPTURE_DATE {day}")

    idx,_,_=api("public/get_index_price",{"index_name":"btc_usdc"})
    index=float(idx["index_price"])
    insts,_,_=api("public/get_instruments",{"currency":"USDC","kind":"option","expired":"false"})
    pairs={}
    tms=ms(t)
    for x in insts:
        name=str(x.get("instrument_name",""))
        if not name.startswith("BTC_USDC-") or not x.get("is_active",True):continue
        exp=x.get("expiration_timestamp"); strike=x.get("strike"); typ=x.get("option_type")
        if exp is None or strike is None or typ not in {"call","put"}:continue
        dte=(float(exp)-tms)/86_400_000
        if not (14<=dte<=60):continue
        pairs.setdefault((int(exp),float(strike)),{})[typ]=x
    cands=[]
    for (exp,k),legs in pairs.items():
        if "call" not in legs or "put" not in legs:continue
        dte=(exp-tms)/86_400_000
        cands.append((abs(dte-30),exp,abs(math.log(k/index)),k,dte,legs))
    if not cands: raise RuntimeError("NO_FROZEN_PAIR")
    cands.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    _,exp,_,strike,dte,legs=cands[0]
    call=capture_book(legs["call"]["instrument_name"])
    put=capture_book(legs["put"]["instrument_name"])
    perp=capture_book("BTC_USDC-PERPETUAL")
    valid=all([
      call["fresh_30s"],put["fresh_30s"],perp["fresh_30s"],
      call["bid_price"] is not None,put["bid_price"] is not None,
      call["bid_amount"] is not None and call["bid_amount"]>=AMOUNT,
      put["bid_amount"] is not None and put["bid_amount"]>=AMOUNT,
    ])
    rec={
      "schema_version":"BTC_VRP_USDC_FORWARD_ENTRY_SOURCE_V0.1",
      "capture_date_utc":day,"captured_at_utc":t.isoformat(),
      "index_price_btc_usdc":index,
      "selection":{"expiration_timestamp":exp,"dte_days":dte,"strike":strike,
                   "call_instrument":legs["call"]["instrument_name"],"put_instrument":legs["put"]["instrument_name"],
                   "amount_each_leg":AMOUNT},
      "call":call,"put":put,"btc_usdc_perpetual":perp,
      "source_valid":valid,
      "settlement_fetched":False,"future_path_fetched":False,
      "returns_computed":False,"pnl_computed":False,"expectancy_computed":False,
      "authenticated":False,"orders":False,"wallets":False
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("a",encoding="utf-8") as f:f.write(json.dumps(rec,sort_keys=True,separators=(",",":"))+"\n")
    RECEIPT_DIR.mkdir(parents=True,exist_ok=True)
    summary={"date":day,"source_valid":valid,"dte_days":dte,"strike":strike,
             "call_bid_amount":call["bid_amount"],"put_bid_amount":put["bid_amount"],
             "settlement_fetched":False,"returns_computed":False,"pnl_computed":False}
    (RECEIPT_DIR/f"{day}.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True))
    if not valid: raise SystemExit(2)

if __name__=="__main__":main()

#!/usr/bin/env python3
"""CARRY-002: ONE read-only live ETH book snapshot; NO ORDERS, funds or accounts.
Never treats a single book as historical fill evidence or valid bilateral execution.
Binance restriction 451 must not be routed around via proxy/VPN/alternate hosts.
"""
import datetime as dt,hashlib,json,pathlib,time,urllib.request,urllib.error
OUT=pathlib.Path("carry002-evidence");OUT.mkdir(exist_ok=True)
UA="CryptoLab-CARRY002/0.1 (read-only; no credentials)"
def pull(url,body=None):
    data=json.dumps(body,separators=(",",":")).encode() if body else None
    req=urllib.request.Request(url,data=data,headers={
      "User-Agent":UA,"Accept":"application/json",
      "Content-Type":"application/json" if data else "text/plain"})
    start=time.monotonic(); t1=dt.datetime.now(dt.timezone.utc).isoformat()
    result={"url":url,"request":body,"requested_at_utc":t1,
      "received_at_utc":None,"http_status":None,"sha256":None,"error":None}
    try:
        with urllib.request.urlopen(req,timeout=20) as res:
            raw=res.read(250000)
            result["http_status"]=res.status
            result["sha256"]=hashlib.sha256(raw).hexdigest()
            result["body"]=json.loads(raw)
    except urllib.error.HTTPError as e:
        result["http_status"]=e.code
        result["error"]="HTTP "+str(e.code)
    except Exception as e:
        result["error"]=type(e).__name__+": "+str(e)[:200]
    result["received_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    result["elapsed_ms"]=round((time.monotonic()-start)*1000,1)
    return result
def walk(levels, dollars, buying):
    if not levels:return {"filled":False,"quoted_depth":"missing"}
    top=float(levels[0]["px"]);best=top
    rem=float(dollars)/top
    amount=0;paid=0
    for row in levels:
        price=float(row["px"]);sz=float(row["sz"])
        if price<=0 or sz<=0:continue
        qty=min(rem,sz)
        paid+=qty*price;amount+=qty;rem-=qty
        if rem<1e-9:break
    if rem>1e-9:return {"filled":False,"remaining_eth":rem,"top_price":best}
    avg=paid/amount
    slip=10000*((avg/best-1) if buying else (1-avg/best))
    return {"filled":True,"qty_eth":round(amount,8),
       "avg_price":round(avg,7),"best_price":best,
       "impact_bps":round(slip,4),
       "NO_EXECUTION":"snapshot-only and no fee/latency/guaranteed price"}
def run():
    hl=pull("https://api.hyperliquid.xyz/info",{"type":"l2Book","coin":"ETH"})
    bn=pull("https://fapi.binance.com/fapi/v1/depth?symbol=ETHUSDT&limit=100")
    outcome={"version":"CARRY-002.1","as_of":dt.datetime.now(dt.timezone.utc).isoformat(),
      "orders_sent":0,"tradeable_cross_venue":False,
      "data":{"hyperliquid":hl,"binance":bn},"hyperliquid_quote_depth":{},
      "status":"NO-GO: cannot assume an executable two-venue order"}
    book=hl.get("body") or {}
    levels=book.get("levels") or []
    if len(levels)==2 and isinstance(levels[0],list) and isinstance(levels[1],list):
        outcome["hyperliquid_book_time_ms"]=book.get("time")
        for usdc in [250,1000,5000]:
            outcome["hyperliquid_quote_depth"][str(usdc)]={
              "buy":walk(levels[1],usdc,True),"sell":walk(levels[0],usdc,False)}
    if bn["http_status"]==451:outcome["binance_blocker"]="HTTP_451_RESTRICTED; no circumvention"
    if hl["http_status"]==200 and bn["http_status"]==200:
        outcome["status"]="ONE_TIMESTAMP_DIAGNOSTIC_ONLY: not synchronized or historical, execution still NO-GO"
    raw=json.dumps(outcome,indent=2,ensure_ascii=False,sort_keys=True).encode()
    (OUT/"book_probe.json").write_bytes(raw)
    (OUT/"book_probe.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  book_probe.json\n")
    print("BOOK_PROBE",json.dumps({"hl_status":hl["http_status"],"binance_status":bn["http_status"],
      "quotes":outcome["hyperliquid_quote_depth"],"verdict":outcome["status"]},ensure_ascii=False),flush=True)
if __name__=="__main__":run()

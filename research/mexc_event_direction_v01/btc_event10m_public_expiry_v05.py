#!/usr/bin/env python3
"""BTC 10m read-only PUBLIC INDEX expiry shadow, only after independent preexpiry custody."""
import argparse,asyncio,hashlib,json,math,pathlib,time
import websockets
OUT=pathlib.Path("artifacts/btc_event10m_paper_v05")
def ms():return int(time.time()*1000)
def check_before_expiry(obj,anchor,now):
    f=obj.get("forecast") or {}
    if obj.get("study")!="BTC_EVENT10M_V05_FROZEN_PROSPECTIVE_PAPER_ONLY" or obj.get("status")!="PAPER_FORECAST_UNANCHORED" or f.get("side") not in ("UP","DOWN"):
        raise ValueError("NO_FROZEN_QUALIFIED_DIRECTION")
    if anchor.get("status")!="GITHUB_SERVER_ARCHIVE_VERIFIED" or anchor.get("independent_custody_proven") is not True or anchor.get("repo")!="joseluisvieira28-oss/Laboratorio":
        raise ValueError("NO_AUTHENTICATED_SERVER_ARTIFACT")
    d=f.get("decision_ms");target=f.get("target_ms")
    if type(d)!=int or type(target)!=int or target!=d+600000 or anchor.get("decision_ms")!=d or anchor.get("expiry_target_ms")!=target:
        raise ValueError("BAD_FROZEN_10M_CLOCK")
    if not d-1000<=anchor.get("artifact_created_ms",0)<target or not d<=now<target:
        raise ValueError("POST_OUTCOME_OR_UNPUBLISHED_CUSTODY")
    return target
def score_index_shadow(obj,tick):
    target=obj["forecast"]["target_ms"];srv=tick.get("server_ms");recv=tick.get("received_ms")
    if tick.get("symbol")!="BTC_USDT" or type(srv)!=int or type(recv)!=int or not(target<=srv<=target+5000 and srv<=recv<=srv+5000):
        raise ValueError("NO_FIRST_VALID_EXACT_EXPIRY_INDEX_TICK")
    price=float(tick.get("index_price"));entry=float(obj["source_receipt"]["index"]["index_price"])
    if not(math.isfinite(price) and price>0 and math.isfinite(entry) and entry>0):
        raise ValueError("BAD_PUBLIC_INDEX_PRICES")
    side=obj["forecast"]["side"];q=obj["forecast"]["side_payout"]
    if not isinstance(q,(float,int)) or not math.isfinite(q) or q<=0:raise ValueError("INVALID_OBSERVED_PAYOUT")
    res="TIE" if price==entry else ("WIN" if (price>entry)==(side=="UP") else "LOSS")
    return {"study":"BTC_EVENT10M_INDEX_SHADOW_ONLY_V05","side":side,
        "index_start":entry,"index_at_expiry":price,"proxy_result":res,
        "hypothetical_q_unit_payoff":0 if res=="TIE" else (q if res=="WIN" else -1),
        "event_futures_actual_server_price_parity_proven":False,
        "event_futures_realized_PnL":None,"trades":0,
        "verdict":"INDEX_SHADOW_ONLY__NOT_ECONOMIC_GO"}
async def tick_at_target(target):
    async with websockets.connect("wss://futures.mexc.com/edge",origin="https://www.mexc.com",
       open_timeout=20,ping_interval=15,ping_timeout=10,max_size=2000000) as ws:
        await ws.send(json.dumps({"method":"sub.index.price","param":{"symbol":"BTC_USDT"}}))
        while ms()<=target+5000:
            try:raw=await asyncio.wait_for(ws.recv(),timeout=min(4,max(.1,(target+5000-ms())/1000)))
            except asyncio.TimeoutError:continue
            if not isinstance(raw,str):continue
            try:msg=json.loads(raw)
            except Exception:continue
            data=msg.get("data") or {}
            if msg.get("channel")!="push.index.price" or (msg.get("symbol") or data.get("symbol"))!="BTC_USDT":continue
            ts=msg.get("ts")
            if type(ts)!=int or ts<target:continue
            rec=ms();path=OUT/"btc_index_expiry_raw.json";path.write_bytes(raw.encode())
            return {"symbol":"BTC_USDT","server_ms":ts,"received_ms":rec,
                "index_price":data.get("price"),"sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "raw_file":path.name}
    raise ValueError("NO_PUBLIC_INDEX_TICK_WITHIN_5_SECONDS")
async def main():
    p=argparse.ArgumentParser()
    p.add_argument("--decision",required=True);p.add_argument("--anchor",required=True)
    args=p.parse_args();OUT.mkdir(exist_ok=True,parents=True)
    out={"status":"BLOCKED","study":"BTC_EVENT10M_PROSPECTIVE_INDEX_SHADOW_V05",
         "orders":0,"accounts":0,"actual_event_futures_fill_parity":False}
    try:
        obj=json.loads(pathlib.Path(args.decision).read_bytes())
        anchor=json.loads(pathlib.Path(args.anchor).read_bytes())
        target=check_before_expiry(obj,anchor,ms())
        tick=await tick_at_target(target)
        out["index_tick"]=tick
        out["shadow"]=score_index_shadow(obj,tick)
        out["status"]="INDEX_SHADOW_ONLY_RESOLVED"
    except Exception as e:out["error"]=type(e).__name__+":"+str(e)[:200]
    (OUT/"expiry_shadow.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="shadow"},indent=2))
    if out["status"]!="INDEX_SHADOW_ONLY_RESOLVED":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())

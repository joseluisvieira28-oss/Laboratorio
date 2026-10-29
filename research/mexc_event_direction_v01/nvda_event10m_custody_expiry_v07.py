#!/usr/bin/env python3
"""Public index ONLY: strict 10m expiry watcher after independently verified artifact."""
import argparse,asyncio,hashlib,json,math,pathlib,time
import websockets
from nvda_event10m_expiry_shadow_v06 import settle,digest
OUT=pathlib.Path("artifacts/nvda_event10m_custody_v07")
def ms():return int(time.time()*1000)
def validate_before_outcome(decision,anchor):
    model=decision.get("forecast") or {}
    if model.get("candidate") not in ("UP","DOWN"):
        raise ValueError("NO_DIRECTIONAL_SIGNAL_TO_SETTLE")
    if decision.get("status")!="PAPER_FORECAST_UNANCHORED_NOT_EVENT_FUTURES_EXECUTION":
        raise ValueError("DECISION_NOT_APPROVED_SHADOW")
    if anchor.get("anchor_protocol")!="GITHUB_API_ZIP_BYTE_CUSTODY_V07" or anchor.get("custody_independently_authenticated") is not True:
        raise ValueError("ANCHOR_NOT_GITHUB_VERIFIED")
    if anchor.get("decision_canonical_sha256")!=digest(decision):
        raise ValueError("DECISION_MUTATION_AFTER_ANCHOR")
    d=int(model["decision_ts_ms"]);target=int(model["expiry_target_ms"])
    if target!=d+600000 or anchor.get("expiry_target_ms")!=target:
        raise ValueError("INVALID_10M_TARGET")
    if not (d-1000<=anchor.get("published_ms",0)<target):
        raise ValueError("NO_PRE_EXPIRY_CUSTODY")
    if anchor.get("github_repository")!="joseluisvieira28-oss/Laboratorio":
        raise ValueError("BAD_CUSTODY_REPOSITORY")
    now=ms()
    if now>=target:
        raise ValueError("PRE_EXPIRY_WATCH_NOT_STARTED_IN_TIME")
    return target

async def collect_tick(target):
    first=None
    async with websockets.connect("wss://futures.mexc.com/edge",
        origin="https://www.mexc.com",open_timeout=20,ping_interval=15,
        ping_timeout=10,max_size=2_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.index.price",
             "param":{"symbol":"NVIDIA_USDT"}},separators=(",",":")))
        while ms()<=target+5000:
            remain=(target+5000-ms())/1000
            if remain<=0:break
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=min(max(.1,remain),4))
            except asyncio.TimeoutError:continue
            if not isinstance(raw,str):continue
            try:msg=json.loads(raw)
            except Exception:continue
            if not isinstance(msg,dict) or msg.get("channel")!="push.index.price":continue
            data=msg.get("data") or {}
            sym=msg.get("symbol") or data.get("symbol")
            if sym!="NVIDIA_USDT":continue
            server_ts=msg.get("ts")
            if type(server_ts) is not int or server_ts<target:continue
            # First at/after target, no nearest-bar or alternate tick substitution.
            first={"symbol":"NVIDIA_USDT","server_ts_ms":server_ts,
                   "received_ms":ms(),"index_price":data.get("price"),
                   "raw_sha256":hashlib.sha256(raw.encode()).hexdigest()}
            break
    if first is None:raise ValueError("NO_EXPIRY_TICK_IN_5_SECONDS")
    return first

async def main(args):
    OUT.mkdir(parents=True,exist_ok=True)
    rep={"study":"NVDA_EVENT10M_CUSTODY_INDEX_SHADOW_V07","status":"BLOCKED",
         "orders":0,"account_reads":0,"authenticated_exchange_endpoints":0,
         "real_event_futures_settlement_parity_proven":False}
    try:
        raw=pathlib.Path(args.decision).read_bytes()
        decision=json.loads(raw)
        anchor=json.loads(pathlib.Path(args.anchor).read_bytes())
        target=validate_before_outcome(decision,anchor)
        tick=await collect_tick(target)
        rep["expiry_tick"]=tick
        shadow=settle(decision,anchor,tick)
        shadow["custody_independently_authenticated"]=True
        shadow["actual_event_futures_fill_parity_proven"]=False
        shadow["verdict"]="INDEPENDENT_CUSTODY_INDEX_SHADOW_ONLY__NO_REAL_EVENT_PNL"
        rep["shadow"]=shadow
        rep["status"]="INDEX_SHADOW_ONLY_RESOLVED"
    except Exception as exc:
        rep["failure"]=type(exc).__name__+":"+str(exc)[:190]
    (OUT/"expiry_receipt.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in rep.items() if k!="shadow"},indent=2))
    if rep["status"]!="INDEX_SHADOW_ONLY_RESOLVED":raise SystemExit(2)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--decision",required=True)
    p.add_argument("--anchor",required=True)
    asyncio.run(main(p.parse_args()))

#!/usr/bin/env python3
from __future__ import annotations
import asyncio,hashlib,json,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
import websockets

OUT=Path("artifacts/ipg001_binance_transport_matrix_v01.json")
SPOT=[
 ("spot_9443","wss://stream.binance.com:9443/ws/btcusdt@aggTrade","raw"),
 ("spot_443","wss://stream.binance.com:443/ws/btcusdt@aggTrade","raw"),
 ("spot_marketdata_only","wss://data-stream.binance.vision/ws/btcusdt@aggTrade","raw"),
]
FUT=[
 ("futures_raw","wss://fstream.binance.com/ws/btcusdt@aggTrade","raw"),
 ("futures_combined","wss://fstream.binance.com/stream?streams=btcusdt@aggTrade","combined"),
 ("futures_subscribe","wss://fstream.binance.com/ws","subscribe"),
]

def norm_event(x,combined=False):
    if combined and isinstance(x,dict) and isinstance(x.get("data"),dict):
        x=x["data"]
    if not isinstance(x,dict) or x.get("e")!="aggTrade":return None
    ts=x.get("T") or x.get("E")
    if ts is None:return None
    return {"event_ts_ms":int(ts),"publish_ts_ms":int(x["E"]) if x.get("E") is not None else None,
            "symbol":x.get("s"),"agg_trade_id":x.get("a")}

async def ws_probe(name,url,mode):
    row={"name":name,"url":url,"mode":mode,"events":[],"pass":False}
    try:
      async with websockets.connect(url,ping_interval=15,ping_timeout=15,open_timeout=12,close_timeout=3) as ws:
        if mode=="subscribe":
          await ws.send(json.dumps({"method":"SUBSCRIBE","params":["btcusdt@aggTrade"],"id":1},separators=(",",":")))
        deadline=time.monotonic()+12
        while len(row["events"])<3 and time.monotonic()<deadline:
          raw=await asyncio.wait_for(ws.recv(),timeout=max(.5,deadline-time.monotonic()))
          if isinstance(raw,bytes):raw=raw.decode()
          x=json.loads(raw)
          if mode=="subscribe" and x.get("id")==1:continue
          ev=norm_event(x,mode=="combined")
          if ev:
            ev["recv_wall_ts_ms"]=int(time.time()*1000)
            ev["raw_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
            row["events"].append(ev)
        row["pass"]=len(row["events"])>=3
    except Exception as e:
      row["error"]=f"{type(e).__name__}:{str(e)[:500]}"
    return row

def rest_probe(name,url):
    row={"name":name,"url":url,"diagnostic_only":True,"pass":False}
    try:
      req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-IPG-Binance-Transport/0.1"})
      with urllib.request.urlopen(req,timeout=15) as r:
        raw=r.read();status=r.status
      x=json.loads(raw.decode())
      row.update({"http_status":status,"row_count":len(x) if isinstance(x,list) else None,
                  "body_sha256":hashlib.sha256(raw).hexdigest(),
                  "pass":status==200 and isinstance(x,list) and len(x)>0})
    except urllib.error.HTTPError as e:
      body=e.read()
      row.update({"http_status":e.code,"error":f"HTTPError:{e.code}:{body[:300].decode(errors='replace')}"})
    except Exception as e:
      row["error"]=f"{type(e).__name__}:{str(e)[:500]}"
    return row

async def main():
    spot=await asyncio.gather(*(ws_probe(*x) for x in SPOT))
    fut=await asyncio.gather(*(ws_probe(*x) for x in FUT))
    return spot,fut

spot,fut=asyncio.run(main())
spot_rest=rest_probe("spot_data_api","https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDT&limit=5")
fut_rest=rest_probe("futures_fapi","https://fapi.binance.com/fapi/v1/aggTrades?symbol=BTCUSDT&limit=5")
spot_pass=any(x["pass"] for x in spot)
fut_pass=any(x["pass"] for x in fut)
if spot_pass and fut_pass:classification="BINANCE_FORWARD_WS_TRANSPORT_PASS"
elif spot_pass:classification="BINANCE_SPOT_WS_PASS_FUTURES_WS_BLOCKED"
elif fut_pass:classification="BINANCE_FUTURES_WS_PASS_SPOT_WS_BLOCKED"
else:classification="BINANCE_FORWARD_WS_TRANSPORT_BLOCKED"
receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001","stage":"BINANCE_PUBLIC_TRANSPORT_MATRIX_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":classification,"spot_ws_pass":spot_pass,"futures_ws_pass":fut_pass,
 "spot_websocket_probes":spot,"futures_websocket_probes":fut,
 "rest_diagnostics":[spot_rest,fut_rest],
 "rest_can_satisfy_forward_timing_gate":False,
 "market_outcomes_opened":False,"pnl_opened":False,"mutation":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

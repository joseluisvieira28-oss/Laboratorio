#!/usr/bin/env python3
from __future__ import annotations
import asyncio,hashlib,json,time,uuid
from datetime import datetime,timezone
from pathlib import Path
import websockets

OUT=Path("artifacts/ipg001_public_forward_source_smoke_v01.json")
TARGETS={
 "binance_spot":10,
 "binance_perp":10,
 "deribit_perp":5,
 "deribit_options":2,
 "deribit_dvol":2,
}
SAMPLES={k:[] for k in TARGETS}
ERRORS={k:[] for k in TARGETS}
CONNECTIONS={}

def recv_clock():
    return int(time.time()*1000),time.monotonic_ns()

def raw_hash(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def add(name,raw,source_ts,sequence=None,instrument=None,publish_ts=None):
    wall,mono=recv_clock()
    SAMPLES[name].append({
      "source_event_ts_ms":int(source_ts) if source_ts is not None else None,
      "source_publish_ts_ms":int(publish_ts) if publish_ts is not None else None,
      "recv_wall_ts_ms":wall,
      "recv_monotonic_ns":mono,
      "source_sequence":str(sequence) if sequence is not None else None,
      "instrument":instrument,
      "raw_sha256":raw_hash(raw),
      "connection_id":CONNECTIONS[name],
    })

async def collect_binance(name,url):
    CONNECTIONS[name]=str(uuid.uuid4())
    try:
      async with websockets.connect(url,ping_interval=15,ping_timeout=15,close_timeout=5) as ws:
        deadline=time.monotonic()+25
        while len(SAMPLES[name])<TARGETS[name] and time.monotonic()<deadline:
          raw=await asyncio.wait_for(ws.recv(),timeout=max(1,deadline-time.monotonic()))
          if isinstance(raw,bytes):raw=raw.decode()
          x=json.loads(raw)
          add(name,raw,x.get("T") or x.get("E"),x.get("a"),x.get("s"),x.get("E"))
    except Exception as e:
      ERRORS[name].append(f"{type(e).__name__}:{str(e)[:300]}")

async def deribit_subscribe(name,channel,mode):
    CONNECTIONS[name]=str(uuid.uuid4())
    try:
      async with websockets.connect("wss://www.deribit.com/ws/api/v2",ping_interval=15,ping_timeout=15,close_timeout=5) as ws:
        req={"jsonrpc":"2.0","id":1,"method":"public/subscribe","params":{"channels":[channel]}}
        await ws.send(json.dumps(req,separators=(",",":")))
        deadline=time.monotonic()+30
        while len(SAMPLES[name])<TARGETS[name] and time.monotonic()<deadline:
          raw=await asyncio.wait_for(ws.recv(),timeout=max(1,deadline-time.monotonic()))
          if isinstance(raw,bytes):raw=raw.decode()
          x=json.loads(raw)
          if x.get("id")==1:
            if x.get("error"):raise RuntimeError(x["error"])
            continue
          if x.get("method")!="subscription":continue
          data=(x.get("params") or {}).get("data")
          if mode=="trades":
            if not isinstance(data,list):continue
            for t in data:
              if not isinstance(t,dict) or t.get("timestamp") is None:continue
              add(name,raw,t.get("timestamp"),t.get("trade_seq"),t.get("instrument_name"))
              if len(SAMPLES[name])>=TARGETS[name]:break
          elif mode=="options":
            if not isinstance(data,list) or not data:continue
            valid=[z for z in data if isinstance(z,dict) and z.get("timestamp") is not None]
            if not valid:continue
            ts=max(int(z["timestamp"]) for z in valid)
            inst=valid[0].get("instrument_name")
            add(name,raw,ts,None,inst)
          elif mode=="dvol":
            if not isinstance(data,dict) or data.get("timestamp") is None:continue
            add(name,raw,data.get("timestamp"),None,data.get("index_name"))
    except Exception as e:
      ERRORS[name].append(f"{type(e).__name__}:{str(e)[:300]}")

async def main():
    await asyncio.gather(
      collect_binance("binance_spot","wss://stream.binance.com:9443/ws/btcusdt@aggTrade"),
      collect_binance("binance_perp","wss://fstream.binance.com/ws/btcusdt@aggTrade"),
      deribit_subscribe("deribit_perp","trades.BTC-PERPETUAL.100ms","trades"),
      deribit_subscribe("deribit_options","markprice.options.btc_usd","options"),
      deribit_subscribe("deribit_dvol","deribit_volatility_index.btc_usd","dvol"),
    )

asyncio.run(main())

checks={}
passed=True
for name,target in TARGETS.items():
    rows=SAMPLES[name]
    source_complete=bool(rows) and all(r["source_event_ts_ms"] is not None for r in rows)
    monotonic=all(b["recv_monotonic_ns"]>=a["recv_monotonic_ns"] for a,b in zip(rows,rows[1:]))
    skews=[abs(r["recv_wall_ts_ms"]-r["source_event_ts_ms"]) for r in rows if r["source_event_ts_ms"] is not None]
    skew_ok=bool(skews) and max(skews)<=10000
    stream_ok=len(rows)>=target and source_complete and monotonic and skew_ok and not ERRORS[name]
    checks[name]={
      "target":target,"count":len(rows),"source_timestamp_complete":source_complete,
      "recv_monotonic_nonregressing":monotonic,
      "max_abs_wall_source_delta_ms":max(skews) if skews else None,
      "errors":ERRORS[name],"pass":stream_ok,
    }
    passed=passed and stream_ok

receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001",
 "stage":"PUBLIC_FORWARD_SOURCE_SMOKE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"FORWARD_PUBLIC_SOURCE_SMOKE_PASS" if passed else "FORWARD_PUBLIC_SOURCE_SMOKE_BLOCKED",
 "checks":checks,
 "samples":SAMPLES,
 "raw_payload_content_persisted":False,
 "wall_source_delta_interpreted_as_latency":False,
 "predictive_analysis_performed":False,
 "market_outcomes_opened":False,"pnl_opened":False,"mutation":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"checks":checks},indent=2))
if not passed:raise SystemExit(2)

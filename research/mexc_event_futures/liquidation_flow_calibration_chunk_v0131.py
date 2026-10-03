#!/usr/bin/env python3
"""Forward-only Bybit liquidation calibration chunk collector. NO MEXC / NO outcomes."""
import argparse, asyncio, json, math, time
from collections import defaultdict
from pathlib import Path

from priority_source_gates_v013 import Evidence, now_ms, valid_liquidation

WS="wss://stream.bybit.com/v5/public/linear"
SYMBOLS=("BTCUSDT","ETHUSDT")
GRACE_MS=5000

def minute_start(ts):
    return (int(ts)//60000)*60000

def build_bin(symbol,start,state):
    end=start+60000
    pongs=[t for t in state["pongs"] if start<=t<end]
    invalid=[t for t in state["invalid_times"] if start<=t<end+GRACE_MS]
    conn_ok=(
        state["connected_at"] is not None and state["connected_at"]<start
        and state["ack_at"] is not None and state["ack_at"]<start
        and (state["disconnected_at"] is None or state["disconnected_at"]>=end+GRACE_MS)
    )
    heartbeat=(any(start<=t<start+30000 for t in pongs)
               and any(start+30000<=t<end for t in pongs))
    healthy=bool(conn_ok and heartbeat and not invalid)
    events=[e for e in state["events"] if start<=e["T"]<end]
    forced_sell=sum(e["notional_proxy"] for e in events if e["S"]=="Buy")
    forced_buy=sum(e["notional_proxy"] for e in events if e["S"]=="Sell")
    total=forced_sell+forced_buy
    signed=forced_buy-forced_sell
    return {
        "symbol":symbol,
        "minute_start_ms":start,
        "minute_end_ms":end,
        "healthy":healthy,
        "connection_ok":conn_ok,
        "heartbeat_first_half":any(start<=t<start+30000 for t in pongs),
        "heartbeat_second_half":any(start+30000<=t<end for t in pongs),
        "pong_count":len(pongs),
        "invalid_count":len(invalid),
        "event_count":len(events),
        "forced_sell_proxy":forced_sell if healthy else None,
        "forced_buy_proxy":forced_buy if healthy else None,
        "total_notional_proxy":total if healthy else None,
        "signed_buy_minus_sell_proxy":signed if healthy else None,
        "absolute_imbalance_ratio":(abs(signed)/total if healthy and total>0 else (0.0 if healthy else None)),
        "event_raw_sha256":[e["raw_sha256"] for e in events],
    }

async def collect(minutes,output,gate_anchor):
    import websockets
    evidence=Evidence(output)
    state={s:{
        "connected_at":None,"disconnected_at":None,"ack_at":None,
        "pongs":[],"invalid_times":[],"events":[],"errors":[],"seq":0
    } for s in SYMBOLS}
    stop=asyncio.Event()

    now=now_ms()
    first=((now//60000)+1)*60000
    final=first+minutes*60000+GRACE_MS

    async def watch(symbol):
        st=state[symbol];topic="allLiquidation."+symbol
        req=f"cal-{symbol.lower()}"
        try:
            async with websockets.connect(WS,open_timeout=20,ping_interval=None,close_timeout=5,max_size=4*1024*1024) as ws:
                st["connected_at"]=now_ms()
                await ws.send(json.dumps({"req_id":req,"op":"subscribe","args":[topic]},separators=(",",":")))
                last_ping=0.0
                while not stop.is_set() and now_ms()<final:
                    if time.monotonic()-last_ping>=15:
                        await ws.send(json.dumps({"req_id":req+"-ping","op":"ping"},separators=(",",":")))
                        last_ping=time.monotonic()
                    try:
                        raw=await asyncio.wait_for(ws.recv(),timeout=2)
                    except asyncio.TimeoutError:
                        continue
                    recv=now_ms();st["seq"]+=1
                    ref=evidence.save(f'{symbol.lower()}-{st["seq"]:08d}.json',raw,received_at_ms=recv,source_url=WS)
                    try:
                        j=json.loads(raw)
                    except Exception as exc:
                        st["invalid_times"].append(recv)
                        st["errors"].append({"type":"NON_JSON","at":recv,"sha256":ref["sha256"],"error":repr(exc)})
                        continue
                    if j.get("op")=="subscribe" and j.get("req_id")==req and j.get("success") is True:
                        st["ack_at"]=recv
                    if j.get("op")=="ping" or j.get("ret_msg")=="pong":
                        st["pongs"].append(recv)
                    if j.get("topic")==topic:
                        for ordinal,item in enumerate(j.get("data",[])):
                            if not valid_liquidation(item,j,recv):
                                st["invalid_times"].append(recv)
                                st["errors"].append({"type":"INVALID_ITEM","at":recv,"sha256":ref["sha256"],"ordinal":ordinal})
                                continue
                            st["events"].append({
                                "T":int(item["T"]),"S":item["S"],
                                "v":float(item["v"]),"p":float(item["p"]),
                                "notional_proxy":float(item["v"])*float(item["p"]),
                                "raw_sha256":ref["sha256"],"ordinal":ordinal,
                                "received_at_ms":recv,"envelope_ts":j.get("ts"),
                            })
                st["disconnected_at"]=now_ms()
        except asyncio.CancelledError:
            st["disconnected_at"]=now_ms();raise
        except Exception as exc:
            st["disconnected_at"]=now_ms()
            st["invalid_times"].append(now_ms())
            st["errors"].append({"type":type(exc).__name__,"error":str(exc),"at":now_ms()})

    tasks=[asyncio.create_task(watch(s)) for s in SYMBOLS]
    while now_ms()<final:
        await asyncio.sleep(min(2,max(.05,(final-now_ms())/1000)))
    stop.set()
    await asyncio.gather(*tasks,return_exceptions=True)

    bins=[]
    for s in SYMBOLS:
        for i in range(minutes):
            bins.append(build_bin(s,first+i*60000,state[s]))

    p=Path(output)/"calibration_bins.jsonl"
    with p.open("w",encoding="utf-8") as f:
        for row in bins:
            f.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
    evidence.entries.append({"path":p.name,"sha256":__import__("hashlib").sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})

    counts={}
    for s in SYMBOLS:
        rows=[r for r in bins if r["symbol"]==s]
        healthy=[r for r in rows if r["healthy"]]
        nonzero=[r for r in healthy if r["total_notional_proxy"] and r["total_notional_proxy"]>0]
        counts[s]={"bins":len(rows),"healthy_bins":len(healthy),"nonzero_healthy_bins":len(nonzero)}
    receipt={
        "family_id":"LIQUIDATION-FLOW-FWD-001",
        "phase":"FORWARD_CALIBRATION_CHUNK",
        "gate_anchor":gate_anchor,
        "first_full_minute_ms":first,
        "minutes_requested":minutes,
        "counts":counts,
        "threshold_computed":False,
        "activation_allowed":False,
        "research_outcomes_opened":0,
        "mexc_subscriptions":0,
        "errors":{s:state[s]["errors"] for s in SYMBOLS},
    }
    evidence.finish(receipt)
    print(json.dumps(receipt,indent=2,sort_keys=True))

def self_test():
    start=1_800_000_000_000
    st={
      "connected_at":start-10000,"disconnected_at":start+70000,"ack_at":start-5000,
      "pongs":[start+10000,start+40000],"invalid_times":[],
      "events":[
        {"T":start+1000,"S":"Buy","notional_proxy":100.0,"raw_sha256":"a"*64},
        {"T":start+2000,"S":"Sell","notional_proxy":300.0,"raw_sha256":"b"*64},
      ]
    }
    r=build_bin("BTCUSDT",start,st)
    assert r["healthy"] and r["total_notional_proxy"]==400.0
    assert r["forced_sell_proxy"]==100.0 and r["forced_buy_proxy"]==300.0
    assert abs(r["absolute_imbalance_ratio"]-.5)<1e-12
    st2={**st,"pongs":[start+10000]}
    assert not build_bin("BTCUSDT",start,st2)["healthy"]
    print("CALIBRATION_BIN_SELFTEST_PASS; SYNTHETIC_ONLY; OUTCOMES_OPENED=0")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--minutes",type=int)
    ap.add_argument("--output")
    ap.add_argument("--gate-anchor")
    a=ap.parse_args()
    if a.self_test:
        self_test()
    else:
        if not a.minutes or not a.output or not a.gate_anchor:
            ap.error("--minutes --output --gate-anchor required")
        asyncio.run(collect(a.minutes,a.output,a.gate_anchor))

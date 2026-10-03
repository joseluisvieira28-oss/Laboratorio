#!/usr/bin/env python3
"""V0.13.1 Bybit liquidation source completion: independent BTC/ETH public channels."""
import argparse
import asyncio
import json
import time
from pathlib import Path

from priority_source_gates_v013 import Evidence, now_ms, valid_liquidation

WS="wss://stream.bybit.com/v5/public/linear"
TOPICS={"BTCUSDT":"allLiquidation.BTCUSDT","ETHUSDT":"allLiquidation.ETHUSDT"}
PRIOR_BTC={
    "run_id":37075262340,
    "artifact_id":11257963990,
    "artifact_digest":"sha256:1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f",
    "valid_raw_sha256":[
        "4680e77698c7903751dcda04c1a8165ca2134cb4d6cf572a90198d414fefc302",
        "f09a4ca383e36acf2f0e3316a2133631734f01604b6b27d978eeb1fe66b23c49",
        "282b7fa22e79458d4b25c665d74c3eb79837d1d5fa99c428bc257436ad960455",
    ],
}

async def main(seconds, output):
    import websockets

    evidence=Evidence(output)
    started=now_ms()
    state={
        s:{"ack":False,"valid_events":0,"messages":0,"pongs":0,"errors":[],"valid_records":[]}
        for s in TOPICS
    }
    stop=asyncio.Event()

    async def watch(symbol):
        topic=TOPICS[symbol]
        seq=0
        req_id=f"v0131-{symbol.lower()}"
        try:
            async with websockets.connect(
                WS,open_timeout=20,ping_interval=None,close_timeout=5,max_size=4*1024*1024
            ) as ws:
                sub={"req_id":req_id,"op":"subscribe","args":[topic]}
                await ws.send(json.dumps(sub,separators=(",",":")))
                deadline=time.monotonic()+seconds
                last_ping=time.monotonic()
                while time.monotonic()<deadline and not stop.is_set():
                    if time.monotonic()-last_ping>=20:
                        await ws.send(json.dumps({"req_id":req_id+"-ping","op":"ping"},separators=(",",":")))
                        last_ping=time.monotonic()
                    try:
                        raw=await asyncio.wait_for(ws.recv(),timeout=min(2,max(.05,deadline-time.monotonic())))
                    except asyncio.TimeoutError:
                        continue
                    recv=now_ms(); seq+=1; state[symbol]["messages"]+=1
                    ref=evidence.save(
                        f'{symbol.lower()}-{seq:08d}.json',raw,
                        received_at_ms=recv,source_url=WS
                    )
                    try:
                        j=json.loads(raw)
                    except Exception as exc:
                        state[symbol]["errors"].append({"type":"NON_JSON","error":repr(exc),"raw_sha256":ref["sha256"]})
                        continue
                    if j.get("op")=="subscribe" and j.get("req_id")==req_id:
                        state[symbol]["ack"]=j.get("success") is True
                    if j.get("op")=="ping" or j.get("ret_msg")=="pong":
                        state[symbol]["pongs"]+=1
                    if j.get("topic")==topic:
                        for ordinal,item in enumerate(j.get("data",[])):
                            valid=valid_liquidation(item,j,recv)
                            rec={
                                "raw_sha256":ref["sha256"],
                                "ordinal":ordinal,
                                "valid":valid,
                                "received_at_ms":recv,
                                "envelope_ts":j.get("ts"),
                                "item":item,
                            }
                            if valid:
                                state[symbol]["valid_events"]+=1
                                state[symbol]["valid_records"].append(rec)
                            else:
                                state[symbol]["errors"].append({
                                    "type":"INVALID_LIQUIDATION_ITEM",
                                    "raw_sha256":ref["sha256"],
                                    "ordinal":ordinal,
                                })
                    if (
                        state["BTCUSDT"]["ack"] and
                        state["ETHUSDT"]["ack"] and
                        state["ETHUSDT"]["valid_events"]>0 and
                        not state["BTCUSDT"]["errors"] and
                        not state["ETHUSDT"]["errors"]
                    ):
                        stop.set()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            state[symbol]["errors"].append({"type":type(exc).__name__,"error":str(exc)})
            stop.set()

    tasks=[asyncio.create_task(watch(s)) for s in TOPICS]
    try:
        await asyncio.wait_for(asyncio.gather(*tasks),timeout=seconds+30)
    except asyncio.TimeoutError:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)

    all_acks=all(state[s]["ack"] for s in TOPICS)
    any_errors=any(state[s]["errors"] for s in TOPICS)
    eth_valid=state["ETHUSDT"]["valid_events"]
    if all_acks and eth_valid>0 and not any_errors:
        verdict="SOURCE_GATE_PASS"
        evidence_mode="CUMULATIVE_PRIOR_BTC_PLUS_CURRENT_ETH"
    elif all_acks and not any_errors:
        verdict="PARTIAL_SOURCE"
        evidence_mode="PRIOR_BTC_ANCHORED_ETH_STILL_MISSING"
    else:
        verdict="SOURCE_BLOCKED"
        evidence_mode="TRANSPORT_ACK_OR_SCHEMA_FAILURE"

    receipt={
        "family_id":"LIQUIDATION-FLOW-FWD-001",
        "family_version":"SOURCE_COMPLETION_V0.13.1",
        "verdict":verdict,
        "evidence_mode":evidence_mode,
        "source":WS,
        "started_at_ms":started,
        "finished_at_ms":now_ms(),
        "max_seconds":seconds,
        "prior_btc_anchor":PRIOR_BTC,
        "state":state,
        "research_outcomes_opened":0,
        "mexc_subscriptions":0,
        "trading":0,
        "safety":{
            "NO_LOGIN":True,
            "NO_API_KEY":True,
            "NO_PRIVATE":True,
            "NO_ORDERS":True,
            "NO_MEXC_OUTCOMES":True,
        },
    }
    evidence.finish(receipt)

    print(json.dumps({
        "verdict":verdict,
        "evidence_mode":evidence_mode,
        "acks":{s:state[s]["ack"] for s in TOPICS},
        "valid_events":{s:state[s]["valid_events"] for s in TOPICS},
        "pongs":{s:state[s]["pongs"] for s in TOPICS},
        "errors":{s:state[s]["errors"] for s in TOPICS},
        "research_outcomes_opened":0,
        "trading":0,
    },indent=2,sort_keys=True))

    if verdict=="SOURCE_BLOCKED":
        raise SystemExit(2)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=int,required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    asyncio.run(main(args.seconds,args.output))

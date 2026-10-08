#!/usr/bin/env python3
from __future__ import annotations
import asyncio, hashlib, json, math, time
from datetime import datetime, timezone
from pathlib import Path
import websockets

WS="wss://fstream.binance.com/market/stream"
STREAMS=["btcusdt@forceOrder","ethusdt@forceOrder"]
TARGETS={"BTCUSDT","ETHUSDT"}
SECONDS=600
MAX_AGE_MS=5000
FUTURE_TOL_MS=1000
OUT=Path("evidence/liquidation-binance-source-v03")

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def sha256(b: bytes):
    return hashlib.sha256(b).hexdigest()

def posnum(x):
    try:
        v=float(x)
        return math.isfinite(v) and v>0
    except Exception:
        return False

async def run():
    OUT.mkdir(parents=True,exist_ok=True)
    valid={s:[] for s in TARGETS}
    invalid=[]
    manifest=[]
    errors=[]
    ack=False
    raw_count=0
    started_ms=int(time.time()*1000)

    try:
        async with websockets.connect(
            WS,open_timeout=20,close_timeout=10,ping_interval=20,ping_timeout=10,
            max_size=2_000_000,additional_headers={"User-Agent":"CryptoLab-Liquidation-Binance/0.3"}
        ) as ws:
            sub={"method":"SUBSCRIBE","params":STREAMS,"id":1}
            await ws.send(json.dumps(sub,separators=(",",":")))
            deadline=time.monotonic()+SECONDS
            while time.monotonic()<deadline:
                timeout=max(0.2,min(5.0,deadline-time.monotonic()))
                try:
                    msg=await asyncio.wait_for(ws.recv(),timeout=timeout)
                except asyncio.TimeoutError:
                    continue

                recv_ms=int(time.time()*1000)
                raw=msg if isinstance(msg,bytes) else msg.encode("utf-8")
                textmsg=msg.decode("utf-8","replace") if isinstance(msg,bytes) else msg
                raw_count+=1
                h=sha256(raw)
                fn=f"raw_{raw_count:06d}.json"
                (OUT/fn).write_bytes(raw)
                manifest.append({"file":fn,"sha256":h,"bytes":len(raw),"received_at_ms":recv_ms})

                try:
                    j=json.loads(textmsg)
                except Exception as e:
                    invalid.append({"raw_sha256":h,"reason":"INVALID_JSON","error":repr(e)})
                    continue

                if j.get("id")==1 and "result" in j:
                    ack = j.get("result") is None
                    continue
                if "code" in j and ("msg" in j or "message" in j):
                    errors.append({"received_at_ms":recv_ms,"payload":j})
                    continue

                data=j.get("data") if isinstance(j,dict) and isinstance(j.get("data"),dict) else j
                if not isinstance(data,dict) or data.get("e")!="forceOrder":
                    continue
                o=data.get("o") or {}
                sym=o.get("s")
                if sym not in TARGETS:
                    continue

                reasons=[]
                side=o.get("S")
                if side not in ("BUY","SELL"): reasons.append("BAD_SIDE")
                if not posnum(o.get("q")): reasons.append("BAD_Q")
                if not (posnum(o.get("ap")) or posnum(o.get("p"))): reasons.append("BAD_PRICE")
                try: E=int(data.get("E"))
                except Exception: E=None; reasons.append("BAD_E")
                try: T=int(o.get("T"))
                except Exception: T=None; reasons.append("BAD_T")
                age_ms=None
                if E is not None and T is not None:
                    source_ms=max(E,T)
                    age_ms=recv_ms-source_ms
                    if age_ms>MAX_AGE_MS: reasons.append("STALE")
                    if age_ms < -FUTURE_TOL_MS: reasons.append("FUTURE_CLOCK")

                rec={
                    "raw_sha256":h,"received_at_ms":recv_ms,"symbol":sym,"side":side,
                    "quantity":o.get("q"),"price":o.get("p"),"average_price":o.get("ap"),
                    "status":o.get("X"),"event_ms":E,"trade_ms":T,"age_ms":age_ms,
                    "valid":not reasons,"reasons":reasons
                }
                if reasons: invalid.append(rec)
                else: valid[sym].append(rec)
    except Exception as e:
        errors.append({"at_utc":utcnow(),"transport_error":repr(e)})

    finished_ms=int(time.time()*1000)
    if errors or not ack:
        verdict="SOURCE_BLOCKED"
    elif all(len(valid[s])>=1 for s in TARGETS):
        verdict="BINANCE_LIQUIDATION_SOURCE_PASS"
    elif any(len(valid[s])>=1 for s in TARGETS):
        verdict="PARTIAL_SOURCE"
    else:
        verdict="NO_EVENTS_OBSERVED"

    receipt={
        "family_id":"LIQUIDATION-FLOW-FWD-003",
        "source_version":"BINANCE_USDM_V0.3",
        "verdict":verdict,
        "source_only":True,
        "endpoint":WS,
        "streams":STREAMS,
        "subscription_ack":ack,
        "started_at_ms":started_ms,
        "finished_at_ms":finished_ms,
        "elapsed_seconds":(finished_ms-started_ms)/1000,
        "raw_message_count":raw_count,
        "valid_events_by_symbol":{s:len(valid[s]) for s in sorted(TARGETS)},
        "valid_events":valid,
        "invalid_target_events":invalid,
        "errors":errors,
        "raw_manifest":manifest,
        "research_outcomes_opened":0,
        "mexc_event_futures_accessed":False,
        "family_activated":False,
        "threshold_committed":False,
        "safety":{
            "NO_AUTH":True,"NO_PRIVATE":True,"NO_ORDERS":True,"NO_ACCOUNT_READS":True,
            "NO_WALLETS":True,"NO_MEXC_OUTCOMES":True,"NO_EXCHANGE_MUTATION":True
        }
    }
    (OUT/"BINANCE_LIQUIDATION_SOURCE_GATE_RECEIPT_V03.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    (OUT/"raw_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({
        "family_id":receipt["family_id"],"verdict":verdict,"subscription_ack":ack,
        "valid_events_by_symbol":receipt["valid_events_by_symbol"],
        "raw_message_count":raw_count,"errors":errors,
        "research_outcomes_opened":0,"family_activated":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    asyncio.run(run())

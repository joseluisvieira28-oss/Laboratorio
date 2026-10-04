#!/usr/bin/env python3
"""LIQUIDATION-FLOW-FWD-002 OKX public source gate.

Public websocket + public instruments metadata only.
No MEXC Event Futures data, outcomes, accounts, orders or mutation.
"""
from __future__ import annotations
import asyncio, hashlib, json, math, time
from datetime import datetime, timezone
from pathlib import Path

import requests
import websockets

WS="wss://ws.okx.com:8443/ws/v5/public"
REST="https://www.okx.com"
TARGETS={"BTC-USDT-SWAP","ETH-USDT-SWAP"}
SECONDS=600
MAX_AGE_MS=5000
FUTURE_TOL_MS=1000
OUT=Path("evidence/liquidation-okx-source-v02")
UA="CryptoLab-Liquidation-OKX-SourceGate/0.2"

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def finite_pos(x):
    try:
        v=float(x)
        return math.isfinite(v) and v>0
    except Exception:
        return False

def fetch_instruments():
    out={}
    for inst in sorted(TARGETS):
        r=requests.get(
            REST+"/api/v5/public/instruments",
            params={"instType":"SWAP","instId":inst},
            headers={"User-Agent":UA}, timeout=30,
        )
        raw=r.content
        if r.status_code!=200:
            raise RuntimeError(f"INSTRUMENT_HTTP_{r.status_code}:{inst}")
        j=r.json()
        if str(j.get("code"))!="0" or not j.get("data"):
            raise RuntimeError(f"INSTRUMENT_MISSING:{inst}:{j}")
        row=next((x for x in j["data"] if x.get("instId")==inst),None)
        if not row:
            raise RuntimeError(f"INSTRUMENT_EXACT_MISSING:{inst}")
        out[inst]={
            "raw_sha256":sha256(raw),
            "raw_bytes":len(raw),
            "captured_at_utc":utcnow(),
            "metadata":{k:row.get(k) for k in
                ["instId","instType","instFamily","ctVal","ctMult","ctValCcy","ctType",
                 "settleCcy","lotSz","minSz","state"]}
        }
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/f"{inst}_instrument.json").write_bytes(raw)
    return out

async def run():
    OUT.mkdir(parents=True,exist_ok=True)
    instruments=fetch_instruments()
    started_ms=int(time.time()*1000)
    valid={s:[] for s in TARGETS}
    invalid=[]
    raw_manifest=[]
    subscription_ack=False
    errors=[]
    pongs=0
    raw_count=0

    try:
        async with websockets.connect(
            WS, open_timeout=20, close_timeout=10,
            ping_interval=None, max_size=2_000_000,
            additional_headers={"User-Agent":UA},
        ) as ws:
            sub={"op":"subscribe","args":[{"channel":"liquidation-orders","instType":"SWAP"}]}
            await ws.send(json.dumps(sub,separators=(",",":")))
            deadline=time.monotonic()+SECONDS
            next_ping=time.monotonic()+20

            while time.monotonic()<deadline:
                timeout=max(0.2,min(5.0,deadline-time.monotonic()))
                try:
                    msg=await asyncio.wait_for(ws.recv(),timeout=timeout)
                except asyncio.TimeoutError:
                    if time.monotonic()>=next_ping:
                        await ws.send("ping")
                        next_ping=time.monotonic()+20
                    continue

                recv_ms=int(time.time()*1000)
                if isinstance(msg,bytes):
                    raw=msg
                    text=msg.decode("utf-8","replace")
                else:
                    text=msg
                    raw=msg.encode("utf-8")

                if text=="pong":
                    pongs+=1
                    continue

                raw_count+=1
                raw_hash=sha256(raw)
                name=f"raw_{raw_count:06d}.json"
                (OUT/name).write_bytes(raw)
                raw_manifest.append({
                    "file":name,"sha256":raw_hash,"bytes":len(raw),
                    "received_at_ms":recv_ms
                })

                try:
                    j=json.loads(text)
                except Exception as e:
                    invalid.append({"raw_sha256":raw_hash,"reason":"INVALID_JSON","error":repr(e)})
                    continue

                if j.get("event")=="subscribe":
                    arg=j.get("arg") or {}
                    if arg.get("channel")=="liquidation-orders" and arg.get("instType")=="SWAP":
                        subscription_ack=True
                    continue
                if j.get("event")=="error":
                    errors.append({"received_at_ms":recv_ms,"payload":j})
                    continue

                arg=j.get("arg") or {}
                if arg.get("channel")!="liquidation-orders":
                    continue

                for outer in j.get("data") or []:
                    inst=outer.get("instId")
                    if inst not in TARGETS:
                        continue
                    details=outer.get("details") or []
                    for d in details:
                        reasons=[]
                        side=d.get("side")
                        pos_side=d.get("posSide")
                        if side not in ("buy","sell"): reasons.append("BAD_SIDE")
                        if pos_side not in ("long","short"): reasons.append("BAD_POS_SIDE")
                        if not finite_pos(d.get("sz")): reasons.append("BAD_SZ")
                        if not finite_pos(d.get("bkPx")): reasons.append("BAD_BKPX")
                        try:
                            event_ms=int(d.get("ts"))
                        except Exception:
                            event_ms=None
                            reasons.append("BAD_TS")
                        age_ms=None
                        if event_ms is not None:
                            age_ms=recv_ms-event_ms
                            if age_ms>MAX_AGE_MS: reasons.append("STALE")
                            if age_ms < -FUTURE_TOL_MS: reasons.append("FUTURE_CLOCK")
                        rec={
                            "raw_sha256":raw_hash,
                            "received_at_ms":recv_ms,
                            "instId":inst,
                            "instFamily":outer.get("instFamily"),
                            "instType":outer.get("instType"),
                            "side":side,
                            "posSide":pos_side,
                            "sz":d.get("sz"),
                            "bkPx":d.get("bkPx"),
                            "bkLoss":d.get("bkLoss"),
                            "ccy":d.get("ccy"),
                            "event_ts_ms":event_ms,
                            "age_ms":age_ms,
                            "valid":not reasons,
                            "reasons":reasons,
                        }
                        if reasons:
                            invalid.append(rec)
                        else:
                            valid[inst].append(rec)

                if time.monotonic()>=next_ping:
                    await ws.send("ping")
                    next_ping=time.monotonic()+20
    except Exception as e:
        errors.append({"at_utc":utcnow(),"transport_error":repr(e)})

    finished_ms=int(time.time()*1000)
    if errors or not subscription_ack:
        verdict="SOURCE_BLOCKED"
    elif all(len(valid[s])>=1 for s in TARGETS):
        verdict="OKX_LIQUIDATION_SOURCE_PASS"
    elif any(len(valid[s])>=1 for s in TARGETS):
        verdict="PARTIAL_SOURCE"
    else:
        verdict="NO_EVENTS_OBSERVED"

    receipt={
        "family_id":"LIQUIDATION-FLOW-FWD-002",
        "source_version":"OKX_V0.2",
        "verdict":verdict,
        "source_only":True,
        "endpoint":WS,
        "subscription":{"channel":"liquidation-orders","instType":"SWAP"},
        "subscription_ack":subscription_ack,
        "started_at_ms":started_ms,
        "finished_at_ms":finished_ms,
        "elapsed_seconds":(finished_ms-started_ms)/1000,
        "pongs":pongs,
        "raw_message_count":raw_count,
        "instruments":instruments,
        "valid_events_by_symbol":{s:len(valid[s]) for s in sorted(TARGETS)},
        "valid_events":valid,
        "invalid_target_details":invalid,
        "errors":errors,
        "raw_manifest":raw_manifest,
        "research_outcomes_opened":0,
        "mexc_event_futures_accessed":False,
        "threshold_committed":False,
        "family_activated":False,
        "safety":{
            "NO_AUTH":True,"NO_PRIVATE":True,"NO_ORDERS":True,
            "NO_ACCOUNT_READS":True,"NO_WALLETS":True,"NO_MEXC_OUTCOMES":True
        }
    }
    (OUT/"OKX_LIQUIDATION_SOURCE_GATE_RECEIPT_V02.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    (OUT/"raw_manifest.json").write_text(
        json.dumps(raw_manifest,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
        "family_id":receipt["family_id"],
        "verdict":verdict,
        "subscription_ack":subscription_ack,
        "valid_events_by_symbol":receipt["valid_events_by_symbol"],
        "raw_message_count":raw_count,
        "pongs":pongs,
        "errors":errors,
        "research_outcomes_opened":0,
        "family_activated":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    asyncio.run(run())

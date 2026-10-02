#!/usr/bin/env python3
import asyncio, hashlib, json, os
from datetime import datetime, timezone
import websockets

WS_URL="wss://futures.mexc.com/edge"
SYMBOLS=["BTC_USDT","ETH_USDT"]
MAX_SECONDS=35
MAX_MESSAGES=500

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def sha_text(s):
    return hashlib.sha256(s.encode("utf-8","replace")).hexdigest()

def valid_index(msg):
    if not isinstance(msg,dict):
        return False
    if msg.get("channel")!="push.index.price":
        return False
    symbol=msg.get("symbol") or (msg.get("data") or {}).get("symbol")
    if symbol not in SYMBOLS:
        return False
    data=msg.get("data")
    if not isinstance(data,dict):
        return False
    try:
        price=float(data.get("price"))
    except Exception:
        return False
    return price>0

async def main():
    os.makedirs("artifacts/mexc_event_futures/v0121",exist_ok=True)
    ev={
        "lab":"MEXC_EVENT_FUTURES_PUBLIC_INDEX_SOURCE_V0.12.1",
        "started_at_utc":now_utc(),
        "ws_url":WS_URL,
        "symbols":SYMBOLS,
        "authenticated":False,
        "private_channels":0,
        "orders":0,
        "account_mutations":0,
        "sent_public_subscriptions":[],
        "index_records":[],
        "event_contract_records":[],
        "other_channels":{},
        "errors":[],
    }

    found=set()
    try:
        async with websockets.connect(
            WS_URL,
            origin="https://www.mexc.com",
            open_timeout=20,
            close_timeout=5,
            ping_interval=15,
            ping_timeout=10,
            max_size=4*1024*1024,
        ) as ws:
            subs=[
                {"method":"sub.index.price","param":{"symbol":"BTC_USDT"}},
                {"method":"sub.index.price","param":{"symbol":"ETH_USDT"}},
                {"method":"sub.event.contract"},
            ]
            for sub in subs:
                raw=json.dumps(sub,separators=(",",":"))
                await ws.send(raw)
                ev["sent_public_subscriptions"].append(sub)

            loop=asyncio.get_running_loop()
            deadline=loop.time()+MAX_SECONDS
            count=0
            while loop.time()<deadline and count<MAX_MESSAGES:
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=min(5,max(0.1,deadline-loop.time())))
                except asyncio.TimeoutError:
                    continue
                count+=1
                recv_at=now_utc()
                if isinstance(raw,bytes):
                    ev["errors"].append({
                        "type":"BINARY_FRAME_UNEXPECTED",
                        "received_at_utc":recv_at,
                        "bytes":len(raw),
                        "sha256":hashlib.sha256(raw).hexdigest(),
                    })
                    continue
                try:
                    msg=json.loads(raw)
                except Exception as e:
                    ev["errors"].append({
                        "type":"NON_JSON_TEXT",
                        "received_at_utc":recv_at,
                        "sha256":sha_text(raw),
                        "preview":raw[:1000],
                        "error":repr(e),
                    })
                    continue

                ch=msg.get("channel") if isinstance(msg,dict) else None
                if valid_index(msg):
                    data=msg.get("data") or {}
                    symbol=msg.get("symbol") or data.get("symbol")
                    rec={
                        "channel":"push.index.price",
                        "symbol":symbol,
                        "price":float(data.get("price")),
                        "server_ts":msg.get("ts"),
                        "received_at_utc":recv_at,
                        "raw_sha256":sha_text(raw),
                    }
                    ev["index_records"].append(rec)
                    found.add(symbol)
                elif ch and "event.contract" in str(ch):
                    ev["event_contract_records"].append({
                        "channel":ch,
                        "symbol":msg.get("symbol"),
                        "server_ts":msg.get("ts"),
                        "received_at_utc":recv_at,
                        "raw_sha256":sha_text(raw),
                        "data":msg.get("data"),
                    })
                elif ch:
                    ev["other_channels"][ch]=ev["other_channels"].get(ch,0)+1

                if found==set(SYMBOLS) and len(ev["index_records"])>=4:
                    # Enough for source proof; preserve a second tick when available.
                    break

            for unsub in [
                {"method":"unsub.index.price","param":{"symbol":"BTC_USDT"}},
                {"method":"unsub.index.price","param":{"symbol":"ETH_USDT"}},
                {"method":"unsub.event.contract"},
            ]:
                try:
                    await ws.send(json.dumps(unsub,separators=(",",":")))
                except Exception:
                    pass
    except Exception as e:
        ev["errors"].append({"type":"WS_EXCEPTION","error":repr(e),"at_utc":now_utc()})

    found={r["symbol"] for r in ev["index_records"]}
    if found==set(SYMBOLS):
        verdict="PUBLIC_INDEX_STREAM_PASS"
    elif found:
        verdict="PARTIAL_INDEX_STREAM"
    else:
        verdict="INDEX_STREAM_BLOCKED"
    ev["verdict"]=verdict
    ev["finished_at_utc"]=now_utc()
    ev["counts"]={
        "index_records":len(ev["index_records"]),
        "symbols_with_index":sorted(found),
        "event_contract_records":len(ev["event_contract_records"]),
        "errors":len(ev["errors"]),
    }

    path="artifacts/mexc_event_futures/v0121/public_index_source_v0121.json"
    with open(path,"w",encoding="utf-8") as f:
        json.dump(ev,f,indent=2,sort_keys=True,ensure_ascii=False)

    print(json.dumps({
        "verdict":verdict,
        "counts":ev["counts"],
        "index_records":ev["index_records"][:12],
        "event_contract_channels":sorted({r["channel"] for r in ev["event_contract_records"]}),
        "safety":{
            "authenticated":False,
            "private_channels":0,
            "orders":0,
            "account_mutations":0,
        },
    },indent=2,sort_keys=True,ensure_ascii=False))
    print("WROTE",path)

    if verdict!="PUBLIC_INDEX_STREAM_PASS":
        raise SystemExit(2)

if __name__=="__main__":
    asyncio.run(main())

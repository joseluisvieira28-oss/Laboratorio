#!/usr/bin/env python3
"""Bybit ETHUSDT market-liveness diagnostic. Does NOT count as liquidation source evidence."""
import asyncio,hashlib,json,pathlib,time
import websockets
ROOT=pathlib.Path("evidence/eth-liveness-v0131");ROOT.mkdir(parents=True,exist_ok=True)
WS="wss://stream.bybit.com/v5/public/linear"
async def main():
    out={"source":WS,"topics":["tickers.ETHUSDT","publicTrade.ETHUSDT"],"ack":False,
         "ticker_messages":0,"trade_messages":0,"errors":[],"evidence":[]}
    try:
        async with websockets.connect(WS,open_timeout=20,ping_interval=None,close_timeout=5,max_size=4*1024*1024) as ws:
            req="v0131-eth-liveness"
            await ws.send(json.dumps({"req_id":req,"op":"subscribe","args":out["topics"]},separators=(",",":")))
            deadline=time.monotonic()+45
            seq=0;last_ping=0.0
            while time.monotonic()<deadline:
                if time.monotonic()-last_ping>=15:
                    await ws.send(json.dumps({"op":"ping"}));last_ping=time.monotonic()
                try: raw=await asyncio.wait_for(ws.recv(),2)
                except asyncio.TimeoutError: continue
                seq+=1;recv=time.time_ns()//1_000_000
                b=raw.encode();sha=hashlib.sha256(b).hexdigest()
                name=f"msg-{seq:06d}.json";(ROOT/name).write_bytes(b)
                out["evidence"].append({"path":name,"sha256":sha,"bytes":len(b),"received_at_ms":recv})
                j=json.loads(raw)
                if j.get("op")=="subscribe" and j.get("req_id")==req:
                    out["ack"]=j.get("success") is True
                topic=str(j.get("topic",""))
                if topic=="tickers.ETHUSDT": out["ticker_messages"]+=1
                if topic=="publicTrade.ETHUSDT": out["trade_messages"]+=1
                if out["ack"] and out["ticker_messages"]>0 and out["trade_messages"]>0: break
    except Exception as e:
        out["errors"].append({"type":type(e).__name__,"error":str(e)})
    out["verdict"]="ETH_MARKET_LIVE" if out["ack"] and (out["ticker_messages"]>0 or out["trade_messages"]>0) and not out["errors"] else "DIAGNOSTIC_BLOCKED"
    out["liquidation_source_gate_credit"]=False
    out["research_outcomes_opened"]=0
    (ROOT/"receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="evidence"},indent=2,sort_keys=True))
    if out["verdict"]!="ETH_MARKET_LIVE": raise SystemExit(2)
asyncio.run(main())

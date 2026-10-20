from __future__ import annotations
import argparse, json, pathlib, time, urllib.request
from datetime import datetime, timezone

RPC="https://ethereum-rpc.publicnode.com"
BINANCE="https://data-api.binance.vision/api/v3/ticker/bookTicker"
SYMBOLS=["ETHUSDT","BTCUSDT","LINKUSDT","DODOUSDT","PEPEUSDT","SHIBUSDT"]
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"forward_data"
OUT.mkdir(parents=True,exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()
def rpc(method,params):
    req=urllib.request.Request(RPC,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001/forward"})
    with urllib.request.urlopen(req,timeout=20) as r: d=json.loads(r.read().decode())
    if d.get("error"): raise RuntimeError(d["error"])
    return d.get("result")
def getj(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-AMM-LVR-001/forward"})
    with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read().decode())
def append(path,obj):
    with path.open("a",encoding="utf-8") as f: f.write(json.dumps(obj,sort_keys=True)+"\n")

ap=argparse.ArgumentParser()
ap.add_argument("--seconds",type=int,default=300)
ap.add_argument("--poll",type=float,default=1.0)
args=ap.parse_args()
deadline=time.monotonic()+args.seconds
last=None
counts={"blocks":0,"transactions":0,"bbo":0,"errors":0}
session={"lab_id":"AMM-LVR-CROSSVENUE-001","started_at_utc":now(),"seconds":args.seconds,"poll":args.poll,"symbols":SYMBOLS}

while time.monotonic()<deadline:
    stamp=now()
    for sym in SYMBOLS:
        try:
            q=getj(f"{BINANCE}?symbol={sym}")
            append(OUT/"cex_bbo.jsonl",{"observed_at_utc":stamp,"symbol":sym,"bid":q["bidPrice"],"bid_qty":q["bidQty"],"ask":q["askPrice"],"ask_qty":q["askQty"]})
            counts["bbo"]+=1
        except Exception as e:
            counts["errors"]+=1; append(OUT/"errors.jsonl",{"at":stamp,"source":"binance","symbol":sym,"error":type(e).__name__+":"+str(e)[:200]})
    try:
        head=int(rpc("eth_blockNumber",[]),16)
        if last is None: last=head-1
        for n in range(last+1,head+1):
            b=rpc("eth_getBlockByNumber",[hex(n),True])
            if not b: continue
            rec={"observed_at_utc":now(),"block_number":n,"block_hash":b.get("hash"),"block_timestamp":int(b["timestamp"],16),"base_fee_per_gas":int(b.get("baseFeePerGas","0x0"),16),"tx_count":len(b.get("transactions",[]))}
            append(OUT/"eth_blocks.jsonl",rec); counts["blocks"]+=1
            for tx in b.get("transactions",[]):
                append(OUT/"eth_transactions.jsonl",{"block_number":n,"block_timestamp":rec["block_timestamp"],"tx_hash":tx.get("hash"),"from":tx.get("from"),"to":tx.get("to"),"gas":int(tx.get("gas","0x0"),16),"gas_price":int(tx.get("gasPrice","0x0"),16) if tx.get("gasPrice") else None,"max_fee_per_gas":int(tx.get("maxFeePerGas","0x0"),16) if tx.get("maxFeePerGas") else None,"max_priority_fee_per_gas":int(tx.get("maxPriorityFeePerGas","0x0"),16) if tx.get("maxPriorityFeePerGas") else None,"input_prefix":(tx.get("input") or "")[:18]})
                counts["transactions"]+=1
        last=max(last,head)
    except Exception as e:
        counts["errors"]+=1; append(OUT/"errors.jsonl",{"at":stamp,"source":"ethereum","error":type(e).__name__+":"+str(e)[:300]})
    time.sleep(args.poll)

session.update({"ended_at_utc":now(),"counts":counts,"last_block":last,"economic_outcomes_opened":False,"orders_submitted":0,"wallet_mutations":0})
append(OUT/"sessions.jsonl",session)
print(json.dumps(session,indent=2,sort_keys=True))

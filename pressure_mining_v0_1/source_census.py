#!/usr/bin/env python3
import json, hashlib, os, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from eth_hash.auto import keccak

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def fetch_json(url, method="GET", data=None, timeout=90):
    headers={"User-Agent":"CryptoLab-PressureMining-Census-V0.1","Accept":"application/json"}
    body=None if data is None else json.dumps(data).encode()
    if body is not None: headers["Content-Type"]="application/json"
    req=Request(url,data=body,headers=headers,method=method)
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return json.loads(b.decode()), sha256_bytes(b)

RPC_ENDPOINTS=[
    "https://ethereum-rpc.publicnode.com",
    "https://rpc.flashbots.net",
    "https://eth.llamarpc.com"
]

def rpc(endpoint, method, params):
    j,_=fetch_json(endpoint,method="POST",data={"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout=90)
    if "error" in j: raise RuntimeError(str(j["error"]))
    return j["result"]

def choose_rpc():
    errs=[]
    for ep in RPC_ENDPOINTS:
        try:
            if rpc(ep,"eth_chainId",[])=="0x1":
                return ep,errs
        except Exception as e: errs.append({"endpoint":ep,"error":repr(e)})
    raise RuntimeError(f"no Ethereum RPC: {errs}")

def block_timestamp(ep,n):
    b=rpc(ep,"eth_getBlockByNumber",[hex(n),False])
    return int(b["timestamp"],16)

def first_block_at_or_after(ep,target_ts):
    hi=int(rpc(ep,"eth_blockNumber",[]),16)
    lo=0
    while lo<hi:
        mid=(lo+hi)//2
        ts=block_timestamp(ep,mid)
        if ts<target_ts: lo=mid+1
        else: hi=mid
    return lo

def topic(sig):
    return "0x"+keccak(sig.encode()).hex()

def get_logs_adaptive(ep,address,topics,start,end):
    all_logs=[]
    cur=start
    chunk=100000
    failures=0
    while cur<=end:
        stop=min(end,cur+chunk-1)
        try:
            logs=rpc(ep,"eth_getLogs",[{"address":address,"fromBlock":hex(cur),"toBlock":hex(stop),"topics":[topics]}])
            all_logs.extend(logs)
            cur=stop+1
            if chunk<100000: chunk=min(100000,chunk*2)
        except Exception:
            failures+=1
            if chunk<=2000: raise
            chunk=max(2000,chunk//2)
    return all_logs,failures

receipt={
 "program":"PRESSURE_MINING_SOURCE_CENSUS_V0.1",
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "firewall":{
   "source_only":True,"price_returns_opened":False,"pnl_computed":False,
   "protected_holdout_opened":False,"live_trading":False,"orders":False,
   "exchange_mutation":False,"paid_data":False
 },
 "compound":{},
 "pendle":{}
}

# Compound event census: 2023-01-01 through 2024-12-31 only.
try:
    roots,_=fetch_json("https://raw.githubusercontent.com/compound-finance/comet/main/deployments/mainnet/usdc/roots.json")
    comet=roots["comet"]
    ep,ep_errs=choose_rpc()
    t0=int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp())
    t1=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())-1
    b0=first_block_at_or_after(ep,t0)
    b1=first_block_at_or_after(ep,t1)
    absorb=topic("AbsorbCollateral(address,address,address,uint256,uint256)")
    buy=topic("BuyCollateral(address,address,uint256,uint256)")
    logs,failures=get_logs_adaptive(ep,comet,[absorb,buy],b0,b1)
    counts={"AbsorbCollateral":0,"BuyCollateral":0,"other":0}
    unique_assets=set()
    unique_borrowers=set()
    for lg in logs:
        t=(lg.get("topics") or [None])[0]
        if t and t.lower()==absorb.lower():
            counts["AbsorbCollateral"]+=1
            if len(lg["topics"])>2: unique_borrowers.add("0x"+lg["topics"][2][-40:])
            if len(lg["topics"])>3: unique_assets.add("0x"+lg["topics"][3][-40:])
        elif t and t.lower()==buy.lower():
            counts["BuyCollateral"]+=1
            if len(lg["topics"])>2: unique_assets.add("0x"+lg["topics"][2][-40:])
        else: counts["other"]+=1
    receipt["compound"]={
      "lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001",
      "status":"SOURCE_CENSUS_PASS",
      "rpc":ep,
      "rpc_prior_errors":ep_errs,
      "comet_address":comet,
      "window_utc":["2023-01-01T00:00:00Z","2024-12-31T23:59:59Z"],
      "block_range":[b0,b1],
      "event_topics":{"AbsorbCollateral":absorb,"BuyCollateral":buy},
      "event_counts":counts,
      "unique_assets":len(unique_assets),
      "unique_absorbed_borrowers_lower_bound":len(unique_borrowers),
      "adaptive_query_failures":failures,
      "sample_viability_note":"Counts are source feasibility only. No market response or economic result computed."
    }
except Exception as e:
    receipt["compound"]={"lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001","status":"SOURCE_CENSUS_PARTIAL","error":repr(e)}

# Pendle metadata census only. No price/convergence values are read into the receipt.
try:
    allm=[]
    skip=0
    for _ in range(20):
        url=f"https://api-v2.pendle.finance/core/v2/markets/all?limit=100&skip={skip}"
        j,_=fetch_json(url,timeout=120)
        rows=j.get("results") if isinstance(j,dict) else None
        if not isinstance(rows,list): break
        allm.extend(rows)
        if len(rows)<100: break
        skip+=100
    cutoff=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())
    def norm_exp(v):
        if isinstance(v,(int,float)): return int(v/1000) if v>10_000_000_000 else int(v)
        if isinstance(v,str):
            try:
                if v.isdigit(): return norm_exp(int(v))
                return int(datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
            except Exception: return None
        return None
    eth=[]
    expired=[]
    for m in allm:
        cid=m.get("chainId") or m.get("chain_id") or (m.get("chain") or {}).get("id") if isinstance(m,dict) else None
        if str(cid)!="1": continue
        eth.append(m)
        exp=norm_exp(m.get("expiry") or m.get("expiryTimestamp") or m.get("expiration"))
        if exp is not None and exp<cutoff: expired.append((m,exp))
    samples=[]
    for m,exp in expired[:10]:
        addr=m.get("address")
        if not isinstance(addr,str): continue
        try:
            h,_=fetch_json(f"https://api-v2.pendle.finance/core/v3/1/markets/{addr}/historical-data",timeout=120)
            samples.append({
              "address":addr,
              "expiry_ts":exp,
              "historical_total":h.get("total") if isinstance(h,dict) else None,
              "timestamp_start":h.get("timestamp_start") if isinstance(h,dict) else None,
              "timestamp_end":h.get("timestamp_end") if isinstance(h,dict) else None
            })
        except Exception as inner:
            samples.append({"address":addr,"expiry_ts":exp,"error":repr(inner)})
    receipt["pendle"]={
      "lab_id":"PENDLE-PT-MATURITY-CONVERGENCE-001",
      "status":"SOURCE_CENSUS_PASS" if len(allm)>0 else "SOURCE_CENSUS_PARTIAL",
      "markets_enumerated":len(allm),
      "ethereum_markets":len(eth),
      "ethereum_markets_expired_before_2025":len(expired),
      "historical_coverage_probes":samples,
      "sample_viability_note":"Metadata/coverage only. No PT convergence performance, returns or PnL computed."
    }
except Exception as e:
    receipt["pendle"]={"lab_id":"PENDLE-PT-MATURITY-CONVERGENCE-001","status":"SOURCE_CENSUS_PARTIAL","error":repr(e)}

raw=json.dumps(receipt,sort_keys=True,indent=2).encode()
receipt["receipt_sha256_pre_self_field"]=sha256_bytes(raw)
out=os.path.join(OUTDIR,"PRESSURE_MINING_SOURCE_CENSUS_RECEIPT_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
print(f"receipt={out}")

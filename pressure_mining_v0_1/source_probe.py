#!/usr/bin/env python3
import json, hashlib, os, sys, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def fetch(url, method="GET", data=None, timeout=45, headers=None):
    h={"User-Agent":"CryptoLab-PressureMining-V0.1","Accept":"application/json"}
    if headers: h.update(headers)
    body=None if data is None else json.dumps(data).encode()
    if body is not None: h["Content-Type"]="application/json"
    req=Request(url,data=body,headers=h,method=method)
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return {"status":r.status,"headers":dict(r.headers),"body":b,"sha256":sha256_bytes(b)}

def fetch_json(url, **kw):
    r=fetch(url,**kw)
    r["json"]=json.loads(r["body"].decode())
    return r

RPC="https://ethereum-rpc.publicnode.com"
def rpc(method, params):
    r=fetch_json(RPC,method="POST",data={"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout=60)
    j=r["json"]
    if "error" in j:
        raise RuntimeError(f"{method}: {j['error']}")
    return j["result"], r["sha256"]

receipt={
  "program":"PRESSURE_MINING_PROGRAM_V0.1",
  "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "firewall":{
    "source_only":True,
    "market_outcomes_opened":False,
    "returns_computed":False,
    "pnl_computed":False,
    "protected_holdout_opened":False,
    "live_trading":False,
    "orders":False,
    "exchange_mutation":False,
    "paid_data":False
  },
  "probes":{}
}

# 1) Compound III source feasibility
compound={"lab_id":"COMPOUND-INVENTORY-LIQUIDATION-001","status":"SOURCE_BLOCKED"}
try:
    roots_url="https://raw.githubusercontent.com/compound-finance/comet/main/deployments/mainnet/usdc/roots.json"
    roots=fetch_json(roots_url)
    comet=roots["json"]["comet"]
    schema_url="https://raw.githubusercontent.com/compound-finance/comet/main/contracts/CometMainInterface.sol"
    schema=fetch(schema_url)
    txt=schema["body"].decode(errors="replace")
    events={"AbsorbCollateral":("event AbsorbCollateral" in txt),"BuyCollateral":("event BuyCollateral" in txt)}
    chain,chain_sha=rpc("eth_chainId",[])
    latest_hex,_=rpc("eth_blockNumber",[])
    code,code_sha=rpc("eth_getCode",[comet,"latest"])
    latest=int(latest_hex,16)
    start=max(0,latest-200)
    logs,logs_sha=rpc("eth_getLogs",[{"address":comet,"fromBlock":hex(start),"toBlock":latest_hex}])
    compound.update({
      "status":"SOURCE_FEASIBILITY_PASS" if code not in ("0x","0x0") and all(events.values()) else "SOURCE_PARTIAL",
      "official_roots_url":roots_url,
      "official_roots_sha256":roots["sha256"],
      "comet_address":comet,
      "official_schema_url":schema_url,
      "official_schema_sha256":schema["sha256"],
      "event_schema_present":events,
      "chain_id":chain,
      "latest_block":latest,
      "code_present":code not in ("0x","0x0"),
      "recent_log_query_blocks":200,
      "recent_logs_returned":len(logs),
      "rpc_receipt_sha256":logs_sha
    })
except Exception as e:
    compound["error"]=repr(e)
receipt["probes"]["compound"]=compound

# 2) Lido queue source accessibility only; no market response
lido={"lab_id":"LIDO-WITHDRAWAL-QUEUE-PRESSURE-001","status":"SOURCE_BLOCKED"}
try:
    queue="0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1"
    activation=17266004
    code,code_sha=rpc("eth_getCode",[queue,"latest"])
    hist_logs,hist_sha=rpc("eth_getLogs",[{"address":queue,"fromBlock":hex(activation),"toBlock":hex(activation+500)}])
    lido.update({
      "status":"SOURCE_PASS_PROSPECTIVE_ONLY" if code not in ("0x","0x0") else "SOURCE_PARTIAL",
      "queue_address":queue,
      "canonical_activation_block_from_prior_authority":activation,
      "code_present":code not in ("0x","0x0"),
      "historical_probe_blocks":500,
      "historical_logs_returned":len(hist_logs),
      "historical_log_query_pass":True,
      "rpc_receipt_sha256":hist_sha,
      "contamination_note":"2023-2024 market-response outcomes remain prohibited for new ID; source accessibility only."
    })
except Exception as e:
    lido["error"]=repr(e)
receipt["probes"]["lido"]=lido

# 3) Pendle public API source feasibility
pendle={"lab_id":"PENDLE-PT-MATURITY-CONVERGENCE-001","status":"SOURCE_BLOCKED"}
try:
    markets_url="https://api-v2.pendle.finance/core/v2/markets/all?limit=100&skip=0"
    mk=fetch_json(markets_url,timeout=120)
    j=mk["json"]
    candidates=[]
    def walk(x):
        if isinstance(x,dict):
            if isinstance(x.get("address"),str):
                cid=x.get("chainId") or x.get("chain_id")
                if cid is None and isinstance(x.get("chain"),dict): cid=x["chain"].get("id")
                candidates.append((cid,x.get("address"),x))
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(j)
    chosen=None
    for cid,addr,obj in candidates:
        if str(cid)=="1" and isinstance(addr,str) and addr.startswith("0x"):
            chosen=(cid,addr,obj); break
    hist_pass=False; hist_summary=None; hist_sha=None
    if chosen:
        cid,addr,obj=chosen
        hist_url=f"https://api-v2.pendle.finance/core/v3/{cid}/markets/{addr}/historical-data"
        hist=fetch_json(hist_url,timeout=120)
        hist_pass=True
        hj=hist["json"]
        if isinstance(hj,dict):
            hist_summary={"top_level_keys":sorted(hj.keys())[:50]}
        elif isinstance(hj,list):
            hist_summary={"list_len":len(hj)}
        hist_sha=hist["sha256"]
    pendle.update({
      "status":"SOURCE_FEASIBILITY_PASS" if len(candidates)>0 and hist_pass else "SOURCE_PARTIAL",
      "markets_endpoint":markets_url,
      "markets_payload_sha256":mk["sha256"],
      "address_like_records_found":len(candidates),
      "selected_probe_market":{"chain_id":chosen[0],"address":chosen[1]} if chosen else None,
      "historical_endpoint_pass":hist_pass,
      "historical_payload_sha256":hist_sha,
      "historical_schema_summary":hist_summary
    })
except Exception as e:
    pendle["error"]=repr(e)
receipt["probes"]["pendle"]=pendle

# 4) Morpho comparison probe — no LAB opened
morpho={"routing":"NO_LAB_OPENED_DUPLICATE_RISK","status":"SOURCE_BLOCKED"}
try:
    url="https://api.morpho.org/v1/blue/markets?limit=3"
    m=fetch_json(url,timeout=60)
    mj=m["json"]
    morpho.update({
      "status":"SOURCE_FEASIBILITY_PASS",
      "endpoint":url,
      "payload_sha256":m["sha256"],
      "schema_type":type(mj).__name__,
      "note":"Source quality confirmed only. Simple HF/liquidation port remains rejected by novelty gate."
    })
except Exception as e:
    morpho["error"]=repr(e)
receipt["probes"]["morpho"]=morpho

raw=json.dumps(receipt,sort_keys=True,indent=2).encode()
receipt["receipt_sha256_pre_self_field"]=sha256_bytes(raw)
out=os.path.join(OUTDIR,"PRESSURE_MINING_SOURCE_PROBE_RECEIPT_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2)
    f.write("\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
print(f"receipt={out}")

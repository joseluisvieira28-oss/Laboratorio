#!/usr/bin/env python3
"""LP-NET-002 third-party source check: bounded no-key Blockscout v2 API.
Checks three *already frozen* Ethereum tx hashes vs Routescan receipt data.
Never trades and never promotes economic PnL.
"""
import argparse,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

BASE="https://eth.blockscout.com/api/v2/transactions/"
MANAGER="0xc36442b4a4522e871399cd717abdd847ab11fe88"
DECLARED=[
 {"token_id":102244,"block":12964997,"txhash":"0x3b058c2b32cbad853282fc6a4c4e19e4ab8407ae617c96c55b12a2a631c55d92","gas_used":221070,"gas_price_wei":27000000000,"indexes":[276,280]},
 {"token_id":107633,"block":15092225,"txhash":"0x710bcc27d0cf34657dc68816752c9b0804dc3e08075105abebe39e446cebb723","gas_used":221068,"gas_price_wei":41520233632,"indexes":[201,205]},
 {"token_id":106475,"block":17948957,"txhash":"0x5c2b52327b1933bfd72cd24bfabb7089cb43960c364d3e9536041386eb9fab7c","gas_used":221094,"gas_price_wei":13240062119,"indexes":[272,276]},
]

def load(url):
    if not url.startswith(BASE):raise ValueError("API host not allowlisted")
    req=Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-LP-NET-002/1.0"})
    with urlopen(req,timeout=12) as resp:data=resp.read(400000)
    return json.loads(data)

def intval(x):
    if isinstance(x,dict):return intval(x.get("value"))
    if isinstance(x,int):return x
    if isinstance(x,str) and x.strip():return int(x,0) if x.startswith("0x") else int(x)
    raise ValueError("Non-integer API value")

def verify(t):
    tx=load(BASE+t["txhash"])
    if not isinstance(tx,dict):raise ValueError("Invalid tx record")
    if tx.get("hash","").lower()!=t["txhash"]:raise ValueError("Tx hash mismatch")
    if intval(tx.get("block_number",tx.get("block")))!=t["block"]:raise ValueError("Tx block mismatch")
    result={"transaction_hash":t["txhash"],"token_id":t["token_id"],"block":t["block"],
            "transaction_source":"Blockscout v2","tx_meta_provenance":"SEPARATE_INDEXER",
            "status":str(tx.get("status")),"gas_used":None,"gas_price_wei":None,
            "gas_agrees_routescan":False,"log_indexes_found":[]}
    gas=intval(tx["gas_used"]);price=intval(tx["gas_price"])
    result["gas_used"]=gas;result["gas_price_wei"]=price
    result["gas_agrees_routescan"]=(gas==t["gas_used"] and price==t["gas_price_wei"])
    try:
        logs=load(BASE+t["txhash"]+"/logs")
        items=logs.get("items",[]) if isinstance(logs,dict) else []
        if not isinstance(items,list):items=[]
        indexes=[]
        for item in items:
            addr=item.get("address")
            addr=(addr.get("hash") if isinstance(addr,dict) else addr)
            if (addr or "").lower()!=MANAGER:continue
            try:
                idx=intval(item.get("index",item.get("log_index")))
            except ValueError:continue
            if idx in t["indexes"]:
                indexes.append(idx)
        result["log_indexes_found"]=sorted(set(indexes))
    except (OSError,ValueError,KeyError,TypeError) as err:
        result["logs_unavailable_reason"]=type(err).__name__+":"+str(err)[:100]
    result["independent_tx_gas_confirmed"]=(result["gas_agrees_routescan"] and
                                      str(tx.get("status","")).lower() in ("ok","success","1"))
    result["same_two_manager_log_indexes_confirmed"]=set(result["log_indexes_found"])==set(t["indexes"])
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out={"study":"LP-NET-002-BLOCKSCOUT-INDEPENDENT-INDEXER","no_private_keys":True,
         "no_orders":True,"capital_used_chf":0,"economic_verdict":"NO_LIVE_GO","targets":[]}
    for t in DECLARED:
        try:out["targets"].append(verify(t))
        except (OSError,ValueError,KeyError,TypeError,RuntimeError,HTTPError,URLError) as err:
            out["targets"].append({"token_id":t["token_id"],"status":"SECOND_SOURCE_BLOCKED",
                 "reason":type(err).__name__+":"+str(err)[:170]})
    out["verified_independent_tx_gas"]=sum(x.get("independent_tx_gas_confirmed",False) for x in out["targets"])
    out["verified_independent_two_log_indexes"]=sum(x.get("same_two_manager_log_indexes_confirmed",False) for x in out["targets"])
    out["full_position_economic_pnl_usd"]=None
    out["next_gate"]="Full-lifecycle NFT state and independent historical token+ETH USD pricing, not single withdrawal tx."
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"independent_tx_gas":out["verified_independent_tx_gas"],
                      "independent_log_pairs":out["verified_independent_two_log_indexes"],
                      "economic_verdict":out["economic_verdict"]}))
if __name__=="__main__":main()

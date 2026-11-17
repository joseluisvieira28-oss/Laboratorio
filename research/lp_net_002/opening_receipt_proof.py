#!/usr/bin/env python3
"""LP-NET-002 source proof of three already frozen NFT opening transactions.
Read-only, exact logs and independent explorer metadata; not economic PnL.
"""
import argparse,json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode

BASE="https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"
BLOCKSCOUT="https://eth.blockscout.com/api/v2/transactions/"
MANAGER="0xc36442b4a4522e871399cd717abdd847ab11fe88"
POOL="0x6c6bc977e13df9b0de53b251522280bb72383700"
POOL_MINT="0x7a53080ba414158be7ec69b987b5fb7d07dee101fee854cb46c5bde7cfbca2e6"

def get_json(url):
    r=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-002-MINT/0.1"})
    with urlopen(r,timeout=15) as resp:return json.loads(resp.read(1500000))
def num(s):
    if isinstance(s,int):return s
    return int(s,16) if isinstance(s,str) and s.startswith("0x") else int(s)
def abi(s):
    if not isinstance(s,str) or not s.startswith("0x") or (len(s)-2)%64:raise ValueError("invalid ABI")
    return [int(s[i:i+64],16) for i in range(2,len(s),64)]
def archive_receipt(txhash):
    q=urlencode({"module":"proxy","action":"eth_getTransactionReceipt","txhash":txhash})
    body=get_json(BASE+"?"+q)
    r=body.get("result") if isinstance(body,dict) else None
    if not isinstance(r,dict):raise ValueError("No Routescan transaction receipt")
    if r.get("transactionHash","").lower()!=txhash:raise ValueError("Transaction hash mismatch")
    if num(r["status"])!=1:raise ValueError("Transaction not successful")
    return r

def proof(target):
    logs=target.get("lp_logs",{}).get("events",[])
    transfers=target.get("transfer_logs",{}).get("events",[])
    inc=[x for x in logs if x.get("name")=="IncreaseLiquidity"]
    if len(inc)!=1 or len(transfers)!=1:raise ValueError("Not a single mint/transfer")
    entry=inc[0];tr=transfers[0]
    if tr["txhash"]!=entry["txhash"] or tr["block"]!=entry["block"]:
        raise ValueError("Initial transfer does not match initial increase tx")
    r=archive_receipt(entry["txhash"])
    if num(r["blockNumber"])!=entry["block"]:raise ValueError("Wrong receipt block")
    all_logs=r.get("logs",[])
    def match(x):
        return [v for v in all_logs if v.get("address","").lower()==MANAGER and
           num(v["logIndex"])==x["log_index"] and
           v.get("topics")==x["topics"] and v.get("data")==x.get("data")]
    if len(match(entry))!=1 or len(match(tr))!=1:
        raise ValueError("NFT increase or mint transfer not proven by receipt")
    change=abi(entry["data"])
    if len(change)!=3:raise ValueError("Increase ABI mismatch")
    pool=[]
    for v in all_logs:
        if v.get("address","").lower()==POOL and v.get("topics",[]):
            if v["topics"][0].lower()==POOL_MINT:
                vals=abi(v.get("data"))
                if len(vals)!=4:raise ValueError("Pool Mint ABI mismatch")
                if vals[1:]==change:pool.append(v)
    if len(pool)!=1:raise ValueError("No exactly-matched DAI/USDC pool mint in receipt")
    token_id=target["token_id"]
    if num(tr["topics"][3])!=token_id:raise ValueError("NFT transfer id mismatch")
    owner_from="0x"+tr["topics"][1][-40:]
    owner_to="0x"+tr["topics"][2][-40:]
    if owner_from!="0x"+"0"*40:raise ValueError("Not a creation transfer from zero")
    b=get_json(BLOCKSCOUT+entry["txhash"])
    if not isinstance(b,dict) or b.get("hash","").lower()!=entry["txhash"] or num(b["block_number"])!=entry["block"]:
        raise ValueError("Independent Blockscout tx not same")
    gas=num(r["gasUsed"]);price=num(r["effectiveGasPrice"])
    if num(b["gas_used"])!=gas or num(b["gas_price"])!=price:
        raise ValueError("Independent tx gas mismatch")
    b_logs=get_json(BLOCKSCOUT+entry["txhash"]+"/logs")
    b_index=set()
    for obj in b_logs.get("items",[]):
        addr=obj.get("address")
        addr=addr.get("hash") if isinstance(addr,dict) else addr
        if (addr or "").lower()==MANAGER:b_index.add(num(obj.get("index",obj.get("log_index"))))
    if entry["log_index"] not in b_index or tr["log_index"] not in b_index:
        raise ValueError("Independent manager event index missing")
    return {"token_id":token_id,"opening_tx_hash":entry["txhash"],"block":entry["block"],
       "mint_transfer_from_zero":True,"initial_owner":owner_to,
       "manager_increase_log_index":entry["log_index"],
       "nft_mint_transfer_log_index":tr["log_index"],
       "pool_mint_log_index":num(pool[0]["logIndex"]),
       "matching_pool_address":POOL,"matching_pool_mint_liquidity_raw":change[0],
       "amount_DAI":str(change[1]/10**18),"amount_USDC":str(change[2]/10**6),
       "amount0_raw":str(change[1]),"amount1_raw":str(change[2]),
       "gas_used_whole_tx":gas,"effective_gas_price_wei":price,
       "whole_entry_tx_cost_eth":str(gas*price/10**18),
       "source":"Routescan receipt + independent Blockscout tx, manager indexes",
       "status":"ENTRY_EVENT_POOL_MINT_AND_TX_GAS_TWO_INDEXERS"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--lifecycle",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);a=p.parse_args()
    d=json.loads(a.lifecycle.read_text())
    out={"study":"LP-NET-002-ENTRY-POOL-VERIFICATION",
       "no_orders":True,"no_wallet":True,"capital_chf":0,
       "economic_verdict":"NO_LIVE_GO","results":[]}
    for t in d["targets"]:
        try:out["results"].append(proof(t))
        except (OSError,RuntimeError,ValueError,TypeError,KeyError) as exc:
            out["results"].append({"token_id":t["token_id"],
                 "status":"ENTRY_PROOF_BLOCKED","reason":type(exc).__name__+":"+str(exc)[:170]})
        time.sleep(.6)
    out["pool_mints_and_gas_independently_verified"]=sum(
        x.get("status")=="ENTRY_EVENT_POOL_MINT_AND_TX_GAS_TWO_INDEXERS" for x in out["results"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"opening_txs_verified":out["pool_mints_and_gas_independently_verified"],
                      "economic_verdict":out["economic_verdict"]}))
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Read-only, bounded historic NFT log probe via independent indexed explorers.
Candidate logs are NOT receipt-verified LP economics, and require corroboration.
"""
import argparse,hashlib,json,time
from decimal import Decimal
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode

MANAGER="0xc36442b4a4522e871399cd717abdd847ab11fe88"
BASES=("https://eth.blockscout.com/api",
       "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api")
TARGETS=((102244,12964997),(107633,15092225),(106475,17948957))
SIGNATURES={
"0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f":"IncreaseLiquidity",
"0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4":"DecreaseLiquidity",
"0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01":"Collect"}

def fetch(base,tid,block):
    params={"module":"logs","action":"getLogs","fromBlock":str(block),"toBlock":str(block),
            "address":MANAGER,"topic1":"0x"+format(tid,"064x"),"page":"1","offset":"100"}
    url=base+"?"+urlencode(params)
    req=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-002-indexed/0.1"})
    with urlopen(req,timeout=15) as resp:body=resp.read(500000)
    js=json.loads(body)
    if not isinstance(js,dict) or not isinstance(js.get("result"),list):
        return {"status":"SOURCE_NO_CANONICAL_LOG_LIST","api_message":str(js.get("message",""))[:150],
                "body_sha256":hashlib.sha256(body).hexdigest()}
    logs=[]
    for item in js["result"]:
        topics=item.get("topics",[])
        if item.get("address","").lower()!=MANAGER or len(topics)<2:continue
        if topics[0].lower() not in SIGNATURES or int(topics[1],16)!=tid:continue
        if int(item["blockNumber"],16)!=block:continue
        logs.append({"kind":SIGNATURES[topics[0].lower()],
                     "tx_hash":item["transactionHash"].lower(),
                     "block_hash":item.get("blockHash"),
                     "log_index":int(item["logIndex"],16),
                     "topics":topics,"raw_data":item.get("data")})
    return {"status":"UNVERIFIED_INDEXED_LOGS" if logs else "API_NO_LOGS_NOT_PROOF",
            "body_sha256":hashlib.sha256(body).hexdigest(),"logs":logs}

def verify_receipt(base,log):
    from urllib.request import Request,urlopen
    from urllib.parse import urlencode
    query={"module":"proxy","action":"eth_getTransactionReceipt","txhash":log["tx_hash"]}
    url=base+"?"+urlencode(query)
    req=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-002-receipt/0.1"})
    with urlopen(req,timeout=15) as resp:raw=resp.read(1500000)
    doc=json.loads(raw);receipt=doc.get("result") if isinstance(doc,dict) else None
    if not isinstance(receipt,dict):raise ValueError("Proxy has no receipt object: "+str(doc.get("message",""))[:100])
    if int(receipt.get("status","0x0"),16)!=1:raise ValueError("Transaction not successful")
    if receipt.get("transactionHash","").lower()!=log["tx_hash"]:raise ValueError("Receipt txhash disagrees")
    if receipt.get("blockHash","").lower()!=log["block_hash"].lower():raise ValueError("Receipt block disagrees")
    proof=[x for x in receipt.get("logs",[])
           if x.get("address","").lower()==MANAGER
           and int(x.get("logIndex","0x0"),16)==log["log_index"]
           and x.get("topics")==log["topics"] and x.get("data")==log["raw_data"]]
    if len(proof)!=1:raise ValueError("Indexed log not exactly replicated in receipt")
    gas=int(receipt["gasUsed"],16);price=int(receipt["effectiveGasPrice"],16)
    return {"status":"TX_RECEIPT_LOG_VERIFIED_ONE_SOURCE","receipt_sha256":hashlib.sha256(raw).hexdigest(),
            "gas_used":gas,"gas_price_wei":price,
            "whole_transaction_fee_eth":str(Decimal(gas)*Decimal(price)/Decimal(10**18)),
            "is_gas_attributable_to_single_position":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    out={"study":"LP-NET-002-INDEXED","permissions":"READ_ONLY","capital_chf":0,
         "pnl_usd":None,"economic_gate":"NO_LIVE_GO","targets":[]}
    for token_id,block in TARGETS:
        row={"token_id":token_id,"burn_block":block,"source_attempts":[]}
        for base in BASES:
            try:
                item={"provider":base,**fetch(base,token_id,block)}
                if item.get("logs"):
                    # The indexed log is not a receipt; verify independently at txhash endpoint.
                    for log in item["logs"]:
                        if base.startswith("https://api.routescan.io/"):
                            try:
                                time.sleep(.6) # provider's documented keyless 2 requests/sec
                                log["receipt_verification"]=verify_receipt(base,log)
                            except (OSError,ValueError,KeyError,TypeError,RuntimeError) as err:
                                log["receipt_verification"]={"status":"RECEIPT_SOURCE_BLOCKED",
                                    "error_type":type(err).__name__,"reason":str(err)[:170]}
                row["source_attempts"].append(item)
            except (OSError,ValueError,KeyError,TypeError,RuntimeError) as err:
                row["source_attempts"].append({"provider":base,"status":"SOURCE_BLOCKED",
                    "error_type":type(err).__name__,"message":str(err)[:170]})
        out["targets"].append(row)
    out["status"]="INDEXED_CANDIDATES_NOT_VERIFIED" if any(
       x.get("logs") for t in out["targets"] for x in t["source_attempts"]) else "SOURCE_BLOCKED_OR_NOT_FOUND"
    out["receipts_verified"] = sum(1 for t in out["targets"] for a in t["source_attempts"]
       for log in a.get("logs",[]) if log.get("receipt_verification",{}).get("status")=="TX_RECEIPT_LOG_VERIFIED_ONE_SOURCE")
    out["next_gate"]="Independent second data source + NFT/factory binding + full lifecycle, then cost-adjusted HODL, before any economic PnL."
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":out["status"],"candidate_logs":sum(
        len(x.get("logs",[])) for t in out["targets"] for x in t["source_attempts"]),
        "receipts_verified":out["receipts_verified"],"economic_gate":out["economic_gate"]}))
if __name__=="__main__":main()

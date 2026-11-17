#!/usr/bin/env python3
"""Diagnosis only: search all pool Mint logs and pool-specific logs in minted NFT receipts.
Read-only. Never override source identity gate from heuristic matches.
"""
import argparse,json,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from opening_receipt_proof import BASE,MANAGER,POOL,POOL_MINT,abi
def load(tx):
    url=BASE+"?"+urlencode({"module":"proxy","action":"eth_getTransactionReceipt","txhash":tx})
    with urlopen(Request(url,headers={"User-Agent":"LP-NET-002-POOL-DIAG/0.1"}),timeout=15) as r:
        d=json.loads(r.read(1500000))
    z=d.get("result")
    if not isinstance(z,dict):raise ValueError("no receipt")
    return z
def main():
    p=argparse.ArgumentParser();p.add_argument("--lifecycle",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    d=json.loads(a.lifecycle.read_text());out={"status":"SOURCE_FORENSIC_ONLY","items":[]}
    for item in d["targets"]:
        inc=next(x for x in item["lp_logs"]["events"] if x["name"]=="IncreaseLiquidity")
        evidence={"nft":item["token_id"],"tx":inc["txhash"],"expected_pool":POOL,
                  "manager_amount_words":abi(inc["data"])}
        try:
            rc=load(inc["txhash"])
            logs=rc["logs"];evidence["receipt_log_count"]=len(logs)
            candidates=[]
            for v in logs:
                addr=v.get("address","").lower()
                t=(v.get("topics") or [None])[0]
                is_pool=(addr==POOL);is_mint=(t or "").lower()==POOL_MINT
                if not is_pool and not is_mint:continue
                datum=v.get("data","0x");words=abi(datum) if datum.startswith("0x") else []
                candidates.append({"address":addr,"topic0":t,"log_index":int(v["logIndex"],16),
                    "pool_address_matches":is_pool,"mint_topic_matches":is_mint,
                    "data_word_count":len(words),
                    "last_three_words_match_manager_increase":words[-3:]==evidence["manager_amount_words"],
                    "data_words_tail":words[-4:]})
            evidence["candidates"]=candidates
            evidence["event_topic0_counts"]={}
            for v in logs:
                topic=(v.get("topics") or [None])[0]
                k=str(topic).lower()
                evidence["event_topic0_counts"][k]=evidence["event_topic0_counts"].get(k,0)+1
        except (OSError,ValueError,KeyError,TypeError) as err:
            evidence["error"]=type(err).__name__+":"+str(err)[:150]
        out["items"].append(evidence);time.sleep(.6)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_counts":[len(x.get("candidates",[])) for x in out["items"]]}))
if __name__=="__main__":main()

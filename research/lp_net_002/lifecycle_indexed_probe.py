#!/usr/bin/env python3
"""Bounded, read-only manager logs for the full *claimed* NFT lifecycle.
Indexed API evidence, not an independent full Ethereum node or fee PnL.
"""
import argparse,hashlib,json,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

BASE="https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"
MANAGER="0xc36442b4a4522e871399cd717abdd847ab11fe88"
TOPIC_TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOPIC={
"0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f":"IncreaseLiquidity",
"0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4":"DecreaseLiquidity",
"0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01":"Collect",
TOPIC_TRANSFER:"Transfer"}
TARGETS=((102244,12964997),(107633,15092225),(106475,17948957))
PER_PAGE=100
MAX_PAGES=4

def fetch(params):
    url=BASE+"?"+urlencode(params)
    request=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-002-LIFECYCLE/0.1"})
    with urlopen(request,timeout=15) as response:body=response.read(700000)
    val=json.loads(body)
    if not isinstance(val,dict) or not isinstance(val.get("result"),list):
        raise ValueError("API cannot guarantee full log range: "+str(val.get("message",""))[:130])
    return val["result"],hashlib.sha256(body).hexdigest()

def get_logs(tid,stop,kind):
    ret=[];digests=[];complete=False
    for page in range(1,MAX_PAGES+1):
        params={"module":"logs","action":"getLogs","address":MANAGER,"fromBlock":0,
          "toBlock":stop,"page":page,"offset":PER_PAGE}
        if kind=="lp":params["topic1"]="0x"+format(tid,"064x")
        else:
            params["topic0"]=TOPIC_TRANSFER
            params["topic3"]="0x"+format(tid,"064x")
            params["topic0_3_opr"]="and"
        values,digest=fetch(params);digests.append(digest)
        for v in values:
            if v.get("address","").lower()!=MANAGER:continue
            if int(v.get("blockNumber","0x0"),16)>stop:raise ValueError("future event in range")
            topics=v.get("topics",[])
            if not topics or topics[0].lower() not in TOPIC:continue
            if kind=="lp":
                if len(topics)<2 or int(topics[1],16)!=tid:continue
                if topics[0].lower()==TOPIC_TRANSFER:continue
            else:
                if len(topics)<4 or int(topics[3],16)!=tid:continue
                if topics[0].lower()!=TOPIC_TRANSFER:continue
            ret.append({"name":TOPIC[topics[0].lower()],
                "block":int(v["blockNumber"],16),"txhash":v["transactionHash"].lower(),
                "log_index":int(v["logIndex"],16),"topics":topics,"data":v.get("data"),
                "block_hash":v.get("blockHash")})
        if len(values)<PER_PAGE:complete=True;break
        time.sleep(.6)
    ret.sort(key=lambda x:(x["block"],x["log_index"]))
    return {"events":ret,"complete_pagination":complete,
            "pages":len(digests),"response_sha256s":digests,
            "source":"routescan_indexed_not_fullnode"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    out={"study":"LP-NET-002-BOUNDED-LIFECYCLE","execution":"READ_ONLY",
         "capital_chf":0,"pnl_usd":None,"economic_verdict":"NO_LIVE_GO","targets":[]}
    for id,stop in TARGETS:
        row={"token_id":id,"last_known_withdrawal_block":stop}
        for kind in ("lp","transfer"):
            try:
                r=get_logs(id,stop,kind)
                row[kind+"_logs"]=r
                row[kind+"_status"]="INDEXED_LOGS_PRESENT" if r["events"] and r["complete_pagination"] else "INCOMPLETE_OR_EMPTY"
            except (OSError,ValueError,TypeError,KeyError,RuntimeError) as e:
                row[kind+"_status"]="SOURCE_BLOCKED"
                row[kind+"_error"]=type(e).__name__+":"+str(e)[:150]
            time.sleep(.6)
        out["targets"].append(row)
    out["full_onchain_position_lifecycle_verified"]=False
    out["status"]="INDEXED_RESEARCH_ONLY"
    out["next_gate"]="Reconcile all indexed log transactions to original receipts and pool identity, revalue all deposits, withdraws and fees, attribute all gas, validate OOS."
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"lp_counts":[len(r.get("lp_logs",{}).get("events",[])) for r in out["targets"]],
                      "transfer_counts":[len(r.get("transfer_logs",{}).get("events",[])) for r in out["targets"]],
                      "economic_verdict":out["economic_verdict"]}))
if __name__=="__main__":main()

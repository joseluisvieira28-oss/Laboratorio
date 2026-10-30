#!/usr/bin/env python3
"""ROLL-KEEPER-001: public Base onchain read ONLY, no orders/accounts/wallet."""
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.request
from collections import Counter

ROOT=pathlib.Path("artifacts/morpho_roll_keeper_source_v01")
RPC="https://mainnet.base.org"
CONTRACT="0x7bfA8207B818cc0e23a7aBdCBe56572fAbCa831F"
SETCONFIG="0x5a688e1dd9756a8fb6f9121f5bfb867eb485cf594652cab2a837f25c3e43d0d7"
ROLL="0x48b0106d0e5756564fec4b993afdd2145168802e7122df03495d5155fb5aa31e"
CHAIN_ID=8453
WINDOW=8192
PAGE=2048
BYTES_LIMIT=1_500_000
class Blocked(Exception):pass
def clock():return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def h(n):return hex(n)
def inthex(x):
    if not isinstance(x,str) or not x.startswith("0x"):raise Blocked("INVALID_HEX")
    try:return int(x,16)
    except ValueError:raise Blocked("INVALID_HEX_NUMBER")
def decode_roll(log):
    topic=log["topics"]
    if not isinstance(topic,list) or len(topic)!=4 or topic[0].lower()!=ROLL:raise Blocked("ROLL_TOPICS_BAD")
    raw=log.get("data")
    if not isinstance(raw,str) or not raw.startswith("0x") or len(raw)!=2+5*64:raise Blocked("ROLL_ABI_BAD")
    words=[int(raw[2+i*64:2+(i+1)*64],16) for i in range(5)]
    if words[0]>>160!=0:raise Blocked("CALLER_NOT_PADDED")
    return {"caller_address":"0x"+format(words[0],"064x")[-40:],
        "config_id":"0x"+format(words[1],"064x"),
        "debt_assets_raw":str(words[2]),
        "collateral_assets_raw":str(words[3]),
        "incentive_assets_raw":str(words[4]),
        "positive_incentive":words[4]>0}
def tests():
    synthetic={"topics":[ROLL,"0x"+"01"*32,"0x"+"02"*32,"0x"+"03"*32],
      "data":"0x"+"00"*12+"12"*20+"aa"*32+format(1000,"064x")+format(1050,"064x")+format(50,"064x")}
    t=decode_roll(synthetic)
    assert t["positive_incentive"] is True
    assert t["incentive_assets_raw"]=="50"
    assert t["debt_assets_raw"]=="1000"
    assert len(ROLL)==66 and len(SETCONFIG)==66
    try:decode_roll({**synthetic,"data":"0x1234"});raise AssertionError("BAD DATA ACCEPTED")
    except Blocked:pass
def rpc(method,params,number):
    payload=json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":number},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=payload,method="POST",headers={
        "Content-Type":"application/json","Accept":"application/json",
        "User-Agent":"CryptoLab-ROLL001-ResearchReadOnly/1.0"})
    t0=clock()
    try:
        with urllib.request.urlopen(req,timeout=16) as r:
            status=r.status
            raw=r.read(BYTES_LIMIT+1)
    except Exception as ex:raise Blocked("RPC_TRANSPORT_"+method+"_"+type(ex).__name__) from ex
    received=clock()
    if status!=200 or len(raw)>BYTES_LIMIT:raise Blocked("RPC_HTTP_OR_SIZE_"+method)
    filename=ROOT/(str(number).zfill(2)+"_"+method+".json")
    filename.write_bytes(raw)
    try:obj=json.loads(raw)
    except Exception as ex:raise Blocked("RPC_INVALID_JSON_"+method) from ex
    if not isinstance(obj,dict) or obj.get("id")!=number or obj.get("error") is not None or "result" not in obj:
        raise Blocked("RPC_RESULT_ERROR_"+method+"_"+str(obj.get("error"))[:160])
    return obj["result"],{"method":method,"utc_started":t0,"utc_received":received,
             "sha256":sha(raw),"bytes":len(raw),"raw_file":filename.name}
def main():
    tests()
    ROOT.mkdir(parents=True,exist_ok=True)
    receipt={"study":"ROLL_KEEPER_001_V01_BASE_PUBLIC_ONCHAIN",
      "created_at_utc":clock(),"status":"SOURCE_BLOCKED_FAIL_CLOSED",
      "chain_id_expected":CHAIN_ID,"contract_expected":CONTRACT,
      "onchain_events":[],"source_requests":[],"actual_orders":0,
      "wallet_access":0,"private_api_access":0,"main_mutations":0,
      "trading_pnl":None,"user_reward_earned":None}
    nextid=1
    try:
        cid,cmeta=rpc("eth_chainId",[],nextid);nextid+=1
        receipt["source_requests"].append(cmeta)
        if inthex(cid)!=CHAIN_ID:raise Blocked("CHAIN_ID_MISMATCH")
        head,meta=rpc("eth_blockNumber",[],nextid);nextid+=1
        receipt["source_requests"].append(meta)
        anchor=inthex(head)
        code,cmeta=rpc("eth_getCode",[CONTRACT,"latest"],nextid);nextid+=1
        receipt["source_requests"].append(cmeta)
        if not isinstance(code,str) or code=="0x" or not code.startswith("0x"):raise Blocked("OFFICIAL_CONTRACT_NOT_DEPLOYED")
        receipt["contract_code_sha256"]=sha(bytes.fromhex(code[2:]))
        receipt["contract_code_bytes"]=len(code[2:])//2
        start=max(0,anchor-WINDOW+1)
        receipt["block_anchor"]=anchor
        receipt["range_start"]=start
        receipt["range_end"]=anchor
        counts=Counter()
        logs=[]
        for low in range(start,anchor+1,PAGE):
            high=min(anchor,low+PAGE-1)
            params=[{"address":CONTRACT,"fromBlock":h(low),"toBlock":h(high),
                    "topics":[[SETCONFIG,ROLL]]}]
            data,meta=rpc("eth_getLogs",params,nextid);nextid+=1
            receipt["source_requests"].append(meta)
            if not isinstance(data,list):raise Blocked("LOGS_NOT_ARRAY")
            for row in data:
                if not isinstance(row,dict) or str(row.get("address","")).lower()!=CONTRACT.lower():
                    raise Blocked("LOG_ADDRESS_IDENTITY")
                block=inthex(row.get("blockNumber"))
                if not low<=block<=high:raise Blocked("LOG_OUTSIDE_FROZEN_RANGE")
                topics=row.get("topics")
                if not isinstance(topics,list) or not topics:raise Blocked("LOG_TOPICS_MISSING")
                sig=str(topics[0]).lower()
                if sig not in (ROLL,SETCONFIG):raise Blocked("LOG_UNEXPECTED_TOPIC")
                if sig==ROLL:
                    decoded=decode_roll(row)
                    counts["roll"]+=1
                    if decoded["positive_incentive"]:counts["roll_positive_incentive"]+=1
                else:
                    decoded={"event_type":"SET_CONFIG_ONLY_NOT_VERIFIED_ACTIVE"}
                    counts["set_config"]+=1
                logs.append({"block_number":block,"tx_hash":row.get("transactionHash"),
                    "log_index":inthex(row.get("logIndex")),
                    "topic0":sig,"decoded":decoded})
        logs.sort(key=lambda x:(x["block_number"],x["log_index"],str(x["tx_hash"])))
        receipt["onchain_events"]=logs
        receipt["event_counts"]=dict(counts)
        receipt["window_blocks"]=anchor-start+1
        receipt["receipt_check"]=[]
        for row in [e for e in logs if e["topic0"]==ROLL and e["decoded"]["positive_incentive"]][:3]:
            if len(receipt["receipt_check"])>=3:break
            txhash=row["tx_hash"]
            rec,meta=rpc("eth_getTransactionReceipt",[txhash],nextid);nextid+=1
            receipt["source_requests"].append(meta)
            if not isinstance(rec,dict) or rec.get("transactionHash","").lower()!=str(txhash).lower():
                raise Blocked("TX_RECEIPT_IDENTITY")
            status=inthex(rec.get("status"))
            if status!=1:raise Blocked("ROLL_TX_NOT_SUCCESS")
            gas=inthex(rec.get("gasUsed"))
            price=inthex(rec.get("effectiveGasPrice"))
            receipt["receipt_check"].append({"tx_hash":txhash,"gas_used":gas,
                  "effective_gas_price_wei":price,"L2_execution_gas_wei_only":str(gas*price),
                  "NOTE":"L1 fee plus token conversion, competition and all-in execution unknown"})
        if counts["roll_positive_incentive"]>0:
            receipt["status"]="ROLL_INCENTIVE_EVENT_OBSERVED_WITHOUT_NET_PROFIT"
        elif counts["roll"]>0:
            receipt["status"]="ROLL_EVENTS_NO_POSITIVE_INCENTIVE_IN_FROZEN_WINDOW"
        else:
            receipt["status"]="ZERO_ROLL_EVENTS_IN_FROZEN_WINDOW"
    except Blocked as ex:
        receipt["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        receipt["blocked_reason"]=str(ex)
    except Exception as ex:
        receipt["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        receipt["blocked_reason"]="UNEXPECTED_"+type(ex).__name__+":"+str(ex)[:150]
    finally:
        receipt["finished_at_utc"]=clock()
        receipt["net_profit_verdict"]="NO_NET_EDGE_CERTIFIED"
        receipt["can_act_on_open_configs"]=False
        receipt["is_transaction_executable"]=False
        receipt["financial_authorization"]="NONE"
        (ROOT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
        print(json.dumps({key:receipt.get(key) for key in ("study","status","blocked_reason",
            "window_blocks","block_anchor","event_counts","receipt_check","contract_code_bytes",
            "net_profit_verdict")},indent=2,sort_keys=True),flush=True)
    if receipt["status"]=="SOURCE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if __name__=="__main__":main()

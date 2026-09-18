#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
from typing import Any
import requests

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/research")
AUTH=json.loads((ROOT/"AAVE_CREDIT_STRESS_001_SOURCE_AUTHORITY_V0.2.json").read_text())
OUT=Path("artifacts/aave_credit_stress_source_v02_sqd");OUT.mkdir(parents=True,exist_ok=True)
PORTAL=AUTH["new_transport"]["endpoint"]
POOL=AUTH["frozen_contract"]["pool"]
TOPIC0=AUTH["frozen_contract"]["topic0"]
TOPIC1=AUTH["frozen_contract"]["topic1"]
MAX_TS=1735689599
TRANSIENT={429,500,502,503,504,529}

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def post(body:dict[str,Any],stats:dict[str,int])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":"AAVE-CREDIT-STRESS-001/source-v0.2"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}")
                ra=r.headers.get("Retry-After");r.close()
                if attempt<7:
                    stats["transient_retries"]+=1
                    try:delay=float(ra) if ra else min(20.0,1.5*(2**attempt))
                    except:delay=min(20.0,1.5*(2**attempt))
                    time.sleep(delay);continue
                raise last
            if r.status_code==204:
                r.close();raise RuntimeError("unexpected Portal 204 inside frozen range")
            r.raise_for_status();stats["successful_http_responses"]+=1;return r
        except (requests.RequestException,RuntimeError) as e:
            last=e
            if attempt<7:
                stats["network_retries"]+=1;time.sleep(min(20.0,1.5*(2**attempt)));continue
            raise
    raise RuntimeError(str(last))

def probe_window(w):
    start=int(w["from_block"]);end=int(w["to_block"])
    stats={"http_attempts":0,"successful_http_responses":0,"transient_retries":0,"network_retries":0,"portal_rows":0}
    body={
      "type":"evm","fromBlock":start,"toBlock":end,
      "fields":{
        "block":{"number":True,"timestamp":True},
        "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True,"data":True}
      },
      "logs":[{"address":[POOL],"topic0":[TOPIC0],"topic1":[TOPIC1]}]
    }
    r=post(body,stats);terminal=None;first_ts=None;last_ts=None;matching=[];rows=0;hh=hashlib.sha256()
    try:
        for raw in r.iter_lines(decode_unicode=True):
            if not raw:continue
            obj=json.loads(raw)
            if isinstance(obj,dict) and obj.get("error"):raise RuntimeError(f"portal error: {obj['error']}")
            header=obj.get("header") or obj.get("block") or {}
            bn=header.get("number")
            if bn is None:raise RuntimeError("Portal row missing continuation block number")
            bn=int(bn)
            if not(start<=bn<=end):raise RuntimeError("Portal row outside frozen window")
            if terminal is not None and bn<terminal:raise RuntimeError("Portal non-monotonic")
            terminal=bn;rows+=1
            ts=int(header["timestamp"])
            if ts>MAX_TS:raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
            first_ts=ts if first_ts is None else min(first_ts,ts);last_ts=ts if last_ts is None else max(last_ts,ts)
            for log in obj.get("logs") or []:
                addr=str(log.get("address","")).lower();topics=[str(x).lower() for x in (log.get("topics") or [])]
                txh=log.get("transactionHash");li=log.get("logIndex");data=log.get("data")
                if addr!=POOL:raise RuntimeError("wrong pool address")
                if len(topics)<2 or topics[0]!=TOPIC0 or topics[1]!=TOPIC1:raise RuntimeError("wrong topic identity")
                if not txh or li is None or not data:raise RuntimeError("missing structural log field")
                lii=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                matching.append({"blockNumber_present":True,"transactionHash_present":True,"logIndex_present":True,
                                 "topics_count":len(topics),"data_present":True})
                hh.update(f"{bn}|{str(txh).lower()}|{lii}|{addr}|{topics[0]}|{topics[1]}\n".encode())
    finally:r.close()
    stats["portal_rows"]=rows
    if rows==0 or terminal is None:raise RuntimeError("Portal empty inside frozen window")
    if terminal!=end:raise RuntimeError(f"terminal {terminal} != exact end {end}")
    return {
      "quarter":w["label"],"from_block":start,"to_block":end,"terminal_block":terminal,
      "first_timestamp":first_ts,"last_timestamp":last_ts,"matching_log_count":len(matching),
      "structural_records":matching[:3],"structural_sha256":hh.hexdigest(),"transport_stats":stats
    }

def head(url):
    try:
        r=requests.head(url,timeout=30,headers={"User-Agent":"AAVE-CREDIT-STRESS-001/source-v0.2"},allow_redirects=True)
        return {"url":url,"ok":200<=r.status_code<400,"status":r.status_code,"etag":r.headers.get("ETag"),"length":r.headers.get("Content-Length")}
    except Exception as e:return {"url":url,"ok":False,"error":type(e).__name__+":"+str(e)}

receipt={
 "lab":"AAVE-CREDIT-STRESS-001","source_gate_id":AUTH["source_gate_id"],"phase":"SOURCE_PROVENANCE_GATE_ONLY",
 "economic_values_decoded":False,"variable_borrow_rate_decoded":False,"stress_signal_computed":False,
 "btc_market_data_opened":False,"btc_returns_computed":False,"regression_computed":False,"pnl_computed":False,
 "2025_accessed":False,"2026_accessed":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False
}
try:
    probes=[probe_window(w) for w in AUTH["frozen_contract"]["windows"]]
    b=[head(u) for u in AUTH["frozen_contract"]["binance_source_presence"]]
    valid=0
    for p in probes:
        struct_ok=all(x["transactionHash_present"] and x["logIndex_present"] and x["data_present"] and x["topics_count"]>=2 for x in p["structural_records"])
        if p["terminal_block"]==p["to_block"] and p["matching_log_count"]>0 and struct_ok:valid+=1
    receipt.update({"transport":"SQD_ETHEREUM_MAINNET_PORTAL","quarter_probes":probes,"binance":b,"valid_quarter_probes":valid})
    if not all(x["ok"] for x in b):cls=AUTH["classifications"]["provenance_failure"]
    elif valid<4:cls=AUTH["classifications"]["insufficient"]
    else:cls=AUTH["classifications"]["pass"]
except Exception as e:
    cls=AUTH["classifications"]["technical_failure"];receipt["error"]=type(e).__name__+":"+str(e)

receipt["classification"]=cls
p=OUT/"AAVE_CREDIT_STRESS_001_SOURCE_V0.2.json";p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({
 "authority_sha256":sha((ROOT/"AAVE_CREDIT_STRESS_001_SOURCE_AUTHORITY_V0.2.json").read_bytes()),
 "result_sha256":sha(p.read_bytes())
},indent=2,sort_keys=True)+"\n")
print("AAVE_CS001_SOURCE_V02_JSON="+json.dumps(receipt,sort_keys=True))
print("AAVE_CS001_SOURCE_V02="+cls)
sys.exit(0 if cls not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2)

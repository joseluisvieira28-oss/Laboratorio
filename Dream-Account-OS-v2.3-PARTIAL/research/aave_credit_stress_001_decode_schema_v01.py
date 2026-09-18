#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Any
import requests

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/research")
AUTH=json.loads((ROOT/"AAVE_CREDIT_STRESS_001_DECODE_SCHEMA_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/aave_credit_stress_decode_schema_v01"); OUT.mkdir(parents=True,exist_ok=True)
PORTAL=AUTH["source"]["endpoint"]; POOL=AUTH["source"]["pool"]; TOPIC0=AUTH["source"]["topic0"]; TOPIC1=AUTH["source"]["topic1"]
TRANSIENT={429,500,502,503,504,529}; MAX_TS=1735689599

def post(body:dict[str,Any]):
    last=None
    for attempt in range(7):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,headers={
                "Content-Type":"application/json","Accept-Encoding":"gzip",
                "User-Agent":"AAVE-CREDIT-STRESS-001/decode-schema-v0.1"})
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}"); ra=r.headers.get("Retry-After"); r.close()
                if attempt<6:
                    try: delay=float(ra) if ra else min(20.0,1.5*(2**attempt))
                    except Exception: delay=min(20.0,1.5*(2**attempt))
                    time.sleep(delay); continue
                raise last
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if attempt<6: time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def decode_words(data:str):
    if not isinstance(data,str) or not data.startswith("0x"): raise RuntimeError("data_not_hex")
    raw=data[2:]
    if len(raw)!=AUTH["abi_decode"]["exact_data_bytes"]*2: raise RuntimeError(f"data_length:{len(raw)//2}")
    words=[int(raw[i:i+64],16) for i in range(0,len(raw),64)]
    if len(words)!=5: raise RuntimeError("word_count")
    names=AUTH["abi_decode"]["data_words"]
    return {name:words[i] for i,name in enumerate(names)}

def probe(w):
    start,end=int(w["from_block"]),int(w["to_block"])
    body={"type":"evm","fromBlock":start,"toBlock":end,
          "fields":{"block":{"number":True,"timestamp":True},
                    "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True,"data":True}},
          "logs":[{"address":[POOL],"topic0":[TOPIC0],"topic1":[TOPIC1]}]}
    r=post(body); terminal=None; rows=[]; identities=set()
    try:
        for raw in r.iter_lines(decode_unicode=True):
            if not raw: continue
            obj=json.loads(raw); header=obj.get("header") or obj.get("block") or {}
            bn=int(header["number"]); ts=int(header["timestamp"])
            if not(start<=bn<=end): raise RuntimeError("block_outside_window")
            if ts>MAX_TS: raise RuntimeError("protected_timestamp")
            terminal=bn
            for lg in obj.get("logs") or []:
                topics=[str(x).lower() for x in (lg.get("topics") or [])]
                if str(lg.get("address","")).lower()!=POOL or len(topics)<2 or topics[0]!=TOPIC0 or topics[1]!=TOPIC1:
                    raise RuntimeError("identity_mismatch")
                tx=str(lg["transactionHash"]).lower(); li=lg["logIndex"]; li=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                ident=(bn,tx,li)
                if ident in identities: raise RuntimeError("duplicate_identity")
                identities.add(ident)
                d=decode_words(lg["data"])
                rows.append({"block":bn,"timestamp":ts,"transactionHash":tx,"logIndex":li,**d})
    finally: r.close()
    if terminal!=end: raise RuntimeError(f"terminal:{terminal}!={end}")
    if not rows: raise RuntimeError("no_decoded_rows")
    vb=[x["variableBorrowRate"] for x in rows]
    return {"label":w["label"],"from_block":start,"to_block":end,"terminal_block":terminal,
            "decoded_log_count":len(rows),"first_timestamp":min(x["timestamp"] for x in rows),
            "last_timestamp":max(x["timestamp"] for x in rows),
            "variableBorrowRate_raw_min":min(vb),"variableBorrowRate_raw_max":max(vb),
            "sample":rows[:3],
            "identity_sha256":hashlib.sha256("\n".join(f'{x["block"]}|{x["transactionHash"]}|{x["logIndex"]}' for x in rows).encode()).hexdigest()}

receipt={"lab_id":AUTH["lab_id"],"gate_id":AUTH["gate_id"],"phase":"OUTCOME_BLIND_DECODE_SCHEMA",
         "btc_market_data_opened":False,"btc_returns_computed":False,"stress_predictor_constructed":False,
         "daily_series_constructed":False,"year_2025_accessed":False,"year_2026_accessed":False,
         "live_trading":False,"exchange_mutation":False}
try:
    windows=[probe(w) for w in AUTH["source"]["windows"]]
    receipt["windows"]=windows
    receipt["decoded_logs_total"]=sum(x["decoded_log_count"] for x in windows)
    receipt["classification"]="DECODE_SCHEMA_PASS" if len(windows)==4 and all(x["decoded_log_count"]>0 for x in windows) else "DECODE_SCHEMA_INSUFFICIENT"
except Exception as e:
    receipt["classification"]="DECODE_SCHEMA_TECHNICAL_FAILURE"; receipt["error"]=type(e).__name__+":"+str(e)

p=OUT/"AAVE_CREDIT_STRESS_001_DECODE_SCHEMA_RECEIPT_V0.1.json"
p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
raise SystemExit(0 if receipt["classification"]!="DECODE_SCHEMA_TECHNICAL_FAILURE" else 2)

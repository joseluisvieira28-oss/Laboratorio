#!/usr/bin/env python3
"""Immutable read-only SQD Base Aave V3 source census, NOT profit/position calculation."""
import datetime as dt
import hashlib
import json
import pathlib
import re
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

URL="https://portal.sqd.dev/datasets/base-mainnet/stream"
POOL="0xa238dd80c259a72e81d7e4664a9801593f98d1c5"
TOPIC="0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
FIRST=33000000
CHUNK=25000
PARTS=4
HEX64=re.compile(r"^0x[0-9a-fA-F]{64}$")
HEX40=re.compile(r"^0x[0-9a-fA-F]{40}$")

def query_payload(start):
    return {
      "type":"evm", "fromBlock":start,"toBlock":start+CHUNK-1,
      "logs":[{"address":[POOL], "topic0":[TOPIC]}],
      "fields":{"block":{"number":True,"timestamp":True},
                "log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}}
    }

def parse_bytes(raw, start):
    last=start+CHUNK-1
    lines=raw.splitlines()
    if not lines or len(raw)>8_000_000:
        raise ValueError("SOURCE_EMPTY_OR_OVERSIZED")
    seen_blocks=set()
    seen_events=set()
    liquidators=set()
    event_counts={}
    event_n=0
    for rawline in lines:
        if len(rawline)>512_000:
            raise ValueError("OVERSIZED_LINE")
        record=json.loads(rawline)
        header=record.get("header")
        if not isinstance(header,dict) or "number" not in header:
            raise ValueError("INVALID_BLOCK_HEADER")
        num=int(header["number"])
        if num<start or num>last:
            raise ValueError("BLOCK_OUT_OF_WINDOW")
        if num in seen_blocks:
            raise ValueError("DUPLICATE_BLOCK")
        seen_blocks.add(num)
        timestamp=header.get("timestamp")
        if timestamp is None:
            raise ValueError("MISSING_TIMESTAMP")
        if isinstance(timestamp,str) and ("T" in timestamp or "-" in timestamp):
            d=dt.datetime.fromisoformat(timestamp.replace("Z","+00:00"))
        else:
            stamp=int(timestamp)
            if stamp>100000000000: stamp/=1000
            d=dt.datetime.fromtimestamp(stamp,dt.timezone.utc)
        if d.year != 2025:
            raise ValueError("PROTECTED_2026_OR_OUT_OF_YEAR_SOURCE")
        for ev in record.get("logs",[]):
            if not isinstance(ev,dict) or ev.get("address","").lower()!=POOL:
                raise ValueError("WRONG_CONTRACT")
            tp=ev.get("topics",[])
            if len(tp)!=4 or any(not isinstance(t,str) or not HEX64.fullmatch(t) for t in tp) or tp[0].lower()!=TOPIC:
                raise ValueError("INVALID_EVENT_TOPICS")
            data=ev.get("data")
            if not isinstance(data,str) or not re.fullmatch(r"0x[0-9a-fA-F]{256}",data):
                raise ValueError("INVALID_EVENT_ABI_WORDS")
            h=ev.get("transactionHash","")
            if not HEX64.fullmatch(h):
                raise ValueError("MISSING_TX_HASH")
            idx=int(ev.get("logIndex",-1))
            if idx<0 or (num,idx) in seen_events:
                raise ValueError("DUPLICATE_OR_INVALID_LOG_ID")
            seen_events.add((num,idx))
            liquidator="0x"+data[2+64*2+24:2+64*3]  # ABI address low 20 bytes of 3rd uint256 slot
            if not HEX40.fullmatch(liquidator):
                raise ValueError("INVALID_LIQUIDATOR")
            liquidators.add(hashlib.sha256(liquidator.lower().encode()).hexdigest())
            event_counts[d.date().isoformat()]=event_counts.get(d.date().isoformat(),0)+1
            event_n+=1
    # documented SQD stream end-of-range boundary marker
    if last not in seen_blocks:
        raise ValueError("NO_END_RANGE_SENTINEL")
    return {"start_block":start,"end_block":last,"event_count":event_n,
            "block_rows":len(seen_blocks),"distinct_liquidator_hashes":sorted(liquidators),
            "event_count_by_utc_date":event_counts}

def source_get(payload):
    body=json.dumps(payload,separators=(",",":"),sort_keys=True).encode()
    req=Request(URL,method="POST",data=body,headers={"Content-Type":"application/json",
                 "Accept":"application/x-ndjson","User-Agent":"CryptoLab-Aave-ReadOnly/0.1"})
    with urlopen(req,timeout=25) as res:
        if res.status!=200: raise ValueError("SOURCE_NON_200")
        raw=res.read(8_000_001)
        if len(raw)>8_000_000: raise ValueError("SOURCE_TOO_LARGE")
        return raw

def run(output_path="source_receipt"):
    out=pathlib.Path(output_path)
    out.mkdir(parents=True,exist_ok=True)
    receipt={"lab":"AAVE_BASE_SQD_BONUS_V01","source_window":[FIRST,FIRST+PARTS*CHUNK-1],
      "source_status":"SOURCE_BLOCKED","has_economic_edge":False,
      "actual_pnl":None, "liquidation_bonus_usd":None, "execution_accessibility":None,
      "read_only":True,"orders":0,"chunks":[]}
    ok=True
    for i in range(PARTS):
        start=FIRST+i*CHUNK
        entry={"from_block":start,"to_block":start+CHUNK-1}
        try:
            body=source_get(query_payload(start))
            sha=hashlib.sha256(body).hexdigest()
            (out/f"chunk_{i}.ndjson").write_bytes(body)
            entry.update(parse_bytes(body,start))
            entry["source_sha256"]=sha
            entry["status"]="SOURCE_PASS"
        except (ValueError,KeyError,TypeError,OverflowError,HTTPError,URLError,TimeoutError, OSError) as exc:
            entry["status"]="SOURCE_BLOCKED"
            entry["reason"]=(type(exc).__name__+":"+str(exc))[:160]
            ok=False
        receipt["chunks"].append(entry)
        if not ok:break
    if ok:
        receipt["source_status"]="SOURCE_PASS_EVENTS_PRESENT" if sum(c["event_count"] for c in receipt["chunks"])>0 else "SOURCE_PASS_ZERO_EVENTS_THIS_FROZEN_WINDOW"
        receipt["total_liquidation_events"]=sum(c["event_count"] for c in receipt["chunks"])
        # Deduplicate hash-only pseudonyms between blocks; do not expose wallet identities
        receipt["unique_liquidator_hash_count"]=len(set(v for c in receipt["chunks"] for v in c.pop("distinct_liquidator_hashes")))
    else:
        for e in receipt["chunks"]:e.pop("distinct_liquidator_hashes",None)
    receipt["utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print("AAVE_BASE_SQD_SOURCE_RECEIPT="+json.dumps(receipt,sort_keys=True))
    return receipt

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="source_receipt")
    run(p.parse_args().out)

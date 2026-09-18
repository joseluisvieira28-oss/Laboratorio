#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,os,sys,time
from datetime import datetime,timezone,date,timedelta
from pathlib import Path
from typing import Any
import requests

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/research")
AUTH=json.loads((ROOT/"AAVE_CREDIT_STRESS_001_DECODE_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/aave_credit_stress_decode_v01");OUT.mkdir(parents=True,exist_ok=True)
PORTAL=AUTH["source"]["endpoint"]
POOL=AUTH["source"]["pool"]
TOPIC0=AUTH["source"]["topic0"]
TOPIC1=AUTH["source"]["usdc_topic1"]
GLOBAL_FROM=int(AUTH["source"]["from_block"]);GLOBAL_TO=int(AUTH["source"]["to_block"])
MAX_TS=int(datetime.fromisoformat(AUTH["source"]["maximum_timestamp_utc"].replace("Z","+00:00")).timestamp())
MAX_HTTP_BLOCK_WINDOW=75000
TRANSIENT={429,500,502,503,504,529}
EXPECTED_BYTES=int(AUTH["abi"]["expected_data_bytes"])
RATE_WORD=int(AUTH["abi"]["variable_borrow_rate_word_index_zero_based"])
SHARD_COUNT=8

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def post(body:dict[str,Any],stats:dict[str,int])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,
              headers={"Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":"AAVE-CREDIT-STRESS-001/decode-v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}");ra=r.headers.get("Retry-After");r.close()
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

def stream_range(start:int,end:int,stats:dict[str,int]):
    cursor=start
    while cursor<=end:
        request_to=min(end,cursor+MAX_HTTP_BLOCK_WINDOW-1)
        body={"type":"evm","fromBlock":cursor,"toBlock":request_to,
          "fields":{"block":{"number":True,"timestamp":True},
                    "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True,"data":True}},
          "logs":[{"address":[POOL],"topic0":[TOPIC0],"topic1":[TOPIC1]}]}
        r=post(body,stats);page_last=None;rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw:continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"):raise RuntimeError(f"portal error: {obj['error']}")
                header=obj.get("header") or obj.get("block") or {}
                bn=header.get("number")
                if bn is None:raise RuntimeError("Portal row missing continuation block number")
                bn=int(bn)
                if not(cursor<=bn<=request_to):raise RuntimeError("Portal row outside requested transport window")
                if page_last is not None and bn<page_last:raise RuntimeError("Portal page non-monotonic")
                page_last=bn;rows+=1;yield obj
        finally:r.close()
        if rows==0 or page_last is None:raise RuntimeError("Portal returned empty page inside frozen range")
        stats["portal_rows"]+=rows;cursor=page_last+1

def shard_bounds(idx:int)->tuple[int,int]:
    total=GLOBAL_TO-GLOBAL_FROM+1
    base=total//SHARD_COUNT;rem=total%SHARD_COUNT
    start=GLOBAL_FROM+idx*base+min(idx,rem)
    size=base+(1 if idx<rem else 0)
    return start,start+size-1

def decode_data(data:str)->list[int]:
    if not isinstance(data,str) or not data.startswith("0x"):raise RuntimeError("invalid log data")
    hx=data[2:]
    if len(hx)!=EXPECTED_BYTES*2:raise RuntimeError(f"wrong data bytes {len(hx)//2}")
    words=[int(hx[i:i+64],16) for i in range(0,len(hx),64)]
    if len(words)!=5:raise RuntimeError("expected exactly five ABI words")
    return words

def shard_mode(idx:int)->int:
    start,end=shard_bounds(idx)
    stats={"http_attempts":0,"successful_http_responses":0,"transient_retries":0,"network_retries":0,"portal_rows":0}
    events=[];seen=set();terminal=None;h=hashlib.sha256();failure=None
    try:
        for obj in stream_range(start,end,stats):
            header=obj.get("header") or obj.get("block") or {};bn=int(header["number"]);ts=int(header["timestamp"]);terminal=bn
            if ts>MAX_TS:raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
            for log in obj.get("logs") or []:
                addr=str(log.get("address","")).lower();topics=[str(x).lower() for x in (log.get("topics") or [])]
                txh=log.get("transactionHash");li=log.get("logIndex");data=log.get("data")
                if addr!=POOL or len(topics)<2 or topics[0]!=TOPIC0 or topics[1]!=TOPIC1:raise RuntimeError("wrong log identity")
                if not txh or li is None or not data:raise RuntimeError("missing structural field")
                lii=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                key=(str(txh).lower(),lii)
                if key in seen:raise RuntimeError("duplicate log identity inside shard")
                seen.add(key)
                words=decode_data(data)
                raw_rate=words[RATE_WORD]
                events.append({"block":bn,"timestamp":ts,"log_index":lii,"tx_hash":str(txh).lower(),"raw_variable_borrow_rate_ray":str(raw_rate)})
                h.update(f"{bn}|{str(txh).lower()}|{lii}|{raw_rate}\n".encode())
        if terminal!=end:raise RuntimeError(f"terminal {terminal} != shard end {end}")
    except Exception as e:failure=f"{type(e).__name__}:{str(e)[:500]}"
    cls="SHARD_PASS" if failure is None else "SHARD_TECHNICAL_FAILURE"
    receipt={"lab_id":AUTH["lab_id"],"decode_gate_id":AUTH["decode_gate_id"],"shard":idx,"from_block":start,"to_block":end,
      "terminal_block":terminal,"classification":cls,"event_count":len(events),"events":events,"transport_stats":stats,
      "structural_sha256":h.hexdigest(),"failure":failure,
      "firewall":{"btc_market_data_opened":False,"btc_returns_computed":False,"regression_computed":False,"bootstrap_computed":False,
                  "pnl_computed":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,
                  "wallet_access":False,"merge_to_main":False}}
    p=OUT/f"shard_{idx}.json";p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"shard":idx,"classification":cls,"from":start,"to":end,"events":len(events)},sort_keys=True))
    return 0 if cls=="SHARD_PASS" else 2

def aggregate_mode(inp:str)->int:
    files=sorted(Path(inp).rglob("shard_*.json"))
    if len(files)!=SHARD_COUNT:raise RuntimeError(f"expected {SHARD_COUNT} shards found {len(files)}")
    shards=[json.loads(f.read_text()) for f in files]
    shards.sort(key=lambda x:x["from_block"])
    expected=GLOBAL_FROM;events=[];seen=set()
    for s in shards:
        if s["classification"]!="SHARD_PASS":raise RuntimeError("non-pass shard")
        if s["from_block"]!=expected:raise RuntimeError("non-contiguous shard coverage")
        if s["terminal_block"]!=s["to_block"]:raise RuntimeError("shard terminal mismatch")
        expected=s["to_block"]+1
        for e in s["events"]:
            key=(e["tx_hash"],e["log_index"])
            if key in seen:raise RuntimeError("duplicate log identity across shards")
            seen.add(key);events.append(e)
    if expected-1!=GLOBAL_TO:raise RuntimeError("global terminal coverage mismatch")
    events.sort(key=lambda e:(e["timestamp"],e["block"],e["log_index"]))
    if len(events)<AUTH["gates"]["minimum_events"]:
        cls=AUTH["classifications"]["insufficient"]
    else:cls=None
    start_date=date.fromisoformat(AUTH["daily_series_rule"]["discovery_calendar_start"])
    end_date=date.fromisoformat(AUTH["daily_series_rule"]["discovery_calendar_end"])
    bydate={}
    for e in events:
        d=datetime.fromtimestamp(e["timestamp"],tz=timezone.utc).date()
        if d<start_date or d>end_date:continue
        prev=bydate.get(d)
        if prev is None or (e["timestamp"],e["block"],e["log_index"])>(prev["timestamp"],prev["block"],prev["log_index"]):
            bydate[d]=e
    first_event_date=min(bydate) if bydate else None
    daily=[];last=None;d=start_date
    while d<=end_date:
        if first_event_date is not None and d>=first_event_date:
            if d in bydate:last=bydate[d];new=True
            else:new=False
            if last is None:raise RuntimeError("carry-forward state missing after first observation")
            daily.append({"date":d.isoformat(),"raw_variable_borrow_rate_ray":last["raw_variable_borrow_rate_ray"],
              "had_new_event":new,"source_block":last["block"] if new else None,"source_timestamp":last["timestamp"] if new else None,
              "source_log_index":last["log_index"] if new else None})
        d+=timedelta(days=1)
    zero_missing=(first_event_date is not None and len(daily)==(end_date-first_event_date).days+1)
    checks={
      "exact_terminal_block_required":expected-1==GLOBAL_TO,
      "duplicate_log_identity_allowed":False,
      "every_matching_log_exact_five_words":True,
      "every_matching_log_topics_match":True,
      "minimum_events":len(events)>=AUTH["gates"]["minimum_events"],
      "minimum_daily_rows_after_first_observation":len(daily)>=AUTH["gates"]["minimum_daily_rows_after_first_observation"],
      "zero_missing_dates_after_first_observation":zero_missing
    }
    if cls is None:
        cls=AUTH["classifications"]["pass"] if all(v is True for k,v in checks.items() if k!="duplicate_log_identity_allowed") and checks["duplicate_log_identity_allowed"] is False else AUTH["classifications"]["insufficient"]
    result={"lab_id":AUTH["lab_id"],"decode_gate_id":AUTH["decode_gate_id"],"classification":cls,
      "event_count":len(events),"daily_rows":len(daily),"first_event_date":first_event_date.isoformat() if first_event_date else None,
      "last_event_date":max(bydate).isoformat() if bydate else None,"gate_checks":checks,"daily_series":daily,
      "structural_sha256":hashlib.sha256(json.dumps(events,sort_keys=True).encode()).hexdigest(),
      "firewall":{"btc_market_data_opened":False,"btc_returns_computed":False,"regression_computed":False,"bootstrap_computed":False,
                  "pnl_computed":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,
                  "wallet_access":False,"merge_to_main":False}}
    p=OUT/"aggregate.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (OUT/"manifest.json").write_text(json.dumps({"authority_sha256":sha((ROOT/"AAVE_CREDIT_STRESS_001_DECODE_AUTHORITY_V0.1.json").read_bytes()),"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="daily_series"},indent=2,sort_keys=True))
    return 0 if cls not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--shard",type=int);ap.add_argument("--aggregate-dir")
    a=ap.parse_args()
    if a.aggregate_dir:return aggregate_mode(a.aggregate_dir)
    if a.shard is None or not 0<=a.shard<SHARD_COUNT:raise SystemExit("valid --shard required")
    return shard_mode(a.shard)
if __name__=="__main__":sys.exit(main())

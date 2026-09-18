#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/research/stablecoin_dex_stress_v0_1")
AUTH=json.loads((ROOT/"SDS_CURVE3POOL_PEG_001_SOURCE_AUTHORITY_V02_SQD.json").read_text())
OUT=Path("artifacts/stablecoin_dex_stress_source_v02_sqd"); OUT.mkdir(parents=True,exist_ok=True)
PORTAL=AUTH["transport"]["endpoint"]
C=AUTH["frozen_scientific_contract"]
POOL=C["pool"]; TOPIC0=C["topic0"]
GLOBAL_FROM=int(C["start_block"]); GLOBAL_TO=int(C["end_block"])
START_TS=int(datetime.fromisoformat(C["source_calendar_start"]+"T00:00:00+00:00").timestamp())
END_TS=int(datetime.fromisoformat(C["source_calendar_end"]+"T23:59:59+00:00").timestamp())
PROTECTED_TS=int(datetime.fromisoformat(C["protected_timestamp_start"].replace("Z","+00:00")).timestamp())
SHARD_COUNT=16
MAX_HTTP_BLOCK_WINDOW=75000
TRANSIENT={429,500,502,503,504,529}
DECIMALS={0:18,1:6,2:6}

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def shard_bounds(idx:int)->tuple[int,int]:
    total=GLOBAL_TO-GLOBAL_FROM+1; base=total//SHARD_COUNT; rem=total%SHARD_COUNT
    start=GLOBAL_FROM+idx*base+min(idx,rem); size=base+(1 if idx<rem else 0)
    return start,start+size-1

def post(body:dict[str,Any],stats:dict[str,int])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,headers={
                "Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":"STABLECOIN-DEX-STRESS-001/source-v0.2-sqd"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}"); ra=r.headers.get("Retry-After"); r.close()
                if attempt<7:
                    stats["transient_retries"]+=1
                    try: delay=float(ra) if ra else min(20.0,1.5*(2**attempt))
                    except: delay=min(20.0,1.5*(2**attempt))
                    time.sleep(delay); continue
                raise last
            if r.status_code==204:
                r.close(); raise RuntimeError("unexpected Portal 204 inside frozen range")
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except (requests.RequestException,RuntimeError) as e:
            last=e
            if attempt<7:
                stats["network_retries"]+=1; time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def stream_range(start:int,end:int,stats:dict[str,int]):
    cursor=start
    while cursor<=end:
        request_to=min(end,cursor+MAX_HTTP_BLOCK_WINDOW-1)
        body={"type":"evm","fromBlock":cursor,"toBlock":request_to,
              "fields":{"block":{"number":True,"timestamp":True},
                        "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True,"data":True}},
              "logs":[{"address":[POOL],"topic0":[TOPIC0]}]}
        r=post(body,stats); page_last=None; rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(f"portal error: {obj['error']}")
                header=obj.get("header") or obj.get("block") or {}
                bn=header.get("number")
                if bn is None: raise RuntimeError("Portal row missing continuation block number")
                bn=int(bn)
                if not(cursor<=bn<=request_to): raise RuntimeError("Portal row outside requested transport window")
                if page_last is not None and bn<page_last: raise RuntimeError("Portal page non-monotonic")
                page_last=bn; rows+=1; yield obj
        finally:r.close()
        if rows==0 or page_last is None: raise RuntimeError("Portal returned empty page inside frozen range")
        stats["portal_rows"]+=rows; cursor=page_last+1

def decode_signed_256(hx:str)->int:
    x=int(hx,16)
    if x>=1<<255: x-=1<<256
    return x

def decode_event(data:str)->tuple[int,int,int,int]:
    if not isinstance(data,str) or not data.startswith("0x"): raise RuntimeError("invalid event data")
    hx=data[2:]
    if len(hx)!=256: raise RuntimeError(f"wrong TokenExchange data bytes {len(hx)//2}")
    w=[hx[i:i+64] for i in range(0,256,64)]
    sold_id=decode_signed_256(w[0]); tokens_sold=int(w[1],16)
    bought_id=decode_signed_256(w[2]); tokens_bought=int(w[3],16)
    return sold_id,tokens_sold,bought_id,tokens_bought

def shard_mode(idx:int)->int:
    start,end=shard_bounds(idx)
    stats={"http_attempts":0,"successful_http_responses":0,"transient_retries":0,"network_retries":0,"portal_rows":0}
    daily=defaultdict(lambda:{"numerator":0.0,"denominator":0.0,"swap_count":0})
    seen=set(); terminal=None; event_count=0; in_window_events=0; h=hashlib.sha256(); failure=None
    first_ts=None; last_ts=None
    try:
        for obj in stream_range(start,end,stats):
            header=obj.get("header") or obj.get("block") or {}; bn=int(header["number"]); ts=int(header["timestamp"]); terminal=bn
            if ts>=PROTECTED_TS: raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
            for log in obj.get("logs") or []:
                addr=str(log.get("address","")).lower(); topics=[str(x).lower() for x in (log.get("topics") or [])]
                txh=str(log.get("transactionHash","")).lower(); li=log.get("logIndex"); data=log.get("data")
                if addr!=POOL or not topics or topics[0]!=TOPIC0: raise RuntimeError("wrong log identity")
                if not txh or li is None or not data: raise RuntimeError("missing structural field")
                lii=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                key=(txh,lii)
                if key in seen: raise RuntimeError("duplicate log identity inside shard")
                seen.add(key)
                sold_id,tokens_sold,bought_id,tokens_bought=decode_event(data)
                if sold_id not in DECIMALS or bought_id not in DECIMALS or sold_id==bought_id: raise RuntimeError("invalid coin ids")
                if tokens_sold<=0 or tokens_bought<=0: raise RuntimeError("non-positive token quantity")
                event_count+=1; first_ts=ts if first_ts is None else min(first_ts,ts); last_ts=ts if last_ts is None else max(last_ts,ts)
                h.update(f"{bn}|{txh}|{lii}|{sold_id}|{tokens_sold}|{bought_id}|{tokens_bought}\n".encode())
                if START_TS<=ts<=END_TS:
                    sold=tokens_sold/(10.0**DECIMALS[sold_id]); bought=tokens_bought/(10.0**DECIMALS[bought_id])
                    if sold<=0 or bought<=0 or not(math.isfinite(sold) and math.isfinite(bought)): raise RuntimeError("invalid normalized quantity")
                    nominal=(sold+bought)/2.0; dev=abs(math.log(bought/sold))
                    if not(math.isfinite(nominal) and math.isfinite(dev)): raise RuntimeError("nonfinite source formula")
                    d=datetime.fromtimestamp(ts,tz=timezone.utc).date().isoformat()
                    daily[d]["numerator"]+=nominal*dev; daily[d]["denominator"]+=nominal; daily[d]["swap_count"]+=1
                    in_window_events+=1
        if terminal!=end: raise RuntimeError(f"terminal {terminal} != shard end {end}")
    except Exception as e: failure=f"{type(e).__name__}:{str(e)[:500]}"
    cls="SHARD_PASS" if failure is None else "SHARD_TECHNICAL_FAILURE"
    receipt={"lab":AUTH["lab"],"mve_id":AUTH["mve_id"],"source_gate_id":AUTH["source_gate_id"],"shard":idx,
             "from_block":start,"to_block":end,"terminal_block":terminal,"classification":cls,
             "event_count":event_count,"in_window_event_count":in_window_events,"daily_partial":dict(sorted(daily.items())),
             "first_event_timestamp":first_ts,"last_event_timestamp":last_ts,"structural_sha256":h.hexdigest(),
             "transport_stats":stats,"failure":failure,
             "firewall":{"eth_market_data_opened":False,"signal_threshold_computed":False,"returns_computed":False,"pnl_computed":False,
                         "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"wallet_access":False,"merge_to_main":False}}
    p=OUT/f"shard_{idx}.json"; p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"shard":idx,"classification":cls,"from":start,"to":end,"events":event_count,"days":len(daily)},sort_keys=True))
    return 0 if cls=="SHARD_PASS" else 2

def aggregate_mode(inp:str)->int:
    files=sorted(Path(inp).rglob("shard_*.json"))
    if len(files)!=SHARD_COUNT: raise RuntimeError(f"expected {SHARD_COUNT} shards found {len(files)}")
    shards=[json.loads(f.read_text()) for f in files]; shards.sort(key=lambda x:x["from_block"])
    expected=GLOBAL_FROM; totals=defaultdict(lambda:{"numerator":0.0,"denominator":0.0,"swap_count":0})
    event_count=0; in_window_events=0; hashes=[]
    for s in shards:
        if s["classification"]!="SHARD_PASS": raise RuntimeError("non-pass shard")
        if s["from_block"]!=expected or s["terminal_block"]!=s["to_block"]: raise RuntimeError("shard coverage mismatch")
        expected=s["to_block"]+1; event_count+=s["event_count"]; in_window_events+=s["in_window_event_count"]; hashes.append(s["structural_sha256"])
        for d,v in s["daily_partial"].items():
            totals[d]["numerator"]+=float(v["numerator"]); totals[d]["denominator"]+=float(v["denominator"]); totals[d]["swap_count"]+=int(v["swap_count"])
    if expected-1!=GLOBAL_TO: raise RuntimeError("global terminal coverage mismatch")
    daily=[]
    for d in sorted(totals):
        v=totals[d]
        if v["denominator"]<=0 or v["swap_count"]<=0: raise RuntimeError(f"invalid daily denominator {d}")
        stress=v["numerator"]/v["denominator"]
        if not math.isfinite(stress): raise RuntimeError(f"nonfinite daily stress {d}")
        daily.append({"date":d,"daily_stress":stress,"swap_count":v["swap_count"],"weighted_numerator":v["numerator"],"weighted_denominator":v["denominator"]})
    years=sorted({int(x["date"][:4]) for x in daily})
    g=AUTH["source_gates"]
    checks={"exact_terminal_block_coverage":expected-1==GLOBAL_TO,
            "duplicate_log_identity_allowed":False,
            "every_event_exact_4_nonindexed_words":True,
            "valid_coin_ids_only":True,
            "positive_quantities_only":True,
            "minimum_daily_source_observations":len(daily)>=g["minimum_daily_source_observations"],
            "required_calendar_years":years==g["required_calendar_years"]}
    cls=AUTH["classifications"]["pass"] if all(v is True for k,v in checks.items() if k!="duplicate_log_identity_allowed") and checks["duplicate_log_identity_allowed"] is False else AUTH["classifications"]["insufficient"]
    result={"lab":AUTH["lab"],"mve_id":AUTH["mve_id"],"source_gate_id":AUTH["source_gate_id"],"classification":cls,
            "event_count":event_count,"in_window_event_count":in_window_events,"daily_source_observations":len(daily),
            "first_daily_date":daily[0]["date"] if daily else None,"last_daily_date":daily[-1]["date"] if daily else None,
            "calendar_years":years,"gate_checks":checks,"daily_source_series":daily,
            "structural_sha256":hashlib.sha256("|".join(hashes).encode()).hexdigest(),
            "firewall":{"eth_market_data_opened":False,"signal_threshold_computed":False,"discovery_trade_count_computed":False,
                        "returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,
                        "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"wallet_access":False,"merge_to_main":False}}
    p=OUT/"aggregate.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (OUT/"manifest.json").write_text(json.dumps({"authority_sha256":sha((ROOT/"SDS_CURVE3POOL_PEG_001_SOURCE_AUTHORITY_V02_SQD.json").read_bytes()),"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="daily_source_series"},indent=2,sort_keys=True))
    return 0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--shard",type=int); ap.add_argument("--aggregate-dir"); a=ap.parse_args()
    if a.aggregate_dir: return aggregate_mode(a.aggregate_dir)
    if a.shard is None or not 0<=a.shard<SHARD_COUNT: raise SystemExit("valid --shard required")
    return shard_mode(a.shard)

if __name__=="__main__": sys.exit(main())

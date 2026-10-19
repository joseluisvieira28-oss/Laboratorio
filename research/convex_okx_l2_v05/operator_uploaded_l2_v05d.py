"""Private local OKX historical 400-level .data book replay — research ONLY.

Accepts EXACT original SOL / BNB files downloaded by the user. Never opens a
network connection or exports the original market stream. No exchange orders.
Sequence IDs are ABSENT in OKX portal's 2023 .data archive: continuity remains
UNPROVEN, even when the book reconstructs cleanly.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import tarfile
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path

try:
    import orjson as fastjson
    loads=fastjson.loads
except ImportError:
    loads=json.loads

CASES={
 "SOL":{
   "inst":"SOL-USDT-SWAP","day":"2023-05-29","t0":1685376300000,
   "original_binance_base_qty":"104.79202011433037",
   "launch_face_base_per_contract":"1",
 },
 "BNB":{
   "inst":"BNB-USDT-SWAP","day":"2023-11-01","t0":1698854700000,
   "original_binance_base_qty":"8.822493532731512",
   "launch_face_base_per_contract":"0.01",
 },
}
TIERS=("0.25","0.5","0.75","1")
MAX_UNCOMPRESSED=750_000_000
MAX_FILE=190_000_000
MAX_EVENTS=5_000_000

def day_start_ms(day):
    return int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)

def sha256_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def synth_sweep(asks,qtybase,contract_face,ratio):
    """This does NOT round to a historically verified contract lot size."""
    target=(qtybase*ratio)/contract_face
    remaining=target
    pairs=sorted(asks.items())
    if not pairs:raise ValueError("NO_ASKS")
    best=Decimal(str(pairs[0][0]))
    money=Decimal(0)
    touched=0
    for px,avail in pairs:
        if remaining<=0:break
        taken=min(remaining,Decimal(str(avail)))
        if taken>0:
            money+=taken*Decimal(str(px))
            remaining-=taken
            touched+=1
    used=target-remaining
    vwap=money/used if used>0 else None
    return {
      "original_quantity_scale":str(ratio),
      "assumed_base_quantity":str(qtybase*ratio),
      "assumed_contracts_unrounded":str(target),
      "top_ask_contract_quantity":str(pairs[0][1]),
      "top_ask_base_equivalent_at_launch_face":str(Decimal(str(pairs[0][1]))*contract_face),
      "top_ask_sufficient":Decimal(str(pairs[0][1]))>=target,
      "full_visible_400level_ask_depth_sufficient":remaining==0,
      "levels_consumed":touched,
      "hypothetical_ask_vwap":str(vwap) if vwap else None,
      "hypothetical_ask_walk_bps":str((vwap/best-1)*10000) if vwap else None,
      "unfilled_contracts":str(remaining),
      "actual_fill_proven":False
    }

def replay(path,case):
    if case not in CASES:raise ValueError("UNREGISTERED_CASE")
    spec=CASES[case]
    p=Path(path)
    if not p.is_file() or p.is_symlink():raise ValueError("MISSING_OR_SYMLINK_ARCHIVE")
    expected=f"{spec['inst']}-L2orderbook-400lv-{spec['day']}.tar.gz"
    if p.name!=expected:raise ValueError("NOT_EXACT_PORTAL_FILENAME")
    if p.stat().st_size>MAX_FILE:raise ValueError("COMPRESSED_CAP_EXCEEDED")
    sha=sha256_file(p)
    start=day_start_ms(spec["day"])
    bids={};asks={}
    counters=Counter()
    first=last=prev=last_snapshot=None
    next_future=None;peak=0;max_gap=0;has_sequences=False
    with tarfile.open(p,"r:gz") as archive:
        members=archive.getmembers()
        if len(members)!=1 or not members[0].isfile():
            raise ValueError("NOT_EXACT_ONE_REGULAR_TAR_MEMBER")
        member=members[0]
        if member.name!=expected.removesuffix(".tar.gz")+".data":
            raise ValueError("PORTAL_DATA_MEMBER_NAME_MISMATCH")
        if member.size>MAX_UNCOMPRESSED:raise ValueError("UNCOMPRESSED_CAP_EXCEEDED")
        f=archive.extractfile(member)
        if f is None:raise ValueError("TAR_MEMBER_UNREADABLE")
        for line in f:
            counters["records_read_including_first_future"]+=1
            if counters["records_read_including_first_future"]>MAX_EVENTS:
                raise ValueError("FROZEN_RECORD_CAP_EXCEEDED")
            if len(line)>2_000_000:raise ValueError("LINE_TOO_LARGE")
            doc=loads(line)
            if not isinstance(doc,dict):raise ValueError("NOT_A_JSON_OBJECT")
            if doc.get("instId")!=spec["inst"]:raise ValueError("WRONG_INSTRUMENT_IN_PAYLOAD")
            rawts=doc.get("ts")
            if not isinstance(rawts,(str,int)) or isinstance(rawts,bool):raise ValueError("BAD_TIMESTAMP_TYPE")
            ts=int(rawts)
            if first is None:first=ts
            if ts>spec["t0"]:
                next_future=ts
                break
            if not start<=ts<start+86400000:
                raise ValueError("EVENT_OUT_OF_FROZEN_UTC_DAY")
            if prev is not None and ts<prev:raise ValueError("NONCHRONOLOGICAL_EVENT")
            if prev is not None:max_gap=max(max_gap,ts-prev)
            prev=ts;last=ts
            if "seqId" in doc or "prevSeqId" in doc:has_sequences=True
            action=doc.get("action")
            if action not in ("snapshot","update"):raise ValueError("UNKNOWN_ACTION")
            if action=="snapshot":
                bids.clear();asks.clear();last_snapshot=ts
            elif not counters["snapshot"]:
                raise ValueError("DELTA_BEFORE_FIRST_SNAPSHOT")
            counters[action]+=1
            for name,book in (("asks",asks),("bids",bids)):
                raw=doc.get(name)
                if not isinstance(raw,list):raise ValueError("MISSING_SIDE")
                for level in raw:
                    if not isinstance(level,list) or len(level)!=3:
                        raise ValueError("UNEXPECTED_PORTAL_PRICE_QTY_COUNT_SHAPE")
                    pr,qt=level[:2]
                    price=float(pr);qty=float(qt)
                    if not 0<price<float("inf") or not 0<=qty<float("inf"):
                        raise ValueError("BAD_PRICE_OR_SIZE")
                    if qty==0:book.pop(price,None)
                    else:book[price]=qty
                if len(book)>400:raise ValueError("MORE_THAN_400_LEVELS_NO_SOURCE_SPEC")
            peak=max(peak,len(asks),len(bids))
    if not asks or not bids or last is None:
        raise ValueError("NO_VALID_COMPLETE_BOOK_BEFORE_T0")
    topask=min(asks);topbid=max(bids)
    if topbid>=topask:raise ValueError("CROSSED_BOOK_AT_T0")
    age=spec["t0"]-last
    if age<0 or age>2000:raise ValueError("STALE_OR_FUTURE_SOURCE_QUOTE")
    if len(asks)!=400 or len(bids)!=400:raise ValueError("INCOMPLETE_400_LEVEL_SNAPSHOT_AT_T0")
    base=Decimal(spec["original_binance_base_qty"])
    face=Decimal(spec["launch_face_base_per_contract"])
    scenarios=[synth_sweep(asks,base,face,Decimal(r)) for r in TIERS]
    return {
      "instrument":spec["inst"],"signal_utc":datetime.fromtimestamp(spec["t0"]/1000,timezone.utc).isoformat(),
      "source":"USER_UPLOADED_OKX_PORTAL_PRIVATE_ARCHIVE",
      "compressed_bytes":p.stat().st_size,
      "archive_sha256_local_custody_not_publisher_signed":sha,
      "uncompressed_member_bytes":member.size,
      "record_counts_until_T0":dict(counters),
      "first_event_ms":first,"last_event_at_or_before_T0_ms":last,
      "first_event_after_T0_was_NOT_APPLIED":next_future,
      "last_snapshot_before_T0_ms":last_snapshot,
      "latest_quote_age_ms":age,
      "max_update_timestamp_gap_ms":max_gap,
      "asks_levels":len(asks),"bids_levels":len(bids),
      "best_bid":str(topbid),"best_ask":str(topask),
      "spread_bps":str((Decimal(str(topask))/Decimal(str(topbid))-1)*10000),
      "source_seq_ids_present":has_sequences,
      "continuity_proof":"UNVERIFIED_NO_EXPORTED_SEQ_IDS",
      "historical_contract_value":"LAUNCH_ANNOUNCEMENT_ONLY_NOT_POINT_IN_TIME_REVALIDATED",
      "launch_face_value_base_per_contract":str(face),
      "contract_lotSz_at_T0_verified":False,
      "sample_count":1,
      "static_hypothetical_long_ask_entry_sweeps":scenarios,
      "real_broker_fills_verified":False,"stop_bid_exit_economics_verified":False,
      "net_profit_or_OOS_certified":False,"live_go":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sol",type=Path)
    ap.add_argument("--bnb",type=Path)
    ap.add_argument("--out",type=Path,default=Path("local-private-okx-v05d"))
    a=ap.parse_args()
    reports={}
    for key,path in (("SOL",a.sol),("BNB",a.bnb)):
        if path is None:
            reports[key]={"status":"NOT_PROVIDED"}
        else:
            try:reports[key]={"status":"HISTORICAL_L2_ENTRY_PROVISIONAL",**replay(path,key)}
            except Exception as exc:
                reports[key]={"status":"FAIL_CLOSED","reason":type(exc).__name__+":"+str(exc)[:120]}
    summary={"status":"PRIVATE_UPLOADED_TWO_SOURCE_OBSERVATIONS_NOT_ALPHA",
       "cases":reports,"source_raw_uploaded_to_GitHub":False,
       "trade_authority":"NONE","2026_holdout_opened":False}
    a.out.mkdir(parents=True,exist_ok=True)
    target=a.out/"V05D_LOCAL_TWO_UPLOADED_ORDERBOOK_CAUSAL_RECEIPT.json"
    target.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf8")
    for key,v in reports.items():
        print("V05D_CASE",json.dumps({
            "asset":key,"status":v["status"],"age_ms":v.get("latest_quote_age_ms"),
            "best_bid":v.get("best_bid"),"best_ask":v.get("best_ask"),
            "scenarios":v.get("static_hypothetical_long_ask_entry_sweeps")
        },sort_keys=True))
    print("LOCAL_SOURCE_RECEIPT",target)

if __name__=="__main__":main()

"""Read operator-owned 2025 official OKX BTC-USDT/ BTC-USD L2 privately, source only.

DO NOT upload source archives to GitHub or any cloud service. Run on a machine
where the two historical files already exist. No network calls or exchange
trading. Fails closed rather than pretending to have verified contract lots.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, math, tarfile
from datetime import datetime, timezone
from pathlib import Path

try:
    import orjson
    loads=orjson.loads
except ImportError:
    loads=json.loads

DAY="2025-06-02"
PROBES=("00:05:00","12:05:00","23:55:00")
INSTS={"LINEAR":"BTC-USDT-SWAP","INVERSE":"BTC-USD-SWAP"}
TIME_FORMAT="%Y-%m-%dT%H:%M:%S%z"
MAX_INPUT=1_500_000_000
MAX_DECOMPRESSED=30_000_000_000
MAX_LINE=2_000_000
MAX_RECORDS=75_000_000

def stamp(hhmmss):
    return int(datetime.strptime(f"{DAY}T{hhmmss}+0000", TIME_FORMAT).timestamp()*1000)

def filehash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for blob in iter(lambda:f.read(4*1024*1024),b""):h.update(blob)
    return h.hexdigest()

def book_sample(t,last_ts,bids,asks,*,source_name):
    if last_ts is None:
        return {"probe_utc":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),"status":"NO_FIRST_SNAPSHOT"}
    age=t-last_ts
    if age<0 or age>2000:
        return {"probe_utc":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),
                "status":"STALE_OR_FUTURE_QUOTE","age_ms":age}
    if len(bids)!=400 or len(asks)!=400:
        return {"probe_utc":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),
                "status":"NOT_FULL_400X400","bids":len(bids),"asks":len(asks)}
    bb=max(bids);ba=min(asks)
    if bb>=ba:raise ValueError("CROSSED_AT_PROBE")
    mid=(bb+ba)/2
    return {"probe_utc":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),
      "status":"SOURCE_ONLY_FRESH_COMPLETE",
      "last_book_event_ms":last_ts,"source_quote_age_ms":age,
      "best_bid_raw_price":bb,"best_ask_raw_price":ba,
      "best_bid_raw_contracts":bids[bb],"best_ask_raw_contracts":asks[ba],
      "book_bids_levels":len(bids),"book_asks_levels":len(asks),
      "sum_visible_bid_raw_contracts":sum(bids.values()),
      "sum_visible_ask_raw_contracts":sum(asks.values()),
      "top_spread_bps":(ba/bb-1)*10000,"mid_reference_raw_quote":mid,
      "spread_over_mid_bps":(ba-bb)/mid*10000,
      "instantaneous_roundtrip_spread_over_mid_bps":(ba-bb)/mid*10000,
      "outermost_bid_raw_price":min(bids),"outermost_ask_raw_price":max(asks),
      "venue_same_OKX_but_usd_vs_usdt_denomination":True,
      "point_in_time_contract_face_value_verified":False,
      "broker_executable_fill_verified":False}

def replay(path:Path,inst:str):
    original=f"{inst}-L2orderbook-400lv-{DAY}"
    if not path.is_file() or path.is_symlink() or path.name!=original+".tar.gz":
        raise ValueError("ORIGINAL_ARCHIVE_PATH_OR_NAME_NOT_EXACT")
    if path.stat().st_size>MAX_INPUT:raise ValueError("COMPRESSED_SIZE_CAP_EXCEEDED")
    timestamps=[stamp(t) for t in PROBES]
    start=int(datetime(2025,6,2,tzinfo=timezone.utc).timestamp()*1000)
    books={"bids":{},"asks":{}}
    last_ts=previous_ts=None
    samples=[]
    num_records=0;num_updates=0;num_snapshots=0;max_gap=0;first_ts=None
    seen_seq=False;data_hash=hashlib.sha256();data_bytes=0;equal_ts=0
    zero_deletions=0;crossed_events=0;schema_keys=set()
    with gzip.open(path,"rb") as gz, tarfile.open(fileobj=gz,mode="r|") as arc:
        member=arc.next()
        if member is None or not member.isfile() or member.name!=original+".data":
            raise ValueError("TAR_DATA_MEMBER_UNEXPECTED")
        if member.size>MAX_DECOMPRESSED:raise ValueError("DECOMPRESSED_SIZE_CAP")
        f=arc.extractfile(member)
        if f is None:raise ValueError("DATA_MEMBER_UNREADABLE")
        while True:
            line=f.readline(MAX_LINE+1)
            if not line:break
            data_hash.update(line);data_bytes+=len(line)
            num_records+=1
            if num_records>MAX_RECORDS or len(line)>MAX_LINE:
                raise ValueError("MAX_RECORDS_OR_LINE_CAP")
            event=loads(line)
            if not isinstance(event,dict) or event.get("instId")!=inst:
                raise ValueError("WRONG_INSTRUMENT_OR_INVALID_JSON")
            schema_keys.update(event)
            tsraw=event.get("ts")
            if not isinstance(tsraw,(str,int)) or isinstance(tsraw,bool):
                raise ValueError("INVALID_TIMESTAMP_SCHEMA")
            ts=int(tsraw)
            if not start<=ts<start+86400000 or (previous_ts is not None and ts<previous_ts):
                raise ValueError("DAY_OR_EVENT_CHRONOLOGY_INVALID")
            while len(samples)<len(timestamps) and ts>timestamps[len(samples)]:
                samples.append(book_sample(timestamps[len(samples)],last_ts,
                    books["bids"],books["asks"],source_name=inst))
            if first_ts is None:first_ts=ts
            if previous_ts is not None:max_gap=max(max_gap,ts-previous_ts)
            if ts==previous_ts:equal_ts+=1
            previous_ts=ts
            action=event.get("action")
            if action=="snapshot":
                books["bids"].clear();books["asks"].clear()
                num_snapshots+=1
            elif action=="update" and num_snapshots>0:
                num_updates+=1
            else:raise ValueError("NO_INITIAL_SNAPSHOT_OR_BAD_ACTION")
            if "seqId" in event or "prevSeqId" in event:seen_seq=True
            for name,book in books.items():
                lines=event.get(name)
                if not isinstance(lines,list):raise ValueError("MISSING_BOOK_SIDE")
                for lvl in lines:
                    if not isinstance(lvl,list) or len(lvl)!=3:
                        raise ValueError("INVALID_PRICE_CONTRACT_COUNT_LEVEL")
                    p=float(lvl[0]);q=float(lvl[1])
                    n=float(lvl[2])
                    if not math.isfinite(p) or p<=0 or not math.isfinite(q) or q<0:
                        raise ValueError("INVALID_PRICE_OR_QTY")
                    if not math.isfinite(n) or n<0 or not n.is_integer():
                        raise ValueError("INVALID_ORDER_COUNT")
                    if q==0:
                        book.pop(p,None);zero_deletions+=1
                    else:book[p]=q
                if len(book)>400:raise ValueError("OVER_400_DEPTH")
            if books["bids"] and books["asks"] and max(books["bids"])>=min(books["asks"]):
                crossed_events+=1
                raise ValueError("CROSSED_SOURCE_EVENT")
            last_ts=ts
        if data_bytes!=member.size:raise ValueError("TAR_MEMBER_SIZE_MISMATCH")
        if arc.next() is not None:raise ValueError("EXTRA_TAR_MEMBER")
        # tar stream alone can stop before the gzip trailer. Drain to EOF so
        # GzipFile validates CRC32/ISIZE, including truncation after the probes.
        while gz.read(4*1024*1024):pass
        while len(samples)<len(timestamps):
            samples.append(book_sample(timestamps[len(samples)],last_ts,
                books["bids"],books["asks"],source_name=inst))
        # Archived event-stream continuity is not proven by monotone timestamps.
    return {"instrument":inst,"status":"ALL_THREE_CAUSAL_400LEVEL_QUOTES_RECONSTRUCTED_SOURCE_ONLY" if
            all(x["status"]=="SOURCE_ONLY_FRESH_COMPLETE" for x in samples)
            else "SOURCE_QUOTE_COVERAGE_FAIL_CLOSED",
            "raw_archive_local_sha256_not_vendor_signed":filehash(path),
            "raw_archive_bytes":path.stat().st_size,
            "source_first_event_ms":first_ts,"source_last_event_ms":last_ts,
            "processed_events_full_day":num_records,
            "data_member_bytes":data_bytes,"data_member_sha256":data_hash.hexdigest(),
            "gzip_crc32_isize_verified_to_eof":True,"tar_exactly_one_expected_member":True,
            "event_schema_keys":sorted(schema_keys),"same_timestamp_adjacent_events":equal_ts,
            "zero_quantity_deletions":zero_deletions,"crossed_source_events":crossed_events,
            "updates_applied":num_updates,"snapshots_applied":num_snapshots,
            "max_adjacent_source_timestamp_gap_ms":max_gap,
            "sequence_fields_any_seen":seen_seq,
            "lossless_source_continuity_proven":False,
            "sample_quotes":samples}

def run(files):
    result={"study":"FUNDING_HUNTER_V03_2025_06_02_TWO_USER_UPLOADED_OKX_L2",
            "asof_utc":"2026-10-19","probe_clocks_utc":PROBES,"historical_quote_outcomes_opened":True,
            "funding_outcomes_opened":False,
            "futures_trade_opened":False,"historical_contract_lot_verified":False,
            "funding_cashflows_verified":False,"live_go":False,"venue_spread_not_arbitrage":True,
            "source_only_cases":{}}
    for key,inst in INSTS.items():
        try:result["source_only_cases"][key]=replay(files[key],inst)
        except Exception as e:result["source_only_cases"][key]={"status":"SOURCE_BLOCKED","error":type(e).__name__+":"+str(e)[:120]}
    left=result["source_only_cases"].get("LINEAR",{})
    right=result["source_only_cases"].get("INVERSE",{})
    if all(x.get("status")=="ALL_THREE_CAUSAL_400LEVEL_QUOTES_RECONSTRUCTED_SOURCE_ONLY" for x in (left,right)):
        refs=[]
        for a,b in zip(left["sample_quotes"],right["sample_quotes"]):
            lm=a["mid_reference_raw_quote"];im=b["mid_reference_raw_quote"]
            refs.append({"probe_utc":a["probe_utc"],"linear_usdt_mid":lm,
                "inverse_usd_mid":im,
                "inverse_usd_over_linear_usdt_raw_premium_bps":(im/lm-1)*10000,
                "FX_USD_USDT_adjustment_available":False,
                "NOT_ARBITRAGE_PROFIT":True})
        result["two_instruments_simultaneous_descriptive_quotes"]=refs
        result["verdict"]="REAL_TWO_BOOK_SAMPLES_QUOTE_ONLY_NO_FUNDING_EDGE"
    else:result["verdict"]="SOURCE_BLOCKED_NO_FULL_PAIR_PROOF"
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--linear",type=Path,required=True)
    ap.add_argument("--inverse",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=run({"LINEAR":a.linear,"INVERSE":a.inverse})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    for key,value in result["source_only_cases"].items():
        print("V03_CASE",json.dumps({"name":key,"status":value["status"],
            "samples":[{"time":x.get("probe_utc"),"status":x["status"],
            "bid":x.get("best_bid_raw_price"),"ask":x.get("best_ask_raw_price"),
            "age_ms":x.get("source_quote_age_ms")} for x in value.get("sample_quotes",[])]},
            sort_keys=True))
    print("V03_FINAL",result["verdict"],"NO_LIVE_GO")
if __name__=="__main__":main()

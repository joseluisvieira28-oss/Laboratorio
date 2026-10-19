"""V06 local source-only STOP_INTRABAR BID 5m exact frozen exit windows.

The private OKX portal tar.gz archives must NEVER be uploaded to GitHub.
This reader does not call the network, exchange or order APIs.
No actual stop trigger, fill, execution price or trade PnL is certified.
"""
import argparse,hashlib,json,math,tarfile
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
try:
 import orjson
 loads=orjson.loads
except ImportError:
 loads=json.loads

CONFIG={
 "SOL":{"inst":"SOL-USDT-SWAP","day":"2023-06-05","end_ms":1685981100000,
        "original_base_qty":"104.79202011433037","face_at_listing":"1",
        "binance_paper_stop":"19.647448704"},
 "BNB":{"inst":"BNB-USDT-SWAP","day":"2023-11-21","end_ms":1700588700000,
        "original_base_qty":"8.822493532731512","face_at_listing":"0.01",
        "binance_paper_stop":"239.72960000000002"},
}
SCALES=("0.25","0.5","0.75","1")
MAX_COMPRESSED=190_000_000
MAX_UNCOMPRESSED=1_500_000_000
MAX_RECORDS=6_000_000

def sell_sweep(bids,baseqty,face):
    contracts=Decimal(str(baseqty))/Decimal(str(face))
    remaining=contracts; paid=Decimal(0); levels=0
    for price,qty in sorted(bids.items(),reverse=True):
        take=min(remaining,Decimal(str(qty)))
        if take>0:
            levels+=1;paid+=Decimal(str(price))*take;remaining-=take
        if remaining==0:break
    best=Decimal(str(max(bids))) if bids else None
    done=contracts-remaining
    vwap=paid/done if done else None
    return {"full_visible_depth":remaining==0,"levels_used":levels,
            "contracts_unrounded":str(contracts),"unfilled_contracts":str(remaining),
            "hypothetical_bid_vwap":str(vwap) if vwap else None,
            "adverse_walk_bps":str((best/vwap-1)*10000) if vwap else None,
            "not_an_order_or_fill":True}

def observe(path,key):
    if key not in CONFIG:raise ValueError("UNREGISTERED_ORIGINAL_TRADE")
    q=CONFIG[key];p=Path(path)
    name=f"{q['inst']}-L2orderbook-400lv-{q['day']}"
    if not p.is_file() or p.is_symlink() or p.name!=name+".tar.gz":
        raise ValueError("INVALID_ORIGINAL_OKX_PORTAL_ARCHIVE")
    if p.stat().st_size>MAX_COMPRESSED:raise ValueError("COMPRESSED_CAP")
    digest=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):digest.update(chunk)
    daystart=int(datetime.fromisoformat(q["day"]).replace(tzinfo=timezone.utc).timestamp()*1000)
    start=q["end_ms"]-300000
    checkpoints=[start+i*60000 for i in range(5)]+[q["end_ms"]-1]
    bids={};asks={};last=None;prev=None
    records=0;snapshots=0;window_count=0;max_window_gap=0;largest_day_gap=0
    crossing=None;mn=math.inf;mx=-math.inf;last_sample=0;samples=[]
    def sample(t):
        if last is None:return {"time_ms":t,"status":"NO_PRIOR_BOOK"}
        age=t-last
        if age<0 or age>2000:return {"time_ms":t,"status":"STALE_OR_FUTURE","quote_age_ms":age}
        if len(bids)!=400 or len(asks)!=400 or max(bids)>=min(asks):
            return {"time_ms":t,"status":"INVALID_400_LEVEL_BOOK"}
        best=max(bids)
        return {"time_ms":t,"utc":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),
                "status":"CAUSAL_L2_SOURCE_ONLY","quote_age_ms":age,
                "best_bid":str(best),"best_ask":str(min(asks)),
                "full_original_qty_sell":sell_sweep(bids,q["original_base_qty"],q["face_at_listing"]),
                "four_static_relative_size_sweeps":[
                    {"fraction":s,**sell_sweep(bids,Decimal(q["original_base_qty"])*Decimal(s),q["face_at_listing"])}
                    for s in SCALES]}
    with tarfile.open(p,"r:gz") as archive:
        members=archive.getmembers()
        if len(members)!=1 or not members[0].isfile() or members[0].name!=name+".data":
            raise ValueError("UNEXPECTED_TAR_MEMBER_SCHEMA")
        if members[0].size>MAX_UNCOMPRESSED:raise ValueError("UNCOMPRESSED_CAP")
        reader=archive.extractfile(members[0])
        if reader is None:raise ValueError("UNREADABLE_DATA_MEMBER")
        first_after=None
        for line in reader:
            records+=1
            if records>MAX_RECORDS or len(line)>2_000_000:raise ValueError("RECORD_SIZE_CAP")
            ev=loads(line)
            if type(ev) is not dict or ev.get("instId")!=q["inst"]:
                raise ValueError("WRONG_HISTORICAL_INSTRUMENT")
            ts=int(ev["ts"])
            if ts>=q["end_ms"]:
                while last_sample<len(checkpoints):
                    samples.append(sample(checkpoints[last_sample]));last_sample+=1
                first_after=ts;break
            if ts<daystart or ts>=daystart+86400000 or (prev is not None and ts<prev):
                raise ValueError("TIME_ORDER_OR_UTC_DATE_INVALID")
            if prev is not None:
                largest_day_gap=max(largest_day_gap,ts-prev)
                if ts>=start:max_window_gap=max(max_window_gap,ts-prev)
            while last_sample<len(checkpoints) and ts>checkpoints[last_sample]:
                samples.append(sample(checkpoints[last_sample]));last_sample+=1
            action=ev.get("action")
            if action=="snapshot":
                snapshots+=1;bids.clear();asks.clear()
            elif action!="update" or snapshots==0:
                raise ValueError("NO_INITIAL_SNAPSHOT_OR_INVALID_ACTION")
            for side,book in (("bids",bids),("asks",asks)):
                data=ev.get(side)
                if type(data) is not list:raise ValueError("BAD_BOOK_SIDE")
                for level in data:
                    if type(level) is not list or len(level)!=3:raise ValueError("BAD_LEVEL")
                    px=float(level[0]);qt=float(level[1])
                    if not math.isfinite(px) or not math.isfinite(qt) or px<=0 or qt<0:
                        raise ValueError("INVALID_PRICE_OR_QTY")
                    if qt==0:book.pop(px,None)
                    else:book[px]=qt
                if len(book)>400:raise ValueError("OVER_400_LEVELS")
            prev=ts;last=ts
            if ts>=start:
                window_count+=1
                if not bids or not asks or max(bids)>=min(asks):
                    raise ValueError("CROSSED_OR_EMPTY_BOOK_IN_STOP_BAR")
                bid=max(bids);mn=min(mn,bid);mx=max(mx,bid)
                if crossing is None and bid<=float(q["binance_paper_stop"]):
                    crossing={"utc":datetime.fromtimestamp(ts/1000,timezone.utc).isoformat(),
                              "relative_to_original_stop_bar_start_ms":ts-start,
                              "first_bid_at_or_below_paper_binance_stop":str(bid),
                              "full_original_qty_sell":sell_sweep(bids,q["original_base_qty"],q["face_at_listing"]),
                              "not_broker_trigger_or_fill":True}
        else:
            first_after=None
            while last_sample<len(checkpoints):
                samples.append(sample(checkpoints[last_sample]));last_sample+=1
    if len(samples)!=6:raise ValueError("SIX_PREDECLARED_SAMPLES_MISSING")
    return {"status":"SIX_CAUSAL_L2_SAMPLES_NO_SEQ_PROOF" if all(x["status"]=="CAUSAL_L2_SOURCE_ONLY" for x in samples) else "INCOMPLETE_SOURCE_COVERAGE",
            "instrument":q["inst"],"date_utc":q["day"],"original_stop_bar_start_ms":start,
            "original_stop_bar_end_ms":q["end_ms"],
            "original_model_binance_raw_stop":q["binance_paper_stop"],
            "original_base_asset_qty":q["original_base_qty"],
            "launch_announced_contract_face_base_not_verified_at_2023":q["face_at_listing"],
            "source_sha256_local_only_not_publisher_signed":digest.hexdigest(),
            "compressed_bytes":p.stat().st_size,
            "source_events_until_original_bar_end":records,
            "snapshots_until_bar_end":snapshots,"events_in_original_stop_bar":window_count,
            "max_whole_day_event_gap_ms":largest_day_gap,"max_event_gap_into_stop_bar_ms":max_window_gap,
            "original_5min_bar_best_bid_min":str(mn),"original_5min_bar_best_bid_max":str(mx),
            "first_quote_after_bar_end_NOT_CONSUMED_ms":first_after,
            "first_bid_cross_within_original_bar":crossing,
            "six_reference_quotes":samples,
            "sequence_ids_present":False,"lossless_update_continuity_proven":False,
            "real_stop_or_order_ack":False,"point_in_time_contract_lot_verified":False,
            "this_does_not_reconstruct_full_trade":True,"trading_authority":"NONE"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sol",type=Path)
    p.add_argument("--bnb",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    results={}
    for key,path in (("SOL",a.sol),("BNB",a.bnb)):
        if path is None:continue
        try:results[key]=observe(path,key)
        except Exception as exc:results[key]={"status":"SOURCE_FAIL_CLOSED","reason":type(exc).__name__+":"+str(exc)[:110]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps({"classification":"HISTORICAL_EXIT_BID_SOURCE_ONLY_NOT_OOS",
                                  "private_raw_archive_data_published":False,
                                  "2026_holdout_opened":False,"models":results,"trading_authority":"NONE"},
                                 indent=2,sort_keys=True)+"\n",encoding="utf8")
    for key,row in results.items():
        print("V06_EXIT_BID_RECEIPT",json.dumps({
            "symbol":key,"source_status":row["status"],
            "original_intrabar_best_bid_range":[row.get("original_5min_bar_best_bid_min"),row.get("original_5min_bar_best_bid_max")],
            "first_paper_bid_cross":row.get("first_bid_cross_within_original_bar"),
            "reference_samples":len(row.get("six_reference_quotes",[]))},sort_keys=True))
if __name__=="__main__":main()

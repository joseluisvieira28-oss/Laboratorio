#!/usr/bin/env python3
"""Fixed first-hour 2024/2025 historical original OKX 400-level SPOT vs USDT-SWAP L2.
Not the OKX/MEXC model, no real MEXC Event Futures payout, account, orders or spending.
Pre-outcome freeze BTC10M_OKX_ORIGINAL_TRUE_L2_FIRST_HOUR_PREOUTCOME_FREEZE_V03_2026_10_31.md.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import pathlib
import tarfile
import urllib.request
import zlib
from datetime import timezone

ROOT=pathlib.Path("artifacts/btc10m_okx_true_l2_pilot_v03")
BASE="https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily"
DAYS=("2024-01-01","2025-01-01")
VENUES=("SPOT","SWAP")
MAX_BYTES=33_554_432
BLOCK=65536
ORIG_SIZE={
("2024-01-01","SPOT"):129489825,
("2024-01-01","SWAP"):376662567,
("2025-01-01","SPOT"):225603298,
("2025-01-01","SWAP"):350454127}
class Gate(Exception):pass
def ms(day):return int(dt.datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
def utc():return dt.datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha(data):return hashlib.sha256(data).hexdigest()
def url_for(day,venue):
    s="BTC-USDT" if venue=="SPOT" else "BTC-USDT-SWAP"
    return f"{BASE}/{day.replace('-','')}/{s}-L2orderbook-400lv-{day}.tar.gz"
def targets(day):
    zero=ms(day)
    boundaries=[zero+minute*60000 for minute in (10,20,30,40,50)]
    arr=[]
    for b in boundaries:
        arr.extend([b+12000,b+17000,b+22000,b+24000,b+624000])
    return sorted(set(arr))
def asof_state(book,original_symbol,last_ts,at):
    if last_ts is None:return {"target_ms":at,"status":"NO_PRIOR_FULL_SNAPSHOT"}
    if last_ts>at or at-last_ts>2000:
        return {"target_ms":at,"status":"STALE_OR_NONCAUSAL","last_ts":last_ts}
    bids=sorted(book["bids"].items(),reverse=True)[:5]
    asks=sorted(book["asks"].items())[:5]
    if len(bids)<5 or len(asks)<5:
        return {"target_ms":at,"status":"SHALLOW_BOOK","last_ts":last_ts}
    bp=bids[0][0];ap=asks[0][0]
    if not 0<bp<ap:return {"target_ms":at,"status":"CROSSED_BOOK","last_ts":last_ts}
    spread=20000*(ap-bp)/(ap+bp)
    if spread>10:return {"target_ms":at,"status":"SPREAD_GATE","last_ts":last_ts}
    bn=sum(p*a for p,a in bids)
    an=sum(p*a for p,a in asks)
    if bn<=0 or an<=0:return {"target_ms":at,"status":"NO_NOTIONAL","last_ts":last_ts}
    return {"target_ms":at,"status":"VALID_L2_STATE","last_ts":last_ts,"symbol":original_symbol,
            "imbalance":(bn-an)/(bn+an),"spread_bps":spread,"mid":(bp+ap)/2,
            "bids5":[[float(p),float(a)] for p,a in bids],
            "asks5":[[float(p),float(a)] for p,a in asks]}
def apply(book,j,expected):
    if j.get("instId")!=expected:raise Gate("WRONG_EXACT_INSTRUMENT")
    typ=j.get("action")
    if typ not in ("snapshot","update"):raise Gate("UNKNOWN_BOOK_ACTION")
    if typ=="snapshot":
        book["bids"].clear();book["asks"].clear();book["ready"]=True
    if not isinstance(j.get("bids"),list) or not isinstance(j.get("asks"),list):
        raise Gate("NOT_BOOK_L2_ROWS")
    if not book["ready"]:return False
    for key in ("bids","asks"):
        state=book[key]
        for level in j[key]:
            if not isinstance(level,list) or len(level)<2:raise Gate("BAD_L2_LEVEL")
            try:p=float(level[0]);q=float(level[1])
            except Exception as e:raise Gate("BAD_LEVEL_NUMERIC") from e
            if not all(math.isfinite(x) for x in (p,q)) or p<=0 or q<0:
                raise Gate("BAD_PRICE_OR_AMOUNT")
            if q==0:state.pop(p,None)
            else:state[p]=q
    return True
def replay_original_prefix(day,venue):
    symbol="BTC-USDT" if venue=="SPOT" else "BTC-USDT-SWAP"
    url=url_for(day,venue)
    req=urllib.request.Request(url,method="GET",headers={"Range":f"bytes=0-{MAX_BYTES-1}",
        "User-Agent":"CryptoLab-OKX-TrueL2-LimitedHistoricPilot/1.0"})
    result={"day":day,"venue":venue,"symbol":symbol,"url":url,
            "source_started_utc":utc(),"source_bytes":0,"book_event_count":0,"snapshots":0,
            "updates_before_first_snapshot":0,"first_event_ts":None,"last_event_ts":None,
            "source_status":"SOURCE_BLOCKED","source_original_prices_saved":False}
    expected_len=ORIG_SIZE[(day,venue)]
    needed=targets(day)
    next_i=0
    states={}
    book={"bids":{},"asks":{},"ready":False}
    last_ts=None;prev_ts=None
    hasher=hashlib.sha256()
    decoder=zlib.decompressobj(31)
    pending=b"";tar_parsed=False
    raw_file=ROOT/f"{day}_{venue.lower()}_original_prefix.bin"
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            result["http_status"]=response.status
            result["content_range"]=response.headers.get("Content-Range")
            if response.status!=206 or result["content_range"]!=f"bytes 0-{MAX_BYTES-1}/{expected_len}":
                raise Gate("ORIGINAL_RANGE_IDENTITY_MISMATCH")
            with raw_file.open("wb") as dest:
                while result["source_bytes"]<MAX_BYTES:
                    block=response.read(min(BLOCK,MAX_BYTES-result["source_bytes"]))
                    if not block:break
                    hasher.update(block);dest.write(block)
                    result["source_bytes"]+=len(block)
                    decompressed=decoder.decompress(block)
                    pending+=decompressed
                    if not tar_parsed and len(pending)>=512:
                        info=tarfile.TarInfo.frombuf(pending[:512],encoding="utf-8",errors="replace")
                        if info.name!=f"{symbol}-L2orderbook-400lv-{day}.data":
                            raise Gate("TAR_MEMBER_WRONG")
                        result["original_tar_name"]=info.name
                        tar_parsed=True
                        pending=pending[512:]
                    if not tar_parsed:continue
                    if len(pending)>10_000_000:raise Gate("DECOMPRESS_PARSE_BACKLOG")
                    while b"\n" in pending:
                        line,pending=pending.split(b"\n",1)
                        if not line.strip():continue
                        try:j=json.loads(line)
                        except Exception as e:raise Gate("NDJSON_PARSE_FAILED") from e
                        try:t=int(j.get("ts"))
                        except Exception as e:raise Gate("EXCHANGE_TS_INVALID") from e
                        if t<ms(day) or t>=ms(day)+86400000:raise Gate("ROW_OUTSIDE_UTC_DAY")
                        if prev_ts is not None and t<prev_ts:
                            raise Gate("EXCHANGE_TS_REGRESSION_NONCAUSAL")
                        # All target features before incoming next event MUST reflect preceding state only.
                        while next_i<len(needed) and needed[next_i]<t:
                            at=needed[next_i]
                            states[str(at)]=asof_state(book,symbol,last_ts,at)
                            next_i+=1
                        if result["first_event_ts"] is None:result["first_event_ts"]=t
                        result["book_event_count"]+=1
                        if j.get("action")=="snapshot":result["snapshots"]+=1
                        if j.get("action")=="update" and not book["ready"]:
                            result["updates_before_first_snapshot"]+=1
                        if apply(book,j,symbol):last_ts=t
                        prev_ts=t;result["last_event_ts"]=t
                    if next_i>=len(needed):
                        break
    except Exception as e:
        result["source_status"]="SOURCE_BLOCKED"
        result["error"]=type(e).__name__+":"+str(e)[:240]
    else:
        result["source_status"]="ALL_FROZEN_ASOF_TARGETS_RECONSTRUCTED" if next_i==len(needed) else "SOURCE_WINDOW_INCOMPLETE"
    result["raw_partial_sha256"]=hasher.hexdigest()
    result["partial_raw_filename"]=raw_file.name
    result["captured_target_count"]=len(states)
    result["expected_target_count"]=len(needed)
    result["valid_asof_state_count"]=sum(x["status"]=="VALID_L2_STATE" for x in states.values())
    result["source_finished_utc"]=utc()
    return result,states
def decision(one_day,spot,swap):
    final=[]
    for minute in (10,20,30,40,50):
        b=ms(one_day)+minute*60000
        paired=[]
        reason=[]
        for second in (12000,17000,22000):
            s=spot.get(str(b+second));p=swap.get(str(b+second))
            if s is None or p is None or s["status"]!="VALID_L2_STATE" or p["status"]!="VALID_L2_STATE":
                reason.append(f"INCOMPLETE_ASOF_{minute}_{second}")
                paired.append(None)
            else:
                paired.append([s["imbalance"],p["imbalance"]])
        start=spot.get(str(b+24000));end=spot.get(str(b+624000))
        side="ABSTAIN"
        if not reason and len(paired)==3 and all(x[0]>=.25 and x[1]<=-.25 for x in paired):side="UP"
        if not reason and len(paired)==3 and all(x[0]<=-.25 and x[1]>=.25 for x in paired):side="DOWN"
        if start is None or end is None or start["status"]!="VALID_L2_STATE" or end["status"]!="VALID_L2_STATE":
            reason.append("NO_TIMELY_10MIN_SPOT_PRICE_REFERENCE")
        label=None;correct=None
        if not reason:
            label="UP" if end["mid"]>start["mid"] else "DOWN" if end["mid"]<start["mid"] else "TIE"
            correct=(side==label) if side!="ABSTAIN" and label!="TIE" else None
        final.append({"day":one_day,"slot_utc_minute":minute,
              "decision_ms":b+24000,"expiry_ms":b+624000,"side":side,
              "status":"PAPER_L2_SAMPLE_VALID" if not reason else "INVALID_ASOF_SAMPLE",
              "reasons":reason,"three_venue_imbalances":paired,
              "idealized_future_spot_mid_label":label if side!="ABSTAIN" else None,
              "qualified_outcome_correct":correct if side!="ABSTAIN" else None,
              "event_futures_settlement_parity_proven":False})
    return final
def tests():
    book={"bids":{},"asks":{},"ready":False}
    assert not apply(book,{"action":"update","instId":"BTC-USDT","bids":[["99","1"]],
        "asks":[["100","1"]]},"BTC-USDT") and not book["ready"]
    assert apply(book,{"action":"snapshot","instId":"BTC-USDT",
        "bids":[[str(100-i),str(i+1)] for i in range(5)],
        "asks":[[str(100.01+i*0.01),str(i+1)] for i in range(5)]},"BTC-USDT")
    assert book["ready"] and len(book["bids"])==5
    assert asof_state(book,"BTC-USDT",1000,2000)["status"]=="VALID_L2_STATE"
    assert asof_state(book,"BTC-USDT",1000,5000)["status"]=="STALE_OR_NONCAUSAL"
    apply(book,{"action":"update","instId":"BTC-USDT","bids":[["100","0"]],
        "asks":[]},"BTC-USDT")
    assert 100.0 not in book["bids"]
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    tests()
    out={"study":"BTC10M_OKX_SPOT_SWAP_FIRST_HOUR_ACTUAL_L2_PILOT_V03",
     "preoutcome_freeze":"research/btc10m_okx_l2_v01/BTC10M_OKX_ORIGINAL_TRUE_L2_FIRST_HOUR_PREOUTCOME_FREEZE_V03_2026_10_31.md",
     "date_started_utc":utc(),"status":"SOURCE_REPLAY_BLOCKED",
     "data_provider":"OKX official 400-level archived historical orderbook, limited first 32MiB per venue/day",
     "model":"3 pairs at sec12,17,22; spot>=.25 & swap<=-.25 UP or mirror DOWN; else ABSTAIN",
     "source_receipts":[],"observations_by_day":{},"actual_orders":0,"account_calls":0,
     "money_spent":0,"protected_2026_outcomes_opened":False,"economic_edge_certified":False}
    try:
        overall=[]
        for day in DAYS:
            a,spot=replay_original_prefix(day,"SPOT")
            b,swap=replay_original_prefix(day,"SWAP")
            out["source_receipts"].extend([a,b])
            rows=decision(day,spot,swap)
            out["observations_by_day"][day]=rows
            overall.extend(rows)
            (ROOT/f"{day}_strict_asof_reconstruction.json").write_text(json.dumps(
                {"day":day,"spot_states":spot,"swap_states":swap},sort_keys=True)+"\n")
            print("DAY_RECEIPT",json.dumps({"day":day,"source_status":[a["source_status"],b["source_status"]],
                "source_ranges_bytes":[a["source_bytes"],b["source_bytes"]],
                "book_events":[a["book_event_count"],b["book_event_count"]],
                "snapshots":[a["snapshots"],b["snapshots"]],
                "valid_states":[a["valid_asof_state_count"],b["valid_asof_state_count"]],
                "all_slots":[{"minute":x["slot_utc_minute"],"status":x["status"],"side":x["side"]} for x in rows]},sort_keys=True),flush=True)
        valid=[x for x in overall if x["status"]=="PAPER_L2_SAMPLE_VALID"]
        qualified=[x for x in valid if x["side"] in ("UP","DOWN")]
        wins=sum(x["qualified_outcome_correct"] is True for x in qualified)
        losses=sum(x["qualified_outcome_correct"] is False for x in qualified)
        ties=len(qualified)-wins-losses
        out["summary"]={"all_frozen_slots":len(overall),"valid_10m_slots":len(valid),
          "qualified_up_down_signals":len(qualified),
          "correct_direction":wins,"wrong_direction":losses,"ties":ties,
          "direction_accuracy_nontie":wins/(wins+losses) if wins+losses else None,
          "hypothetical_constant_q070_pnl_per_stake":(.7*wins-losses)/len(qualified) if qualified else None,
          "sample_size_sufficient_for_economic_inference":False}
        if any(x["source_status"]!="ALL_FROZEN_ASOF_TARGETS_RECONSTRUCTED" for x in out["source_receipts"]) or len(valid)!=len(overall):
            out["status"]="SOURCE_REPLAY_BLOCKED_OR_INCOMPLETE"
        elif not qualified:out["status"]="ZERO_SIGNALS_IN_TINY_FIRST_HOUR_HISTORIC_PILOT"
        else:out["status"]="TINY_HISTORICAL_PILOT_LABELS_OBSERVED_NO_EDGE_INFERENCE"
    except Exception as e:
        out["status"]="SOURCE_REPLAY_BLOCKED"
        out["error"]=type(e).__name__+":"+str(e)[:350]
    finally:
        out["finished_utc"]=utc()
        (ROOT/"receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("FINAL_PILOT",json.dumps({key:out.get(key) for key in ("status","error","summary","model")},sort_keys=True),flush=True)
    if out["status"].startswith("SOURCE_REPLAY_BLOCKED"):raise SystemExit(2)
if __name__=="__main__":main()

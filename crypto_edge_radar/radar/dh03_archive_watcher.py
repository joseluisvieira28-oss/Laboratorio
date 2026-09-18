from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
import json
import os
from typing import Any

from .binance_usdm_archive import BinanceArchiveError, SYMBOLS, load_verified_daily_1m_rows
from .binance_usdm_monthly_funding import BinanceMonthlyFundingError, load_verified_monthly_funding
from .dh03_12h_forward import FIRST_SIGNAL_BAR_OPEN_MS, MAX_HOLD_MS, MinuteBar, aggregate_12h, derive_signals, simulate_signal
from .evidence import build_evidence_store

WARMUP_START=date(2026,8,28)
FIRST_ARCHIVE_FORWARD_DAY=date(2026,9,18)
FUNDING_START_MONTH="2026-09"
STRATEGY_ID="HTF-DH03-12H-STANDALONE-FORWARD-V1"

def _days(start:date,end:date):
    d=start
    while d<=end:
        yield d
        d+=timedelta(days=1)

def _month_start_ms(ym:str)->int:
    y,m=map(int,ym.split("-"))
    return int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)

def _month_after(ym:str)->str:
    y,m=map(int,ym.split("-"))
    return f"{y+1:04d}-01" if m==12 else f"{y:04d}-{m+1:02d}"

def _completed_months_through(latest_day:date)->list[str]:
    current=FUNDING_START_MONTH
    stop=f"{latest_day.year:04d}-{latest_day.month:02d}"
    out=[]
    while current<stop:
        out.append(current)
        current=_month_after(current)
    return out

def _load_price_corpus(latest_day:date,timeout:int=30):
    minutes:dict[str,list[MinuteBar]]={s:[] for s in SYMBOLS}
    source=[]
    for s in SYMBOLS:
        for d in _days(WARMUP_START,latest_day):
            row=load_verified_daily_1m_rows(s,d,timeout=timeout)
            source.append({"symbol":s,"day":d.isoformat(),"sha256":row["sha256"],"row_count":len(row["rows"]),"checksum_verified":row["checksum_verified"],"forward_role":"FORWARD_OR_EXECUTION" if d>=FIRST_ARCHIVE_FORWARD_DAY else "WARMUP_ONLY"})
            minutes[s].extend(MinuteBar(*x) for x in row["rows"])
    return minutes,source

def _load_final_funding(latest_day:date,timeout:int=30):
    events={s:([],[]) for s in SYMBOLS}
    receipts=[]
    complete_through_ms=_month_start_ms(FUNDING_START_MONTH)
    missing=[]
    for ym in _completed_months_through(latest_day):
        month_ok=True
        month_rows={}
        for s in SYMBOLS:
            try:
                row=load_verified_monthly_funding(s,ym,timeout=timeout)
                month_rows[s]=row
            except BinanceMonthlyFundingError as exc:
                missing.append({"month":ym,"symbol":s,"error":str(exc)})
                month_ok=False
                break
        if not month_ok:
            break
        for s,row in month_rows.items():
            times,rates=events[s]
            for e in row["events"]:
                times.append(int(e["funding_time_ms"]))
                rates.append(float(e["funding_rate"]))
            receipts.append({"symbol":s,"month":ym,"sha256":row["sha256"],"event_count":row["event_count"],"checksum_verified":True})
        complete_through_ms=_month_start_ms(_month_after(ym))
    return events,receipts,complete_through_ms,missing

def evaluate_corpus(minutes_by_symbol:dict[str,list[MinuteBar]],funding_by_symbol:dict[str,tuple[list[int],list[float]]],funding_complete_through_ms:int)->dict[str,Any]:
    symbols={}
    totals={"signals":0,"price_exits":0,"final_resolutions":0,"funding_pending":0,"unresolved_price_paths":0,"overlap_skipped":0}
    for s in SYMBOLS:
        minutes=minutes_by_symbol[s]
        bars,incomplete=aggregate_12h(minutes)
        signals,diag=derive_signals(s,bars)
        ftimes,frates=funding_by_symbol.get(s,([],[]))
        active_until=None
        rows=[]
        overlap=0
        for sig in signals:
            if active_until is not None and sig.entry_open_time<=active_until:
                overlap+=1
                continue
            provisional=simulate_signal(sig,minutes,[],[])
            active_until=provisional.exit_time if provisional.exit_time is not None else sig.entry_open_time+MAX_HOLD_MS
            entry={"signal":asdict(sig),"price_exit_time":provisional.exit_time,"price_exit_price":provisional.exit_price,"price_exit_reason":provisional.exit_reason,"price_path_unresolved":provisional.execution_path_unresolved,"funding_reconciliation_pending":True,"final_resolution":None}
            if provisional.execution_path_unresolved:
                totals["unresolved_price_paths"]+=1
            else:
                totals["price_exits"]+=1
                if provisional.exit_time is not None and provisional.exit_time<=funding_complete_through_ms:
                    final=simulate_signal(sig,minutes,ftimes,frates)
                    if final.execution_path_unresolved:
                        raise RuntimeError("final replay diverged from resolved price path")
                    entry["funding_reconciliation_pending"]=False
                    entry["final_resolution"]=asdict(final)
                    totals["final_resolutions"]+=1
                else:
                    totals["funding_pending"]+=1
            rows.append(entry)
        totals["signals"]+=len(rows)
        totals["overlap_skipped"]+=overlap
        symbols[s]={"complete_12h_bars":len(bars),"incomplete_12h_buckets":incomplete,"signal_diagnostics":diag,"selected_signals":len(rows),"overlap_skipped":overlap,"rows":rows}
    return {"symbols":symbols,"totals":totals}

def _persist(store,receipt:dict[str,Any])->dict[str,int]:
    inserted={"signals":0,"price_exits":0,"final_resolutions":0,"snapshots":0}
    for s,row in receipt["evaluation"]["symbols"].items():
        for item in row["rows"]:
            sig=item["signal"]
            fp=sig["fingerprint"]
            signal_payload={"strategy_id":STRATEGY_ID,"symbol":s,"signal":sig,"source_mode":"BINANCE_PUBLIC_ARCHIVE_CHECKSUM_VERIFIED","used_as_forward_evidence":True,"authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False}
            rr=store.append_once("DH03_FORWARD_SIGNAL",f"{STRATEGY_ID}:signal:{fp}",signal_payload)
            inserted["signals"]+=int(bool(rr["inserted"]))
            if item["price_exit_time"] is not None and not item["price_path_unresolved"]:
                price_payload={"strategy_id":STRATEGY_ID,"symbol":s,"signal_fingerprint":fp,"exit_time":item["price_exit_time"],"exit_price":item["price_exit_price"],"exit_reason":item["price_exit_reason"],"funding_reconciliation_pending":item["funding_reconciliation_pending"],"authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False}
                rr=store.append_once("DH03_FORWARD_PRICE_EXIT",f"{STRATEGY_ID}:price-exit:{fp}",price_payload)
                inserted["price_exits"]+=int(bool(rr["inserted"]))
            if item["final_resolution"] is not None:
                final_payload={"strategy_id":STRATEGY_ID,"symbol":s,"signal_fingerprint":fp,"resolution":item["final_resolution"],"funding_authority":"BINANCE_PUBLIC_DATA_MONTHLY_FUNDINGRATE_CHECKSUM_VERIFIED","authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False}
                rr=store.append_once("DH03_FORWARD_FINAL_RESOLUTION",f"{STRATEGY_ID}:final:{fp}",final_payload)
                inserted["final_resolutions"]+=int(bool(rr["inserted"]))
    snap_key=f"{STRATEGY_ID}:snapshot:{receipt['latest_archive_day']}"
    snap={"strategy_id":STRATEGY_ID,"latest_archive_day":receipt["latest_archive_day"],"status":receipt["status"],"totals":receipt["evaluation"]["totals"],"funding_complete_through_ms":receipt["funding_complete_through_ms"],"source_price_file_count":len(receipt["price_source_receipts"]),"source_funding_file_count":len(receipt["funding_source_receipts"]),"authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False,"live_capital_enabled":False}
    rr=store.append_once("DH03_FORWARD_SNAPSHOT",snap_key,snap)
    inserted["snapshots"]+=int(bool(rr["inserted"]))
    return inserted

def run_once(*,now:datetime|None=None,persist:bool=True)->dict[str,Any]:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    latest_day=now.astimezone(timezone.utc).date()-timedelta(days=1)
    base={"strategy_id":STRATEGY_ID,"checked_at_utc":now.astimezone(timezone.utc).isoformat().replace("+00:00","Z"),"latest_archive_day":latest_day.isoformat(),"mode":"PUBLIC_ARCHIVE_SHADOW_ONLY","authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False,"live_capital_enabled":False}
    if latest_day<FIRST_ARCHIVE_FORWARD_DAY:
        return {**base,"status":"WAITING_FIRST_ELIGIBLE_ARCHIVE_DAY","first_forward_archive_day":FIRST_ARCHIVE_FORWARD_DAY.isoformat(),"used_as_forward_evidence":False}
    try:
        minutes,price_receipts=_load_price_corpus(latest_day)
    except BinanceArchiveError as exc:
        if "404" in str(exc):
            return {**base,"status":"WAITING_ARCHIVE_PUBLICATION","error":str(exc)}
        raise
    funding,funding_receipts,complete_through,missing=_load_final_funding(latest_day)
    evaluation=evaluate_corpus(minutes,funding,complete_through)
    receipt={**base,"status":"OK","first_signal_bar_open_ms":FIRST_SIGNAL_BAR_OPEN_MS,"warmup_start":WARMUP_START.isoformat(),"price_source_receipts":price_receipts,"funding_source_receipts":funding_receipts,"funding_missing":missing,"funding_complete_through_ms":complete_through,"evaluation":evaluation,"used_as_forward_evidence":True}
    if persist:
        db_path=os.getenv("RADAR_DB","/tmp/dh03_shadow.sqlite3")
        database_url=os.getenv("RADAR_DATABASE_URL") or os.getenv("DATABASE_URL")
        store=build_evidence_store(db_path,database_url)
        receipt["evidence_backend"]=store.backend
        receipt["inserted"]=_persist(store,receipt)
        ok,detail=store.verify_chain()
        receipt["evidence_chain_ok"]=ok
        receipt["evidence_chain_detail"]=detail
        if not ok:
            raise RuntimeError(f"evidence chain failed:{detail}")
    return receipt

def main()->int:
    try:
        r=run_once()
        print(json.dumps(r,sort_keys=True))
        return 0 if r["status"] in {"OK","WAITING_FIRST_ELIGIBLE_ARCHIVE_DAY","WAITING_ARCHIVE_PUBLICATION"} else 2
    except Exception as exc:
        print(json.dumps({"strategy_id":STRATEGY_ID,"status":"FAIL_CLOSED","error":f"{type(exc).__name__}:{exc}","authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False,"live_capital_enabled":False},sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

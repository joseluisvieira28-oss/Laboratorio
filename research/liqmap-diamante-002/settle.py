#!/usr/bin/env python3
"""LIQMAP-002 post-maturity 24-full-hour settlement: price touches, not actual liquidations."""
import datetime as dt
import json
import math
import pathlib

import point as p

HERE=pathlib.Path(__file__).resolve().parent
OBS=HERE/"observations"
SET=HERE/"settlements"
OUT=HERE/"run_results"
H=p.ONE_H
NOW_BUFFER_MS=60000
FEES=(10,35,80)

def first_full_hour(captured):
    ms=p.millis(dt.datetime.fromisoformat(captured))
    return (ms//H+1)*H

def touch(bars,mark,target,mirror):
    higher=max(target,mirror);lower=min(target,mirror)
    for i,c in enumerate(bars):
        up=c["h"]>=higher
        down=c["l"]<=lower
        if up and down:return {"kind":"AMBIGUOUS","i":i,"price":None}
        if up:return {"kind":"UP_FIRST","i":i,"price":higher}
        if down:return {"kind":"DOWN_FIRST","i":i,"price":lower}
    return {"kind":"NEITHER","i":len(bars)-1,"price":bars[-1]["c"]}

def classify(first,choice):
    if first["kind"]=="AMBIGUOUS":return "AMBIGUOUS"
    if first["kind"]=="NEITHER":return "NEITHER"
    return "TARGET_FIRST" if first["kind"]==choice+"_FIRST" else "MIRROR_FIRST"

def pnl(bars,first,choice,mark,target,mirror,fee):
    entry=bars[0]["o"]
    target_side=target if (choice=="UP")== (target>mark) else mirror
    stop_side=mirror if target_side==target else target
    if not 0<entry or not 0<target_side or not 0<stop_side:
        raise ValueError("invalid PnL prices")
    gap=(entry>=max(target,mirror) or entry<=min(target,mirror))
    if first["kind"]=="AMBIGUOUS":
        exit_price=stop_side
    elif first["kind"]=="NEITHER":
        exit_price=bars[-1]["c"]
    else:
        exit_price=first["price"]
    signed=1 if choice=="UP" else -1
    gross=signed*(exit_price/entry-1)
    if first["kind"]=="AMBIGUOUS" or gap:
        gross=min(gross,0.,-abs(stop_side/entry-1))
    return {"gross_bps":round(10000*gross,6),
            "net_bps":round(10000*gross-2*(fee+5),6),
            "hypothetical_fill_only":True,"entry_gap_uncertain":gap}

def settle_one(record,now=None):
    now=now or p.utc()
    if record.get("status")!="FUTURE_PENDING_OUTCOME" or not record.get("is_future_economic_observation"):
        return None
    first=first_full_hour(record["captured_utc"])
    end=first+24*H
    if p.millis(now)<end+NOW_BUFFER_MS:return None
    req,rc,raw=p.hl_candles(first,end-1)
    bars=p.clean_candles(req,first,24,now_ms=p.millis(now)-NOW_BUFFER_MS)
    f=record["forecast"]
    first_hit=touch(bars,f["mark"],f["target"],f["mirror"])
    chosen=f["signal"]
    mom=record["prior_momentum24_direction"]
    if chosen not in ("UP","DOWN") or mom not in ("UP","DOWN"):
        raise ValueError("invalid locked signal")
    result={"study":"LIQMAP-DIAMANTE-002","request_date":record["requested_date"],
       "captured_utc":record["captured_utc"],
       "future_candle_first_utc":dt.datetime.fromtimestamp(first/1000,dt.timezone.utc).isoformat(),
       "future_candle_end_utc":dt.datetime.fromtimestamp(end/1000,dt.timezone.utc).isoformat(),
       "price_source_receipt":rc,
       "forecast_lock_sha256":__import__("hashlib").sha256(
           json.dumps(record,sort_keys=True).encode()).hexdigest(),
       "source_map_sha256":record["receipts"][0]["raw_sha256"],
       "first_touch":first_hit["kind"],"model_result":classify(first_hit,chosen),
       "momentum_result":classify(first_hit,mom),
       "n_complete_price_candles":len(bars),"executed_trades":0,
       "economic_PnL_only_modeled":True,
       "simulated_fee_stress":{}}
    for fee in FEES:
        result["simulated_fee_stress"][str(fee)]={
           "map":pnl(bars,first_hit,chosen,f["mark"],f["target"],f["mirror"],fee),
           "mom24":pnl(bars,first_hit,mom,f["mark"],f["target"],f["mirror"],fee)}
    # Full original market candles are not published with the summary; raw source archived in artifact.
    (OUT/("price_candles_raw_"+record["requested_date"]+".json")).write_bytes(raw)
    return result

def main():
    OBS.mkdir(parents=True,exist_ok=True)
    SET.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[]
    for path in sorted(OBS.glob("*.json")):
        date=path.stem
        existing=SET/(date+".json")
        if existing.exists():continue
        record=json.loads(path.read_text())
        if record.get("status")!="FUTURE_PENDING_OUTCOME":
            # Persist a non-trade terminal condition once, don't cherry-pick source failures away.
            terminal={"request_date":date,"status":record.get("status","UNKNOWN"),
                      "economically_valid":False,"executed_trades":0}
            existing.write_text(json.dumps(terminal,indent=2)+"\n")
            summary.append((date,terminal["status"]))
            continue
        try:
            result=settle_one(record)
        except Exception as e:
            result={"request_date":date,"status":"SETTLEMENT_SOURCE_BLOCKED",
              "error":type(e).__name__+": "+str(e),"economically_valid":False,
              "executed_trades":0}
        if result is None:
            summary.append((date,"NOT_MATURED"))
            continue
        if "status" not in result:result["status"]="MATURED_OUTCOME"
        result["economically_valid"]=result["status"]=="MATURED_OUTCOME"
        existing.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        summary.append((date,result["status"]))
    (OUT/"SETTLEMENT_DAILY_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("LIQMAP002_SETTLE",summary,flush=True)

if __name__=="__main__":main()

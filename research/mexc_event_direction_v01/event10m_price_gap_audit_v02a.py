#!/usr/bin/env python3
"""Offline price-stream continuity audit. Never inspect price content."""
import json, pathlib, statistics
ROOT=pathlib.Path("artifacts/event10m_crossvenue_price_forensics_v02a")
SOURCE=pathlib.Path("downloaded/source_receipt.json")
EXPECTED={"BTC":{"binance":2111,"mexc":59},"ETH":{"binance":1671,"mexc":55}}
WINDOW=30_000_000_000
def audit():
    obj=json.loads(SOURCE.read_text())
    assert obj["lab"]=="E10M_XVENUE_PRICE_PARITY_SOURCE_V02"
    assert obj["gate"]=="PRICE_SOURCE_INCOMPLETE"
    assert obj["market_direction_outcomes_opened"]==0
    assert obj["account_or_orders"]==0
    series=obj["observations"]
    assert set(series)=={"BTC","ETH"}
    all_t=[]
    for sym in ("BTC","ETH"):
        for venue in ("binance","mexc"):
            rows=series[sym][venue]
            assert len(rows)==EXPECTED[sym][venue],(sym,venue,len(rows))
            all_t.extend(int(row[0]) for row in rows)
    ref=min(all_t);end=max(all_t)
    report={"study":"E10M_XVENUE_PRICE_STREAM_GAP_AUDIT_V02A",
            "source_run_id":41032128118,"source_artifact_id":12965304781,
            "source_gate_unchanged":"PRICE_SOURCE_INCOMPLETE",
            "source_stream_errors":{v:x.get("error") for v,x in obj["streams"].items()},
            "source_overall_observation_span_s":round((end-ref)/1e9,3),
            "per_symbol":{},"forward_10min_outcomes_opened":0,
            "trade_actions":0,"source_requests_new":0}
    for sym in ("BTC","ETH"):
        d={}
        for venue in ("binance","mexc"):
            stamps=sorted(int(row[0]) for row in series[sym][venue])
            gaps=[(stamps[i]-stamps[i-1])/1e9 for i in range(1,len(stamps))]
            bins={}
            for stamp in stamps:
                n=int((stamp-ref)//WINDOW)
                bins[str(n*30)+"-"+str((n+1)*30)+"s"]=bins.get(str(n*30)+"-"+str((n+1)*30)+"s",0)+1
            d[venue]={"count":len(stamps),"first_since_common_s":round((stamps[0]-ref)/1e9,3),
               "last_since_common_s":round((stamps[-1]-ref)/1e9,3),
               "silence_to_end_s":round((end-stamps[-1])/1e9,3),
               "longest_intermessage_gap_s":round(max(gaps,default=0),3),
               "median_intermessage_gap_s":round(statistics.median(gaps),3) if gaps else None,
               "first_60sec_count":sum(s-ref<60_000_000_000 for s in stamps),
               "last_60sec_count":sum(end-s<=60_000_000_000 for s in stamps),
               "count_by_30sec_bucket":bins}
        report["per_symbol"][sym]=d
    report["verdict"]="OFFLINE_SOURCE_GAP_DIAGNOSIS_COMPLETE_NOT_AN_EDGE"
    return report
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    try:
        r=audit()
    except Exception as exc:
        r={"study":"E10M_XVENUE_PRICE_STREAM_GAP_AUDIT_V02A",
           "verdict":"SOURCE_AUDIT_BLOCKED","error":type(exc).__name__+":"+str(exc)[:160],
           "forward_10min_outcomes_opened":0,"trade_actions":0}
    (ROOT/"receipt.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,indent=2,sort_keys=True),flush=True)
    if r["verdict"]=="SOURCE_AUDIT_BLOCKED":raise SystemExit(2)
if __name__=="__main__":main()

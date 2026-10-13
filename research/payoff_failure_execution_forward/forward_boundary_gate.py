#!/usr/bin/env python3
"""Immutable after-boundary public-market forward shadow gate, never an order bot.

Only accepts complete consecutive hourly bars from 2026-10-14 00:00 UTC onward.
Does NOT use any sealed 2026 price observations for indicator warmup.
Needs 200 hours of freshly collected warmup. External collector NOT included.
"""
import argparse,datetime as dt,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"payoff_40_10_btc_001"))
import engine
BOUNDARY=int(dt.datetime(2026,10,14,tzinfo=dt.timezone.utc).timestamp()*1000)
H=engine.HOUR
WARMUP=200*H

def validate(s):
    if s.get("status")!="SOURCE_OK" or s.get("authority")!="PUBLIC_READ_ONLY_SHADOW":
        raise ValueError("SOURCE_AUTHORITY_MISSING")
    if s.get("forward_boundary_utc")!="2026-10-14T00:00:00Z":
        raise ValueError("FORWARD_BOUNDARY_MISMATCH")
    b=s.get("bars",[])
    if not b or int(b[0]["t"])!=BOUNDARY:
        raise ValueError("SEALED_PREBOUNDARY_DATA_FORBIDDEN")
    if len(b)<202:
        raise ValueError("POST_BOUNDARY_200H_WARMUP_INSUFFICIENT")
    times=[int(x["t"]) for x in b]
    if any(t<BOUNDARY or t%H!=0 for t in times) or any(y-x!=H for x,y in zip(times,times[1:])):
        raise ValueError("HOURLY_GAP_OR_ILLEGAL_TIME")
    end=times[-1]
    if int(s.get("verified_complete_through_ms",0))<end+H:
        raise ValueError("LAST_BAR_NOT_CONFIRMED_CLOSED")
    if int(s.get("funding_verified_through_ms",0))<end+H:
        raise ValueError("FUNDING_COVERAGE_NOT_VERIFIED")
    marks={int(k):v for k,v in s.get("marks",{}).items()}
    if any(t not in marks for t in times):
        raise ValueError("MARK_COVERAGE_INCOMPLETE")
    funds={int(k):float(v) for k,v in s.get("funding",{}).items()}
    if any(t<BOUNDARY or t>end+H for t in funds):
        raise ValueError("FUNDING_TIME_OUT_OF_SCOPE")
    engine.check_bars(b,BOUNDARY+WARMUP,end)
    return b,marks,funds,end

def run(s):
    b,marks,funds,end=validate(s)
    begin=BOUNDARY+WARMUP
    if end<=begin:raise ValueError("NO_POST_WARMUP_COMPLETED_BAR")
    out={"science":"FUTURE_SHADOW_ONLY_NOT_REAL_EXECUTION",
         "boundary_utc":"2026-10-14T00:00:00Z",
         "warmup_observed_hours":WARMUP//H,
         "no_2026_preboundary_data":True,
         "last_closed_open_timestamp_ms":end,"trading_authority":"NONE",
         "source_semantics":"PUBLIC_OBSERVATIONAL_WITH_PROVENANCE_RECEIPTS",
         "results":{}}
    for scen,(fee,slip) in engine.CONFIGS.items():
        out["results"][scen]={
            mode:engine.replay(b,funds,marks,mode,fee,slip,begin=begin,end=end)
            for mode in ("PARENT","PAYOFF")}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    s=json.loads(a.source.read_text())
    o=run(s)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"science":o["science"],"trading_authority":"NONE",
                      "closed":{sc:{m:v["trades_closed"] for m,v in modes.items()}
                                for sc,modes in o["results"].items()}},sort_keys=True))
if __name__=="__main__":main()

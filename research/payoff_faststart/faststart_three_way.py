"""Alternative FAST-START 3-way shadow gate. Research only. No orders.
Pre-boundary completed candles are INDICATOR-ONLY, no economic events.
The sealed 2026 holdout remains inaccessible. Unverified sources fail closed.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"payoff_40_10_btc_001"),str(ROOT/"payoff_funding_netstop_001")]
import engine
from forward_child_replay import replay_forward_child

BOUNDARY=1791936000000
H=engine.HOUR
PARENT_SHA="673d50b2f786e88c593a900db1a9aac6a265d215"

def digest(b):
    return hashlib.sha256(json.dumps(b,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def validate(s):
    if s.get("status")!="SOURCE_OK" or s.get("trading_authority")!="NONE":
        raise ValueError("UNVERIFIED_SOURCE_OR_TRADING_AUTHORITY")
    if s.get("parent_v02_freeze_sha")!=PARENT_SHA or not s.get("parent_v02_source_receipt_sha256"):
        raise ValueError("PARENT_SOURCE_AUTHORITY_UNVERIFIED")
    if s.get("science_boundary_ms")!=BOUNDARY:
        raise ValueError("SCIENCE_BOUNDARY_CHANGED")
    b=s.get("bars")
    if not isinstance(b,list) or len(b)<202:
        raise ValueError("INSUFFICIENT_WARMUP_OR_FUTURE_BARS")
    times=[int(x["t"]) for x in b]
    if times[0]!=BOUNDARY-200*H or times[200]!=BOUNDARY:
        raise ValueError("WARMUP_NOT_IMMEDIATELY_BEFORE_BOUNDARY")
    if any(u%H or v-u!=H for u,v in zip(times,times[1:])):
        raise ValueError("UNVERIFIED_HOURLY_CONTIGUITY")
    if digest(b[:200])!=s.get("warmup_sha256"):
        raise ValueError("WARMUP_DATA_DIGEST_MISMATCH")
    if s.get("verified_complete_through_ms",0)<times[-1]+H:
        raise ValueError("LATEST_BAR_NOT_CLOSED")
    if s.get("funding_verified_through_ms",0)<times[-1]+H:
        raise ValueError("FUNDING_SOURCE_UNVERIFIED")
    m={int(k):v for k,v in s.get("marks",{}).items()}
    if any(t not in m for t in times[200:]):
        raise ValueError("MARK_PRICE_MISSING")
    f={int(k):float(v) for k,v in s.get("funding",{}).items()}
    if any(t<BOUNDARY or t>times[-1]+H for t in f):
        raise ValueError("PRE_BOUNDARY_FUNDING_FORBIDDEN")
    engine.check_bars(b,BOUNDARY,times[-1])
    return b,m,f,times[-1]

def compare(s):
    b,m,f,end=validate(s)
    out={"classification":"FAST_START_FORWARD_RESEARCH_NO_LIVE_GO",
         "science_begin_ms":BOUNDARY,
         "warmup_hours_before_boundary":200,
         "economic_events_before_boundary":0,
         "source_provenance_status":"SELF_ATTESTED_REQUIRES_INDEPENDENT_RECEIPT_CHECK",
         "trading_authority":"NONE","scenarios":{}}
    for scen,(fee,slip) in engine.CONFIGS.items():
        out["scenarios"][scen]={
            "PARENT":engine.replay(b,f,m,"PARENT",fee,slip,begin=BOUNDARY,end=end),
            "PAYOFF_4R":engine.replay(b,f,m,"PAYOFF",fee,slip,begin=BOUNDARY,end=end),
            "NETSTOP_CHILD":replay_forward_child(b,f,m,fee,slip,begin=BOUNDARY,end=end)}
    return out

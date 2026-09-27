#!/usr/bin/env python3
"""Aggregate LICP-001 outcome-blind calibration shards into a freezer-compatible receipt."""
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from research.liquidation_cascade.licp001_feature_calibration_v01 import burst_report, cross_venue

def parse_end(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def canonical_event(raw):
    venue=raw["venue"]
    if venue=="BYBIT":
        side=raw["liquidated_side"]
        pressure="SELL" if side=="Buy" else ("BUY" if side=="Sell" else None)
        source="bybit"
    elif venue=="BINANCE_SNAPSHOT":
        side=raw["liquidated_side"]
        pressure=side if side in ("BUY","SELL") else None
        source="binance"
    else:
        return None
    if pressure is None:return None
    return {
      "source":source,"symbol":raw["symbol"],"venue_ts":int(raw["exchange_ts_ms"]),
      "venue_side":side,"pressure":pressure,"notional":float(raw["notional_proxy"])
    }

def event_key(e):
    return (e["source"],e["symbol"],e["venue_ts"],e["venue_side"],round(e["notional"],8))

def sha_events(events):
    h=hashlib.sha256()
    for e in sorted(events,key=event_key):
        h.update((json.dumps(e,separators=(",",":"),sort_keys=True)+"\n").encode())
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",help="directory containing shard subdirectories with health.json/liquidations.jsonl")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    root=Path(a.root)
    health_files=sorted(root.rglob("health.json"))
    if not health_files: raise SystemExit("NO_SHARDS")

    starts=[]; ends=[]; scheduled=0.0
    conn={"bybit":0.0,"binance":0.0,"mexc":0.0}
    regressions=0; shards=[]; events_by_key={}
    for hp in health_files:
        h=json.loads(hp.read_text())
        if h.get("outcome_blind") is not True: raise SystemExit("NON_OUTCOME_BLIND_SHARD")
        if h.get("schema")!="licp001.health.v2": raise SystemExit("UNSUPPORTED_HEALTH_SCHEMA")
        shard_sched=float(h.get("scheduled_seconds",0))
        if shard_sched < 60: raise SystemExit("INVALID_SCHEDULED_SECONDS")
        hh=h.get("health",{})
        for v in ("bybit","binance","mexc"):
            if int(hh.get(v,{}).get("acks",0)) < 1: raise SystemExit("SOURCE_ACK_MISSING:"+v)
        if int(hh["mexc"].get("depth_updates",0)) < 1: raise SystemExit("MEXC_DEPTH_MISSING")
        if int(hh["bybit"].get("malformed",0)) or int(hh["binance"].get("malformed",0)):
            raise SystemExit("MALFORMED_LIQUIDATION_PAYLOAD")
        starts.append(int(h["started_wall_ms"])); ends.append(parse_end(h["ended_at"]))
        scheduled+=shard_sched
        for v in conn:
            vh=hh.get(v,{})
            conn[v]+=min(float(vh.get("connected_seconds",0)),shard_sched)
            regressions+=int(vh.get("clock_regressions",0))
        ep=hp.parent/"liquidations.jsonl"
        actual_event_sha=hashlib.sha256(ep.read_bytes() if ep.exists() else b"").hexdigest()
        if actual_event_sha != h.get("event_log_sha256"): raise SystemExit("EVENT_LOG_HASH_MISMATCH")
        gp=hp.parent/"gaps.jsonl"
        actual_gap_sha=hashlib.sha256(gp.read_bytes() if gp.exists() else b"").hexdigest()
        if actual_gap_sha != h.get("gaps_log_sha256"): raise SystemExit("GAPS_LOG_HASH_MISMATCH")
        count=0
        if ep.exists():
            for line in ep.read_text().splitlines():
                if not line.strip():continue
                e=canonical_event(json.loads(line))
                if e is None:continue
                events_by_key[event_key(e)]=e;count+=1
        shards.append({"path":str(hp.parent),"raw_events":count,"event_log_sha256":h.get("event_log_sha256")})

    events=list(events_by_key.values())
    bybit=[e for e in events if e["source"]=="bybit"]
    bybit_btc=[e for e in bybit if e["symbol"]=="BTCUSDT"]
    uptime={v:(min(100.0,conn[v]/scheduled*100.0) if scheduled else 0.0) for v in conn}
    span_days=(max(ends)-min(starts))/86400000.0
    eligibility={
      "span_days":span_days,
      "bybit_events":len(bybit),
      "bybit_btc_events":len(bybit_btc),
      "uptime_pct":min(uptime.values()),
      "uptime_by_source_pct":uptime,
      "clock_regressions":regressions,
      "raw_event_log_sha256":sha_events(events),
      "shard_count":len(health_files),
      "scheduled_seconds":scheduled,
    }
    ready=(span_days>=7 and len(bybit)>=250 and len(bybit_btc)>=50
           and eligibility["uptime_pct"]>=95 and regressions==0)
    result={
      "status":"LICP001_AGGREGATED_OUTCOME_BLIND_CALIBRATION",
      "decision":"CALIBRATION_SAMPLE",
      "eligibility":eligibility,
      "eligible_for_freeze":ready,
      "total_liquidation_events":len(events),
      "bursts":burst_report(events),
      "cross_venue_confirmation":cross_venue(events),
      "mexc_price_outcomes_opened":False,
      "shards":shards,
    }
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()

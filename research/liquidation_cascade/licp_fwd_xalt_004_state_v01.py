#!/usr/bin/env python3
"""Persistent, deterministic state helpers for LICP-FWD-XALT-004.

Operational hardening only. Frozen science is unchanged:
SELL/SHORT SOL_USDT, +60s entry delay, +60m exit, 16 bps taker hurdle.
"""
import hashlib, json, os, statistics, tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ENTRY_DELAY_MS=60_000
HORIZON_MS=3_600_000
STALE_MS=1_000
COOLDOWN_MS=120_000
FEE_BPS=16.0

def episode_id(pressure, bybit_burst, binance_burst):
    payload={
      "family":"FWD_XALT_004","pressure":pressure,
      "bybit_start_ms":int(bybit_burst["start_ms"]),
      "bybit_end_ms":int(bybit_burst["end_ms"]),
      "binance_start_ms":int(binance_burst["start_ms"]),
      "binance_end_ms":int(binance_burst["end_ms"]),
    }
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def short_metrics(entry_bid,exit_ask):
    entry=float(entry_bid);exit=float(exit_ask)
    if entry<=0 or exit<=0: raise ValueError("NONPOSITIVE_BBO")
    gross=(entry-exit)/entry*10_000.0
    return {"gross_bps":gross,"net_taker_bps":gross-FEE_BPS}

def fresh_non_crossed(bbo,now_mono_ns):
    if not bbo:return False
    if float(bbo["bid"])>=float(bbo["ask"]):return False
    age_ms=(int(now_mono_ns)-int(bbo["local_ns"]))/1e6
    return 0<=age_ms<=STALE_MS

def make_record(pressure,bybit_burst,binance_burst,event_wall_ms):
    eid=episode_id(pressure,bybit_burst,binance_burst)
    return {
      "schema":"licp_fwd_xalt_004.record.v1",
      "episode_id":eid,
      "family":"FWD_XALT_004",
      "pressure":pressure,
      "target":"SOL_USDT",
      "event_wall_ms":int(event_wall_ms),
      "entry_due_wall_ms":int(event_wall_ms)+ENTRY_DELAY_MS,
      "bybit_burst":bybit_burst,
      "binance_burst":binance_burst,
      "entry":None,"exit":None,
      "entry_missed_restart":False,"exit_missed_restart":False,
    }

def add_episode(records,record):
    if any(r["episode_id"]==record["episode_id"] for r in records):
        return False
    records.append(record);return True

def mark_restart_gaps(records,observer_start_wall_ms):
    changed=False
    for r in records:
        if r.get("exit") is not None:continue
        if r.get("entry") is None:
            if int(r["entry_due_wall_ms"]) < int(observer_start_wall_ms):
                if not r.get("entry_missed_restart"):
                    r["entry_missed_restart"]=True;changed=True
        else:
            due=int(r["entry"]["wall_ms"])+HORIZON_MS
            if due < int(observer_start_wall_ms):
                if not r.get("exit_missed_restart"):
                    r["exit_missed_restart"]=True;changed=True
    return changed

def apply_bbo(records,bbo,now_mono_ns):
    """Apply one current fresh BBO. Returns True iff durable state changed."""
    if not fresh_non_crossed(bbo,now_mono_ns):return False
    changed=False
    wall=int(bbo["wall_ms"])
    for r in records:
        if r.get("entry_missed_restart") or r.get("exit_missed_restart"):
            continue
        if r.get("entry") is None:
            if wall>=int(r["entry_due_wall_ms"]):
                r["entry"]={
                  "wall_ms":wall,"bid":float(bbo["bid"]),"ask":float(bbo["ask"]),
                  "entry_bid":float(bbo["bid"])
                }
                changed=True
            continue
        if r.get("exit") is None:
            exit_due=int(r["entry"]["wall_ms"])+HORIZON_MS
            if wall>=exit_due:
                m=short_metrics(r["entry"]["entry_bid"],bbo["ask"])
                r["exit"]={"wall_ms":wall,"bid":float(bbo["bid"]),"ask":float(bbo["ask"]),"exit_ask":float(bbo["ask"])}
                r.update(m);changed=True
    return changed

def load_records(path):
    p=Path(path)
    if not p.exists():return []
    j=json.loads(p.read_text())
    if j.get("schema")!="licp_fwd_xalt_004.state.v1":raise ValueError("BAD_STATE_SCHEMA")
    rows=j.get("records")
    if not isinstance(rows,list):raise ValueError("BAD_STATE_RECORDS")
    ids=[r.get("episode_id") for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError("DUPLICATE_EPISODE_ID")
    return rows

def save_records(path,records):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps({"schema":"licp_fwd_xalt_004.state.v1","records":records},indent=2,sort_keys=True)+"\n"
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=p.parent,delete=False) as f:
        f.write(data);f.flush();os.fsync(f.fileno());tmp=f.name
    os.replace(tmp,p)

def state_sha256(path):
    p=Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else hashlib.sha256(b"").hexdigest()

def evaluate_forward(records,now_wall_ms):
    matured=[]
    for r in records:
        maturity=int(r["entry_due_wall_ms"])+HORIZON_MS
        if int(now_wall_ms)>=maturity:matured.append(r)
    missing=[r for r in matured if r.get("exit") is None]
    complete=[r for r in matured if r.get("exit") is not None and "net_taker_bps" in r]
    dates=defaultdict(list)
    for r in complete:
        d=datetime.fromtimestamp(int(r["event_wall_ms"])/1000,tz=timezone.utc).date().isoformat()
        dates[d].append(float(r["gross_bps"]))
    missing_rate=(len(missing)/len(matured)) if matured else 0.0
    result={
      "matured_episodes":len(matured),"completed_episodes":len(complete),
      "missing_or_unresolved":len(missing),"missing_rate":missing_rate,
      "distinct_utc_dates":len(dates),"decision":"FORWARD_INSUFFICIENT"
    }
    if complete:
        result["mean_net_taker_bps"]=statistics.fmean(float(r["net_taker_bps"]) for r in complete)
        result["median_gross_bps"]=statistics.median(float(r["gross_bps"]) for r in complete)
        result["by_date_mean_gross_bps"]={d:statistics.fmean(xs) for d,xs in sorted(dates.items())}
    enough=(len(matured)>=20 and len(dates)>=3 and missing_rate<=0.10 and len(complete)>=20)
    if enough:
        positive_dates=sum(v>0 for v in result["by_date_mean_gross_bps"].values())
        survives=(result["mean_net_taker_bps"]>0 and result["median_gross_bps"]>0 and positive_dates>=2)
        result["positive_mean_dates"]=positive_dates
        result["decision"]="FORWARD_TRANSFER_SURVIVES" if survives else "FORWARD_TRANSFER_FAIL"
    return result

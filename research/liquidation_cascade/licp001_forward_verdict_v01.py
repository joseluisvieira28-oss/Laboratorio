#!/usr/bin/env python3
"""Deterministic LICP-001 forward verdict aggregator.

Implements LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md.
No exchange access. No threshold selection. No horizon/target rescue.
"""
import argparse, json, statistics
from datetime import datetime, timezone
from pathlib import Path

PRIMARY_FAMILY="BTC_CONFIRMED"
PRIMARY_TARGET="BTC_USDT"
PRIMARY_HORIZON="60000"
MIN_EPISODES=20
MIN_DATES=3
MIN_COVERAGE=0.90
COOLDOWN_MS=120_000
BASE_RT_BPS=16.0
STRESS_RT_BPS=32.0


def ignition_ts_ms(rec):
    try:
        return int(rec["meta"]["ignition"]["ignition_venue_ts"])
    except Exception:
        raise ValueError("MISSING_IGNITION_TIMESTAMP")


def load_receipts(root):
    root=Path(root)
    files=[root] if root.is_file() else sorted(root.rglob("*.json"))
    out=[]
    for p in files:
        try:
            j=json.loads(p.read_text())
        except Exception:
            continue
        if j.get("status")!="FORWARD_OBSERVATION":
            continue
        if j.get("live_trading") is not False:
            raise ValueError("LIVE_TRADING_RECEIPT_REJECTED")
        out.append((str(p),j))
    if not out:
        raise ValueError("NO_FORWARD_RECEIPTS")
    return out


def canonical_episodes(receipts):
    rows=[]
    for src,j in receipts:
        for rec in j.get("records",[]):
            if rec.get("family")!=PRIMARY_FAMILY:
                continue
            ts=ignition_ts_ms(rec)
            rows.append((ts,src,rec))
    rows.sort(key=lambda x:x[0])

    kept=[]
    last_ts=None
    for ts,src,rec in rows:
        if last_ts is not None and ts-last_ts<COOLDOWN_MS:
            continue
        kept.append((ts,src,rec))
        last_ts=ts
    return kept


def utc_date(ts_ms):
    return datetime.fromtimestamp(ts_ms/1000.0,tz=timezone.utc).date().isoformat()


def primary_result(rec):
    t=rec.get("targets",{}).get(PRIMARY_TARGET)
    if not isinstance(t,dict):
        return None
    o=t.get("outcomes",{}).get(PRIMARY_HORIZON)
    if not isinstance(o,dict):
        return None
    gross=o.get("taker_gross_bps")
    base=o.get("mexc_taker_net_bps")
    if gross is None or base is None:
        return None
    gross=float(gross);base=float(base)
    return {
      "taker_gross_bps":gross,
      "base_net_bps":base,
      "stress_2x_net_bps":gross-STRESS_RT_BPS,
    }


def verdict(receipts):
    episodes=canonical_episodes(receipts)
    first20=episodes[:MIN_EPISODES]
    dates=sorted({utc_date(ts) for ts,_,_ in first20})

    if len(first20)<MIN_EPISODES or len(dates)<MIN_DATES:
        return {
          "state":"FORWARD_INSUFFICIENT",
          "independent_episodes":len(episodes),
          "first20_count":len(first20),
          "distinct_utc_dates_first20":dates,
          "minimum_episodes":MIN_EPISODES,
          "minimum_dates":MIN_DATES,
        }

    primary=[]
    episode_rows=[]
    for ts,src,rec in first20:
        pr=primary_result(rec)
        episode_rows.append({
          "ignition_ts_ms":ts,
          "utc_date":utc_date(ts),
          "source_receipt":src,
          "pressure":rec.get("pressure"),
          "primary_complete":pr is not None,
          "primary":pr,
        })
        if pr is not None:
            primary.append(pr)

    coverage=len(primary)/MIN_EPISODES
    if coverage<MIN_COVERAGE:
        return {
          "state":"BLOCKED_DATA_QUALITY",
          "first20_count":MIN_EPISODES,
          "valid_primary_outcomes":len(primary),
          "coverage":coverage,
          "required_coverage":MIN_COVERAGE,
          "distinct_utc_dates_first20":dates,
          "episodes":episode_rows,
        }

    base=[x["base_net_bps"] for x in primary]
    stress=[x["stress_2x_net_bps"] for x in primary]
    mean_base=statistics.fmean(base)
    median_base=statistics.median(base)
    mean_stress=statistics.fmean(stress)
    positive_fraction=sum(x>0 for x in base)/len(base)

    survives=(mean_base>0 and median_base>0 and mean_stress>0)
    return {
      "state":"SURVIVES_FORWARD_CANDIDATE" if survives else "NO_EDGE",
      "first20_count":MIN_EPISODES,
      "valid_primary_outcomes":len(primary),
      "coverage":coverage,
      "distinct_utc_dates_first20":dates,
      "primary_family":PRIMARY_FAMILY,
      "primary_target":PRIMARY_TARGET,
      "primary_horizon_ms":int(PRIMARY_HORIZON),
      "base_round_trip_bps":BASE_RT_BPS,
      "stress_round_trip_bps":STRESS_RT_BPS,
      "mean_base_net_bps":mean_base,
      "median_base_net_bps":median_base,
      "mean_stress_2x_net_bps":mean_stress,
      "positive_base_fraction":positive_fraction,
      "episodes":episode_rows,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",help="Receipt JSON file or directory tree")
    ap.add_argument("--out")
    a=ap.parse_args()
    receipts=load_receipts(a.root)
    result=verdict(receipts)
    result["schema"]="licp001.forward_verdict.v1"
    result["receipt_count"]=len(receipts)
    txt=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.out:
        Path(a.out).write_text(txt)
    print(txt,end="")

if __name__=="__main__":
    main()

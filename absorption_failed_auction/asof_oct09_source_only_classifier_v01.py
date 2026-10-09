#!/usr/bin/env python3
"""Outcome-blind Oct09 as-of source-join / frozen event classifier recovery probe.

Read only immutable MM-V1 receipts and canonical Binance spot aggTrades.
Reuses original frozen engine.classify unmodified. No future-return resolution.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import engine
import collector

BAR_MS=300_000
ASOF_END_MS=1791543600000 # Oct09 11:00 UTC frozen snapshot
START_MS=1790933100000 # Oct02 09:25 UTC
OCT09_START_MS=1791504000000
BASELINE=2016
SOURCE_FEATURE_SHA="18750b490331240511bdb352080ce2b1bc30d2e441e4c23b1843109905803180"
FROZEN_BOUNDARY_MS=1790860200000

def archive_feature_map(path):
    src=Path(path)
    if hashlib.sha256(src.read_bytes()).hexdigest()!=SOURCE_FEATURE_SHA:
        raise ValueError("PREVIOUS_SOURCE_ARTIFACT_SHA256_MISMATCH")
    result={}
    for line in src.read_text().splitlines():
        v=json.loads(line)
        t=int(v["bar_close_ms"])
        if t in result: raise ValueError("SOURCE_DUPLICATE_BAR")
        if float(v["agg_base_volume"])<=0: raise ValueError("SOURCE_ZERO_VOLUME")
        result[t]={"agg_base_volume":float(v["agg_base_volume"]),
                   "agg_delta":float(v["aggressive_buy_qty"])-float(v["aggressive_sell_qty"]),
                   "agg_delta_pct":float(v["agg_delta_pct"])}
    if len(result)!=2016:
        raise ValueError("EXPECTED_2016_DAILY_BINS_02_TO_08")
    return result

def load_sensor(vault_root):
    root=Path(vault_root)
    rows=[]
    for n in range(2,9):
        day=f"2026-10-{n:02d}"
        path=root/"archive"/day/f"{day}.jsonl"
        manifest=json.loads((root/"archive"/day/f"{day}.manifest.json").read_text())
        content=path.read_bytes()
        if hashlib.sha256(content).hexdigest()!=manifest["corpus_sha256"]:
            raise ValueError("VAULT_DAY_SHA256_MISMATCH_"+day)
        for line in content.decode("utf-8").splitlines():
            obj=json.loads(line);payload=obj["payload"]
            if obj["payload_sha256"] != __import__("hashlib").sha256(
                json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest():
                raise ValueError("VAULT_PAYLOAD_SHA256_MISMATCH")
            rows.append(payload)
    path=root/"recovery"/"2026-10-09_ASOF_1100UTC_RAW_TVFP_RECEIPTS.jsonl"
    for line in path.read_text().splitlines():
        raw=json.loads(line)
        p=raw["payload"]
        if raw.get("trading_authority")!="NONE" or raw.get("record_type")!="TVFP_RECEIPT" or p.get("sensor_version")!="MM-V1" or p.get("symbol")!="BINANCE:BTCUSDT":
            raise ValueError("UNAUTHORIZED_ASOF_SENSOR")
        digest=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()
        if digest!=raw.get("payload_sha256"):
            raise ValueError("ASOF_PAYLOAD_SHA256_MISMATCH")
        rows.append(p)
    rows.sort(key=lambda r:r["bar_close_ms"])
    closes=[r["bar_close_ms"] for r in rows]
    if (len(rows)!=2036 or closes[0]!=START_MS or closes[-1]!=ASOF_END_MS
        or any(y-x!=BAR_MS for x,y in zip(closes,closes[1:]))):
        raise ValueError("RECOVERED_2036_CONTIGUITY_MISMATCH")
    return rows

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--source-feature-file",required=True)
    cli.add_argument("--vault-root",required=True)
    cli.add_argument("--outdir",required=True)
    p=cli.parse_args()
    out=Path(p.outdir);out.mkdir(parents=True,exist_ok=True)
    source=archive_feature_map(p.source_feature_file)
    sensor=load_sensor(p.vault_root)
    # Public only, strictly before/as-of immutable snapshot. Source/current bar fields, not future returns.
    recent,api_meta=collector.fetch_post_terminal_flow(OCT09_START_MS,ASOF_END_MS)
    if not recent or api_meta["requests"]>1200:
        raise ValueError("RECENT_BINANCE_SPOT_SOURCE_MISSING_OR_UNBOUNDED")
    for opened,b in recent.items():
        t=opened+BAR_MS
        if not OCT09_START_MS<t<=ASOF_END_MS:
            raise ValueError("UNAUTHORIZED_CURRENT_SOURCE_TIMESTAMP")
        if t in source:
            raise ValueError("ARCHIVE_CURRENT_SOURCE_OVERLAP")
        source[t]={"agg_base_volume":float(b["agg_base_volume"]),
                   "agg_delta":float(b["agg_delta"]),"agg_delta_pct":float(b["agg_delta_pct"])}
    joined=[]
    for p in sensor:
        t=p["bar_close_ms"]
        if t not in source:
            raise ValueError("BINANCE_CANONICAL_FLOW_MISSING_FOR_AUTHENTIC_SENSOR_"+str(t))
        row={k:p[k] for k in collector.REQUIRED_SENSOR}
        row.update(source[t])
        joined.append(row)
    if len(joined)!=2036:
        raise ValueError("SOURCE_JOIN_ROW_MISMATCH")
    classified=engine.classify(joined,FROZEN_BOUNDARY_MS)
    candidates=[x for x in classified if x["event_class"]!="WARMUP"]
    if len(candidates)!=20:
        raise ValueError("EXPECTED_20_POST_BASELINE_CANDIDATES")
    if any(any(str(k).startswith("R") and str(k)[1:].isdigit() for k in r) for r in classified):
        raise ValueError("OUTCOME_LEAK")
    counts=dict(sorted(Counter(x["event_class"] for x in candidates).items()))
    safe_events=[{"bar_close_ms":r["bar_close_ms"],"event_class":r["event_class"],
                  "direction":r.get("direction",0)} for r in candidates]
    receipt={
        "lab_id":"ABSORPTION-FAILED-AUCTION-001",
        "state":"SOURCE_JOIN_AND_FROZEN_CLASSIFIER_REPLAY_ONLY",
        "asof_utc":"2026-10-09T11:00:00Z",
        "parent_classification":"PASS_STRONG",
        "source":"canonical Binance spot aggTrades, verified 2026-10-02..08 daily ZIPs plus bounded Oct09 public REST",
        "canonical_daily_features_sha256":SOURCE_FEATURE_SHA,
        "source_daily_archives_sha256_verified_in_run":37922287209,
        "sensor_receipts_2036_sha256_verified_in_run":37921551326,
        "authentic_source_matched_candles":len(joined),
        "prior_consecutive_history_bars":BASELINE,
        "post_baseline_candidate_bars":len(candidates),
        "candidate_counts":counts,
        "outcome_blind_event_markers":safe_events,
        "public_binance_api_requests":api_meta["requests"],
        "public_binance_recent_aggtrade_rows":api_meta["aggtrade_rows"],
        "trading_authority":"NONE",
        "economic_outcomes_unlocked":False,
        "economic_verdict_authorized":False,
        "formal_canonical_forward_ledger_modified":False,
        "method_note":"Source-only retrospective reconstruction from originally prospective received MM-V1 telemetry. Frozen classification unmodified; new scientific credit requires independent acceptance of provenance/coverage and ledger authority. NOT a live-trading signal or evidence of profits."
    }
    (out/"SOURCE_ONLY_ASOF_2026-10-09_FROZEN_CLASSIFIER_RECEIPT.json").write_text(
        json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in receipt.items() if k!="outcome_blind_event_markers"},sort_keys=True,indent=2))
if __name__=="__main__":
    main()

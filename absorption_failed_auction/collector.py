#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import engine

BAR_MS = 300000
TERMINAL_END_MS = 1790858100000
PARENT_ARTIFACT_ID = 11163421403
API_BASES = [
    "https://data-api.binance.vision/api/v3/aggTrades",
    "https://api.binance.com/api/v3/aggTrades",
]

REQUIRED_SENSOR = (
    "bar_open_ms","bar_close_ms","ltf_path_efficiency","bar_return_bps",
    "poc_migration_bps","poc_mid","vah","val","buy_imbalance_rows",
    "sell_imbalance_rows","footprint_rows","ltf_intrabars"
)


class CollectorError(RuntimeError):
    pass


def _sha_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_ms(v) -> int:
    x=int(v)
    ax=abs(x)
    if ax < 10**11: return x*1000
    if ax < 10**14: return x
    if ax < 10**17: return x//1000
    return x//1_000_000


def _api(params):
    last=None
    for base in API_BASES:
        url=base+"?"+urllib.parse.urlencode(params)
        for attempt in range(4):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Absorption/0.1"})
                with urllib.request.urlopen(req,timeout=45) as r:
                    obj=json.loads(r.read())
                if not isinstance(obj,list):
                    raise CollectorError(f"unexpected API object: {obj}")
                return obj,base
            except Exception as exc:
                last=exc
                time.sleep(min(2**attempt,8))
    raise CollectorError(f"official Binance public API unavailable: {last}")


def fetch_post_terminal_flow(start_ms:int,end_ms:int):
    """Fetch canonical aggTrades over [start_ms,end_ms), aggregate to UTC 5m."""
    if end_ms <= start_ms:
        return {},{"requests":0,"aggtrade_rows":0,"api_bases_used":[]}
    trades={}
    requests=0
    bases=set()
    hour=start_ms
    while hour<end_ms:
        seg_end=min(hour+3600_000,end_ms)
        batch,base=_api({"symbol":"BTCUSDT","startTime":hour,"endTime":seg_end-1,"limit":1000})
        requests+=1;bases.add(base)
        for x in batch:
            t=_to_ms(x["T"])
            if hour<=t<seg_end: trades[int(x["a"])]=x
        while len(batch)==1000:
            last_id=int(batch[-1]["a"])
            batch,base=_api({"symbol":"BTCUSDT","fromId":last_id+1,"limit":1000})
            requests+=1;bases.add(base)
            if not batch: break
            crossed=False
            for x in batch:
                t=_to_ms(x["T"])
                if t>=seg_end:
                    crossed=True
                    continue
                if t>=hour: trades[int(x["a"])]=x
            if crossed: break
        hour=seg_end

    buckets=defaultdict(lambda:{"agg_base_volume":0.0,"agg_buy_volume":0.0,"agg_sell_volume":0.0,"agg_trade_count":0})
    for aid in sorted(trades):
        x=trades[aid]
        t=_to_ms(x["T"])
        if not (start_ms<=t<end_ms): continue
        bo=(t//BAR_MS)*BAR_MS
        q=float(x["q"])
        b=buckets[bo]
        b["agg_base_volume"]+=q
        if bool(x["m"]): b["agg_sell_volume"]+=q
        else: b["agg_buy_volume"]+=q
        b["agg_trade_count"]+=1

    out={}
    for bo,b in buckets.items():
        delta=b["agg_buy_volume"]-b["agg_sell_volume"]
        out[bo]={**b,"agg_delta":delta,"agg_delta_pct":delta/b["agg_base_volume"] if b["agg_base_volume"] else math.nan}

    return out,{"requests":requests,"aggtrade_rows":len(trades),"api_bases_used":sorted(bases)}


def _payload_to_structure(p):
    if p.get("lab_id")!="TV-FOOTPRINT-CALIBRATION-001" or p.get("sensor_version")!="MM-V1":
        raise CollectorError("TV sensor identity mismatch")
    if p.get("symbol")!="BINANCE:BTCUSDT" or str(p.get("timeframe"))!="5":
        raise CollectorError("TV market identity mismatch")
    row={k:p.get(k) for k in REQUIRED_SENSOR}
    for k in REQUIRED_SENSOR:
        if row[k] is None:
            raise CollectorError(f"missing/null required sensor field {k} at {p.get('bar_close_ms')}")
    row["bar_open_ms"]=int(row["bar_open_ms"])
    row["bar_close_ms"]=int(row["bar_close_ms"])
    return row


def load_sensor(vault_paths,current_path):
    by={}
    def add_obj(obj,source):
        p=obj.get("payload") if isinstance(obj,dict) else None
        if not isinstance(p,dict): return
        row=_payload_to_structure(p)
        bo=row["bar_open_ms"]
        sig=json.dumps(row,sort_keys=True,separators=(",",":"))
        if bo in by and by[bo][1]!=sig:
            raise CollectorError(f"conflicting structural receipt {bo}")
        by[bo]=(row,sig,source)

    for path in vault_paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip(): add_obj(json.loads(line),str(path))

    current_path=Path(current_path)
    if current_path.suffix.lower()==".csv":
        with current_path.open(newline="",encoding="utf-8") as fh:
            for raw in csv.DictReader(fh):
                row={}
                for k in REQUIRED_SENSOR:
                    if k not in raw or raw[k] in (None,""):
                        raise CollectorError(f"current intake missing {k}")
                    if k in ("bar_open_ms","bar_close_ms","buy_imbalance_rows","sell_imbalance_rows","footprint_rows","ltf_intrabars"):
                        row[k]=int(raw[k])
                    else:
                        row[k]=float(raw[k])
                bo=row["bar_open_ms"]
                sig=json.dumps(row,sort_keys=True,separators=(",",":"))
                if bo in by and by[bo][1]!=sig:
                    raise CollectorError(f"conflicting structural intake {bo}")
                by[bo]=(row,sig,str(current_path))
    else:
        for line in current_path.read_text(encoding="utf-8").splitlines():
            if line.strip(): add_obj(json.loads(line),str(current_path))

    rows=[v[0] for k,v in sorted(by.items())]
    for a,b in zip(rows,rows[1:]):
        if b["bar_open_ms"]-a["bar_open_ms"]!=BAR_MS:
            raise CollectorError(f"sensor continuity gap {a['bar_open_ms']}->{b['bar_open_ms']}")
    return rows


def load_terminal_flow(path):
    out={}
    with Path(path).open(newline="",encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r.get("agg_base_volume") or not r.get("agg_delta"):
                raise CollectorError("terminal comparison contains unmatched Binance bar")
            bo=int(r["bar_open_ms"])
            base=float(r["agg_base_volume"])
            delta=float(r["agg_delta"])
            out[bo]={"agg_base_volume":base,"agg_delta":delta,"agg_delta_pct":delta/base}
    if len(out)!=2016:
        raise CollectorError(f"terminal flow map expected 2016 got {len(out)}")
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vault",nargs="+",required=True)
    ap.add_argument("--current",required=True)
    ap.add_argument("--terminal-comparison",required=True)
    ap.add_argument("--authority",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()

    authority=json.loads(Path(args.authority).read_text())
    if authority["parent_classification"]!="PASS_STRONG":
        raise CollectorError("parent is not PASS_STRONG")
    if authority["event_collection_open"] is not True:
        raise CollectorError("event collection not open")
    if authority["economic_outcomes_unlocked"] is not False:
        raise CollectorError("economic outcomes unexpectedly unlocked")
    boundary=int(authority["event_open_boundary_ms"])

    sensor=load_sensor([Path(x) for x in args.vault],Path(args.current))
    terminal=load_terminal_flow(Path(args.terminal_comparison))
    latest_close=max(r["bar_close_ms"] for r in sensor)

    post,api_meta=fetch_post_terminal_flow(TERMINAL_END_MS,latest_close)
    flow={**terminal,**post}

    merged=[]
    for s in sensor:
        bo=s["bar_open_ms"]
        if bo not in flow:
            raise CollectorError(f"canonical Binance flow missing for bar {bo}")
        f=flow[bo]
        row={**s,
             "agg_base_volume":f["agg_base_volume"],
             "agg_delta":f["agg_delta"],
             "agg_delta_pct":f["agg_delta_pct"]}
        merged.append(row)

    if len(merged)<engine.BASELINE:
        raise CollectorError("insufficient causal baseline")

    classified=engine.classify(merged,boundary)
    forward=[r for r in classified if r["bar_close_ms"]>=boundary]

    forbidden=[]
    for r in forward:
        for k in r:
            if str(k).startswith("R") and str(k)[1:].isdigit():
                forbidden.append(k)
    if forbidden:
        raise CollectorError(f"outcome leakage fields detected: {sorted(set(forbidden))}")

    outdir=Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    ledger=outdir/"EVENT_LEDGER.jsonl"
    keep=[
        "bar_open_ms","bar_close_ms","event_class","direction",
        "agg_delta_pct","agg_base_volume","ltf_path_efficiency",
        "bar_return_bps","poc_migration_bps",
        "q95_abs_delta_pct","q75_agg_base_volume",
        "q25_path_efficiency","q75_path_efficiency",
        "q25_abs_bar_return_bps","suppressed_candidate"
    ]
    with ledger.open("w",encoding="utf-8") as fh:
        for r in forward:
            obj={k:r[k] for k in keep if k in r}
            obj["utc_date"]=datetime.fromtimestamp(r["bar_close_ms"]/1000,tz=timezone.utc).date().isoformat()
            obj["economic_outcomes_unlocked"]=False
            obj["trading_authority"]="NONE"
            fh.write(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n")

    counts=defaultdict(int)
    for r in forward: counts[r["event_class"]]+=1
    state={
        "lab_id":engine.LAB_ID,
        "parent_classification":"PASS_STRONG",
        "event_open_boundary_ms":boundary,
        "processed_through_bar_close_ms":latest_close,
        "forward_bars_classified":len(forward),
        "event_class_counts":dict(sorted(counts.items())),
        "failed_auction_events":counts["FAILED_AUCTION"],
        "efficient_acceptance_events":counts["EFFICIENT_ACCEPTANCE"],
        "distinct_utc_dates":len({datetime.fromtimestamp(r["bar_close_ms"]/1000,tz=timezone.utc).date().isoformat() for r in forward}),
        "economic_outcomes_unlocked":False,
        "outcome_fields_present":False,
        "trading_authority":"NONE",
        "binance_post_terminal_source":api_meta,
        "current_intake_sha256":_sha_file(Path(args.current)),
        "terminal_comparison_sha256":_sha_file(Path(args.terminal_comparison)),
    }
    (outdir/"COLLECTOR_STATE.json").write_text(json.dumps(state,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    receipt={
        "classification":"FORWARD_EVENT_COLLECTION_ACTIVE",
        "state":state,
        "ledger_sha256":_sha_file(ledger),
        "authority_commit":authority.get("parent_receipt_commit"),
        "economic_outcomes_unlocked":False,
        "trading_authority":"NONE"
    }
    (outdir/"COLLECTOR_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))


if __name__=="__main__":
    main()

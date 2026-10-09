#!/usr/bin/env python3
"""Source-only price-level 5-minute source integrity and shape census.
YT-AXIA-VAP-001. No future returns, executions, or orders.
Numeric shape criteria frozen in YT_AXIA_VAP_001_SOURCE_CENSUS_FREEZE.json.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
from urllib.request import Request,urlopen
import zipfile

HERE=Path(__file__).resolve().parent
FREEZE=HERE/"YT_AXIA_VAP_001_SOURCE_CENSUS_FREEZE.json"
RECEIPT=HERE/"YT_AXIA_VAP_001_SOURCE_CENSUS_RECEIPT.json"
STEP=300000
PREFIX="https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
class Blocked(Exception):pass

def price_to_cents(value):
    parts=value.strip().split(".")
    if len(parts)>2 or not parts[0].isdigit() or len(parts)!=2 or not parts[1].isdigit():
        raise Blocked("PRICE_FORMAT")
    if any(c!="0" for c in parts[1][2:]):
        raise Blocked("PRICE_MORE_PRECISE_THAN_CENT")
    cents=int(parts[0])*100+int((parts[1]+"00")[:2])
    if cents<=0:raise Blocked("PRICE_NONPOSITIVE")
    return cents

def bounded_ms(value):
    v=int(value)
    if not 10**12<=v<10**13:raise Blocked("TIMESTAMP_EXPECTED_MS_2022_2024")
    return v

def price_bucket(price_cents,anchor_cents):
    if anchor_cents<=0:raise Blocked("BAD_ANCHOR")
    return ((price_cents-anchor_cents)*10000)//anchor_cents

def local_peaks(bins):
    if not bins:return []
    return [k for k,v in sorted(bins.items()) if
            v>0 and v>bins.get(k-1,0) and v>bins.get(k+1,0)]

def qualifies_shape(bins,trades,min_bins=8,min_trades=100,min_share=.08,separation=3,valley_ratio=.35):
    if trades<min_trades or len(bins)<min_bins:return False
    total=sum(bins.values())
    if total<=0:raise Blocked("ZERO_VOLUME_BAR")
    peaks=[k for k in local_peaks(bins) if bins[k]>=min_share*total]
    for i,p in enumerate(peaks):
        for q in peaks[i+1:]:
            if q-p<separation:continue
            low=min(bins.get(b,0.0) for b in range(p+1,q))
            if low <= valley_ratio*min(bins[p],bins[q]):
                return True
    return False

def load_freeze():
    f=json.loads(FREEZE.read_text())
    if (f["lab_id"]!="YT-AXIA-VAP-001" or
        f["status"]!="SOURCE_ONLY_FREEZE_BEFORE_RAW_TRADES" or
        f["economic_outcomes_allowed"] is not False or
        f["price_grid"]!="floor((trade_price_cents - first_trade_price_cents)*10000 / first_trade_price_cents)" or
        f["min_trades_per_bar"]!=100 or f["min_occupied_price_bins"]!=8 or
        f["min_each_peak_share"]!=.08 or f["min_peak_separation_bins"]!=3 or
        f["max_valley_vs_smaller_peak"]!=.35 or
        len(f["dates"])!=3 or
        set(x[:4] for x in f["dates"])!={"2022","2023","2024"}):
        raise Blocked("UNEXPECTED_OR_MUTATED_FREEZE")
    return f

def download_one(day):
    name="BTCUSDT-aggTrades-"+day+".zip"
    def req(url):
        r=Request(url,headers={"User-Agent":"CryptoLab-YTAXIA-SourceCensus/0.1"})
        return urlopen(r,timeout=90)
    with req(PREFIX+name+".CHECKSUM") as r:
        parts=r.read(150).decode("ascii").split()
    if not parts or len(parts[0])!=64 or any(c not in "0123456789abcdefABCDEF" for c in parts[0]):
        raise Blocked("BAD_OFFICIAL_CHECKSUM")
    if len(parts)>1 and parts[1].lstrip("*").split("/")[-1]!=name:
        raise Blocked("OFFICIAL_CHECKSUM_NOT_BOUND_TO_FILE")
    target_hash=parts[0].lower()
    # Bounded memory: ZIP written to a short-lived, untracked temporary file.
    size=0;sha=hashlib.sha256()
    with tempfile.TemporaryFile() as dst:
        with req(PREFIX+name) as r:
            while True:
                block=r.read(1024*1024)
                if not block:break
                size+=len(block)
                if size>200_000_000:raise Blocked("ZIP_GT_200MB")
                sha.update(block);dst.write(block)
        if sha.hexdigest()!=target_hash:raise Blocked("SHA256_MISMATCH")
        dst.seek(0)
        bybar={};last_id=None;last_ts=None;count=0
        day_first=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
        day_last=day_first+86_400_000
        with zipfile.ZipFile(dst) as archive:
            members=[x for x in archive.namelist() if x.lower().endswith(".csv")]
            if len(members)!=1:raise Blocked("ZIP_HAS_WRONG_MEMBER_COUNT")
            with archive.open(members[0]) as raw:
                rows=csv.reader(io.TextIOWrapper(raw,encoding="utf-8-sig",newline=""))
                for row in rows:
                    if not row:continue
                    if row[0].strip().lower() in ("agg_trade_id","a"):continue
                    if len(row)<7:raise Blocked("BAD_CSV_COLUMNS")
                    agg_id=int(row[0]);price=price_to_cents(row[1])
                    qty=float(row[2]);ts=bounded_ms(row[5])
                    maker=row[6].strip().lower()
                    if maker not in ("true","false") or not math.isfinite(qty) or qty<=0:
                        raise Blocked("BAD_QTY_OR_AGGRESSOR")
                    if last_id is not None and agg_id<=last_id:raise Blocked("BAD_AGG_ID_ORDER")
                    if last_ts is not None and ts<last_ts:raise Blocked("BAD_TIME_ORDER")
                    if not day_first<=ts<day_last:raise Blocked("WRONG_DAY")
                    last_id=agg_id;last_ts=ts
                    bar_start=(ts//STEP)*STEP
                    if bar_start not in bybar:
                        bybar[bar_start]={"anchor":price,"bins":defaultdict(float),"trades":0,
                          "buy_qty":0.0,"sell_qty":0.0}
                    b=bybar[bar_start]
                    k=price_bucket(price,b["anchor"])
                    b["bins"][k]+=qty;b["trades"]+=1
                    if maker=="true":b["sell_qty"]+=qty
                    else:b["buy_qty"]+=qty
                    count+=1
        if len(bybar)!=288 or min(bybar)!=day_first or max(bybar)!=day_last-STEP:
            raise Blocked("SOURCE_DAY_5M_BUCKETS_NOT_COMPLETE")
        if any(day_first+i*STEP not in bybar for i in range(288)):
            raise Blocked("SOURCE_DAY_5M_GAP")
        return bybar,{"utc_day":day,"archive":name,"archive_sha256":target_hash,
          "compressed_bytes":size,"agg_trade_rows":count,"five_minute_bars":288}

def main():
    f=load_freeze()
    out=[]
    source_summaries=[]
    total_shapes=0;total_controls=0;days_with_shapes=0
    for day in f["dates"]:
        bars,proof=download_one(day)
        counts=Counter()
        for _,bar in sorted(bars.items()):
            n=bar["trades"];bins=bar["bins"]
            if n < f["min_trades_per_bar"] or len(bins)<f["min_occupied_price_bins"]:
                counts["INSUFFICIENT_PROFILE_GEOMETRY"]+=1
                continue
            shape=qualifies_shape(bins,n)
            counts["TWO_PEAK_VALLEY" if shape else "ELIGIBLE_OTHER_PROFILE"]+=1
        if counts["TWO_PEAK_VALLEY"]>0:days_with_shapes+=1
        total_shapes+=counts["TWO_PEAK_VALLEY"]
        total_controls+=counts["ELIGIBLE_OTHER_PROFILE"]
        source_summaries.append(proof)
        out.append({"utc_day":day,"source_only_count_classes":dict(sorted(counts.items()))})
        print("CENSUS_PASS",day,"trades",proof["agg_trade_rows"],"profile_shapes",counts["TWO_PEAK_VALLEY"],flush=True)
    viable=(total_shapes>=f["min_event_bars"] and
        days_with_shapes>=f["min_event_days"] and total_controls>=f["min_control_bars"])
    rec={"lab_id":"YT-AXIA-VAP-001","phase":"SOURCE_AND_PREOUTCOME_EVENT_COUNT_ONLY",
      "classification":"SOURCE_SHAPE_PREVALENCE_PASS_NOT_ECONOMIC" if viable else "SOURCE_SHAPE_RARE_SAMPLE_BLOCKED",
      "official_archive_sha256_verified":len(source_summaries),"proofs":source_summaries,
      "counts_by_probe_day":out,"bars_with_lab_defined_shape":total_shapes,
      "eligible_control_bars":total_controls,"days_with_shape":days_with_shapes,
      "source_full_year_coverage_verified":False,"price_rows_opened_same_bar_only":True,
      "future_returns_opened":False,"forward_outcomes_opened":False,
      "cost_or_trading_model_frozen":False,"trade_profitability_tested":False,
      "trading_authority":"NONE",
      "interpretation":"First source-only prevalence census of LAB-defined two-peak footprint geometry, not an Axia mechanical strategy, not a tradable signal. No confirmatory inference."
      }
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in rec.items() if k not in ("proofs","counts_by_probe_day")},indent=2))
    return rec

if __name__=="__main__":
    try:main()
    except (Blocked,ValueError,KeyError,zipfile.BadZipFile,TimeoutError) as e:
        result={"lab_id":"YT-AXIA-VAP-001","classification":"SOURCE_ONLY_BLOCKED","reason":type(e).__name__+":"+str(e),
          "forward_outcomes_opened":False,"trade_profitability_tested":False,"trading_authority":"NONE"}
        RECEIPT.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result),file=sys.stderr)
        sys.exit(2)

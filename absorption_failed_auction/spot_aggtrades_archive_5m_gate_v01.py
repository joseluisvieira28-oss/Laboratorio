#!/usr/bin/env python3
"""Source-only canonical Binance spot aggTrades 5m archive join, October 2-8 2026.

Uses original buyer-maker semantics, source SHA-256, causal 5m trade timestamps.
NEVER classifies events or reads FUTURE economic markouts. No exchange auth.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import tempfile
from urllib.request import Request,urlopen
import zipfile

BAR_MS=300_000
DAYS=[date(2026,10,2)+timedelta(days=n) for n in range(7)]
URL_PREFIX="https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
MAX_ARCHIVE_BYTES=100_000_000
SOURCE_LAB="ABSORPTION-FAILED-AUCTION-001"

def to_ms(raw):
    ts=int(raw)
    if ts<10**11: return ts*1000
    if ts<10**14: return ts
    if ts<10**17: return ts//1000
    return ts//1_000_000

def spot_aggressor_sign(is_buyer_maker):
    text=str(is_buyer_maker).strip().lower()
    if text not in ("true","false"):
        raise ValueError("buyer-maker semantics unknown")
    return -1 if text=="true" else 1

def spot_5m_close(t):
    return (t//BAR_MS+1)*BAR_MS

def get_checksum(day):
    name="BTCUSDT-aggTrades-"+day.isoformat()+".zip"
    req=Request(URL_PREFIX+name+".CHECKSUM",headers={"User-Agent":"CryptoLab-SpotSourceV1/0.1"})
    with urlopen(req,timeout=60) as h:
        if h.status!=200: raise ValueError("CHECKSUM_HTTP")
        content=h.read().decode("ascii","strict").strip().split()
    if not content or not re.fullmatch(r"[0-9a-fA-F]{64}",content[0]):
        raise ValueError("official checksum invalid for "+name)
    if len(content)>1 and content[1].lstrip("*").split("/")[-1]!=name:
        raise ValueError("checksum name mismatch for "+name)
    return name,content[0].lower()

def load_one(day, prior_id=None):
    name,checksum=get_checksum(day)
    req=Request(URL_PREFIX+name,headers={"User-Agent":"CryptoLab-SpotSourceV1/0.1"})
    hasher=hashlib.sha256()
    downloaded=0
    with tempfile.TemporaryFile() as tmp:
        with urlopen(req,timeout=90) as resp:
            if resp.status!=200: raise ValueError("ZIP_HTTP_"+name)
            while True:
                data=resp.read(1024*1024)
                if not data: break
                downloaded+=len(data)
                if downloaded>MAX_ARCHIVE_BYTES: raise ValueError("ZIP_SIZE_CAP_"+name)
                hasher.update(data);tmp.write(data)
        if hasher.hexdigest()!=checksum: raise ValueError("OFFICIAL_ZIP_SHA256_FAIL_"+name)
        tmp.seek(0)
        counts=defaultdict(lambda:[0.0,0.0,0])
        lo=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
        hi=lo+86400_000
        n=0
        with zipfile.ZipFile(tmp) as z:
            members=[p for p in z.namelist() if p.lower().endswith(".csv")]
            if len(members)!=1: raise ValueError("CSV_MEMBER_COUNT_"+name)
            with z.open(members[0]) as source:
                rows=csv.reader(io.TextIOWrapper(source,encoding="utf-8-sig",newline=""))
                for row in rows:
                    if not row: continue
                    if n==0 and row[0].strip().lower() in ("agg_trade_id","a"): continue
                    if len(row)<7: raise ValueError("CSV_BAD_COLUMNS_"+name)
                    agg_id=int(row[0])
                    if prior_id is not None and agg_id<=prior_id: raise ValueError("NONMONOTONE_OR_DUPLICATE_AGG_ID_"+name)
                    prior_id=agg_id
                    ts=to_ms(row[5])
                    if not lo<=ts<hi: raise ValueError("TRADE_TIMESTAMP_DAY_MISMATCH_"+name)
                    p=float(row[1]);qty=float(row[2])
                    if not all(math.isfinite(x) for x in (p,qty)) or p<=0 or qty<=0:
                        raise ValueError("INVALID_TRADE_PRICE_QTY_"+name)
                    side=spot_aggressor_sign(row[6])
                    b=counts[spot_5m_close(ts)]
                    if side==1:b[0]+=qty
                    else:b[1]+=qty
                    b[2]+=1
                    n+=1
        if n==0: raise ValueError("EMPTY_AGGTRADES_"+name)
        print("ZIP_VERIFIED",str(day),"trades",n,"size_bytes",downloaded,"buckets",len(counts),flush=True)
        return counts,prior_id,{"day":str(day),"sha256":checksum,"zip_bytes":downloaded,"agg_trade_rows":n,"five_minute_buckets":len(counts)}

def verify_vault(root,all_features):
    vault_root=Path(root)
    days={}
    total=0
    first=None;last=None
    for day in DAYS:
        label=day.isoformat()
        p=vault_root/"archive"/label/f"{label}.manifest.json"
        manifest=json.loads(p.read_text())
        raw=(vault_root/"archive"/label/f"{label}.jsonl").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=manifest["corpus_sha256"]:
            raise ValueError("VAULT_CORPUS_SHA256_FAIL_"+label)
        closes=[]
        for line in raw.decode("utf-8").splitlines():
            obj=json.loads(line)
            if obj.get("trading_authority")!="NONE" or obj["payload"].get("sensor_version")!="MM-V1":
                raise ValueError("VAULT_SENSOR_IDENTITY_FAIL")
            t=int(obj["payload"]["bar_close_ms"])
            if t not in all_features:
                raise ValueError("SOURCE_MISSING_CANONICAL_FLOW_"+str(t))
            b=all_features[t]
            if sum(b[:2])<=0:
                raise ValueError("SOURCE_ZERO_BASE_VOLUME_"+str(t))
            closes.append(t)
        if not closes or any(b-a!=BAR_MS for a,b in zip(closes,closes[1:])):
            raise ValueError("SENSOR_WITHIN_DAY_GAP_"+label)
        if label=="2026-10-02":
            if len(closes)!=175: raise ValueError("OCT2_PARTIAL_SIZE_CHANGED")
        elif len(closes)!=288: raise ValueError("FULL_DAY_COUNT_CHANGED_"+label)
        days[label]={"sensor_bars":len(closes),"source_flow_bars_present":len(closes),"sensor_manifest_sha256":manifest["corpus_sha256"]}
        total+=len(closes)
        if first is None:first=closes[0]
        if last is not None and closes[0]-last!=BAR_MS:
            raise ValueError("GAP_BETWEEN_PUBLISHED_VAULT_DAYS")
        last=closes[-1]
    if total!=1903:
        raise ValueError("EXPECTED_1903_SOURCE_BOUND_BARS")
    return days,first,last

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--vault-root",required=True)
    arg.add_argument("--outdir",required=True)
    opts=arg.parse_args()
    out=Path(opts.outdir);out.mkdir(parents=True,exist_ok=True)
    previous_id=None;features={};proof=[]
    for day in DAYS:
        current,previous_id,source=load_one(day,previous_id)
        for close,b in current.items():
            if close in features:
                raise ValueError("OVERLAP_AGG_BUCKET_DUPLICATE")
            features[close]=b
        proof.append(source)
    days,first,last=verify_vault(opts.vault_root,features)
    path=out/"SOURCE_ONLY_CANONICAL_SPOT_AGGTRADES_5M_2026-10-02_TO_08.jsonl"
    with path.open("w") as f:
        for k in sorted(features):
            buy,sell,n=features[k]
            if buy+sell<=0: continue
            f.write(json.dumps({"bar_close_ms":k,"aggressive_buy_qty":buy,
                "aggressive_sell_qty":sell,"agg_delta_pct":(buy-sell)/(buy+sell),
                "agg_base_volume":buy+sell,"agg_trade_count":n},sort_keys=True)+"\n")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    receipt={
        "lab_id":SOURCE_LAB,"state":"SPOT_AGGTRADES_ARCHIVE_FULL_SHA256_AND_1903_VAULT_BARS_MATCH_PASS",
        "days":proof,"vault_coverage":days,
        "total_verified_spot_trade_rows":sum(x["agg_trade_rows"] for x in proof),
        "total_downloaded_compressed_bytes":sum(x["zip_bytes"] for x in proof),
        "source_5m_bar_count":len(features),
        "vault_bound_bars":sum(x["sensor_bars"] for x in days.values()),
        "vault_first_close_ms":first,"vault_last_close_ms":last,
        "source_feature_corpus_sha256":digest,
        "2026_10_09_current_day_flow_covered":False,
        "2016_full_prior_bars_complete_in_this_archive_only":False,
        "new_primary_events_classified":False,
        "economic_outcomes_unlocked":False,"trading_authority":"NONE",
        "note":"Technical source mapping only: source candles 2026-10-02..08 are 1903 <2016. The additional 2026-10-09 as-of 133 footprint bars still need canonical spot flow data; no classifier / outcome run."
    }
    (out/"SOURCE_ONLY_CANONICAL_SPOT_AGGTRADES_GATE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in receipt.items() if k not in ("vault_coverage","days")},indent=2))
if __name__=="__main__":
    main()

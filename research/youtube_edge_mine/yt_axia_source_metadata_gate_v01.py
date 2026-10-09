#!/usr/bin/env python3
"""YT-AXIA-VAP-001: metadata-only official Binance spot aggTrades feasibility.

Never downloads ZIP bodies or reads price/trades/future returns. Date list is
frozen inside the script for a price-blind source gate. Read-only public HTTP.
"""
from __future__ import annotations
from datetime import date
import json, re, sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

DATES=("2022-01-12","2022-06-16","2022-11-12",
       "2023-02-14","2023-07-20","2023-12-15",
       "2024-01-18","2024-04-19","2024-08-08","2024-11-25")
PREFIX="https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
OUT=Path(__file__).with_name("YT_AXIA_VAP_001_SPOT_SOURCE_METADATA_RECEIPT.json")
class GateError(Exception): pass

def parse_checksum(data,expected_name):
    try: parts=data.decode("ascii","strict").strip().split()
    except (UnicodeError,ValueError):raise GateError("NON_ASCII_CHECKSUM")
    if len(parts)<1 or not re.fullmatch(r"[a-fA-F0-9]{64}",parts[0]):raise GateError("CHECKSUM_SHA256_INVALID")
    if len(parts)>1 and parts[1].lstrip("*").split("/")[-1]!=expected_name:raise GateError("CHECKSUM_NAME_MISMATCH")
    return parts[0].lower()

def head_probe(day,transport=None):
    date.fromisoformat(day)
    name=f"BTCUSDT-aggTrades-{day}.zip"
    url=PREFIX+name
    transport=transport or http
    content_length,_=transport(url,"HEAD")
    _,checksum_data=transport(url+".CHECKSUM","GET")
    digest=parse_checksum(checksum_data,name)
    if content_length<=0 or content_length>=2_000_000_000:raise GateError("ARCHIVE_SIZE_UNUSABLE")
    return {"utc_day":day,"filename":name,"compressed_bytes":content_length,"checksum_metadata_sha256":digest,"zip_content_opened":False}

def http(url,method):
    req=Request(url,method=method,headers={"User-Agent":"CryptoLab-YTAXIA-SourceGate/0.1"})
    try:
        with urlopen(req,timeout=40) as r:
            if r.status!=200:raise GateError("HTTP_STATUS_NOT_200")
            size=int(r.headers.get("Content-Length","0"))
            body=b"" if method=="HEAD" else r.read(512)
            return size,body
    except (HTTPError,URLError,TimeoutError) as err:
        raise GateError("SOURCE_TRANSPORT_"+type(err).__name__) from None

def run():
    manifest=[]
    for day in DATES:
        val=head_probe(day)
        manifest.append(val)
        print("SPOT_AGGTRADES_META_OK",day,val["compressed_bytes"],flush=True)
    receipt={"lab_id":"YT-AXIA-VAP-001","state":"OFFICIAL_SPOT_PRICE_LEVEL_ARCHIVES_METADATA_PASS",
      "tested_dates":list(DATES),"checked_archives":len(manifest),"files":manifest,
      "total_compressed_bytes_on_probed_dates":sum(x["compressed_bytes"] for x in manifest),
      "price_level_source_possible":True,
      "zip_bodies_downloaded":False,"zip_sha256_data_verified":False,
      "price_rows_opened":False,"outcomes_opened":False,"trading_authority":"NONE",
      "not_a_full_year_coverage_proof":True,
      "note":"Public official spot aggTrades include price/size/buyer-maker/timestamp; historical availability sampled. Source alone cannot prove a P shape, true iceberg, resting book liquidity, capacity, fills or net expectancy."
      }
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"state":receipt["state"],"checked_archives":len(manifest)}))

if __name__=="__main__":
    try:run()
    except GateError as exc:
        d={"lab_id":"YT-AXIA-VAP-001","state":"SOURCE_METADATA_BLOCKED",
           "reason":str(exc),"price_rows_opened":False,"outcomes_opened":False,"trading_authority":"NONE"}
        OUT.write_text(json.dumps(d,indent=2)+"\n")
        print(json.dumps(d),file=sys.stderr);sys.exit(2)

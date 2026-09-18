#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, re, sys, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import requests

DAY="2021-01-15"
SYMBOL="BTCUSDT"
BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
ZIP_NAME=f"{SYMBOL}-metrics-{DAY}.zip"
ZIP_URL=f"{BASE}/{ZIP_NAME}"
CHECKSUM_URL=ZIP_URL+".CHECKSUM"

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def checksum(text:str)->str:
    m=re.search(r"\b([0-9a-fA-F]{64})\b",text)
    if not m: raise ValueError("checksum not found")
    return m.group(1).lower()

def main()->int:
    out=Path("ll0017_dupdiag_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"LL0017_DUPLICATE_PROVENANCE_DIAGNOSTIC_V0_1.json"
    receipt={}
    try:
        zr=requests.get(ZIP_URL,timeout=(15,120),headers={"User-Agent":"LL0017/dupdiag-v0.1"})
        cr=requests.get(CHECKSUM_URL,timeout=(15,120),headers={"User-Agent":"LL0017/dupdiag-v0.1"})
        if zr.status_code!=200 or cr.status_code!=200:
            raise RuntimeError(f"http zip={zr.status_code} checksum={cr.status_code}")
        actual=sha(zr.content); expected=checksum(cr.text)
        if actual!=expected: raise RuntimeError("checksum mismatch")
        with zipfile.ZipFile(io.BytesIO(zr.content)) as zf:
            members=[x for x in zf.namelist() if not x.endswith("/")]
            if len(members)!=1: raise RuntimeError(f"members={members}")
            raw=zf.read(members[0]).decode("utf-8-sig")
        lines=raw.splitlines()
        if not lines: raise RuntimeError("empty csv")
        header=next(csv.reader([lines[0]]))
        lower=[x.strip().lower() for x in header]
        if "create_time" not in lower or "symbol" not in lower:
            raise RuntimeError(f"required structural fields missing header={header}")
        ti=lower.index("create_time"); si=lower.index("symbol")
        groups=defaultdict(list)
        row_count=0
        symbol_counts=Counter()
        for line in lines[1:]:
            if not line.strip(): continue
            row=next(csv.reader([line]))
            if len(row)!=len(header): raise RuntimeError("row width mismatch")
            t=row[ti].strip(); sym=row[si].strip()
            symbol_counts[sym]+=1
            groups[t].append(sha(line.encode("utf-8")))
            row_count+=1
        multiplicities=Counter(len(v) for v in groups.values())
        duplicate_groups={k:v for k,v in groups.items() if len(v)>1}
        exact=0; distinct=0
        per_group_distinct_hash_counts=Counter()
        for hashes in duplicate_groups.values():
            n=len(set(hashes)); per_group_distinct_hash_counts[n]+=1
            if n==1: exact+=1
            else: distinct+=1
        if not duplicate_groups:
            classification="DIAGNOSTIC_PROVENANCE_FAILURE"
            failure="expected duplicate groups from parent run but found none"
        elif distinct==0:
            classification="EXACT_PROVIDER_ROW_DUPLICATION_CONFIRMED"; failure=None
        else:
            classification="MULTIPLE_DISTINCT_ROWS_PER_TIMESTAMP"; failure=None
        receipt={
          "classification":classification,
          "failure":failure,
          "date":DAY,
          "provider_sha256":expected,
          "archive_sha256":actual,
          "header":header,
          "row_count":row_count,
          "unique_timestamp_count":len(groups),
          "timestamp_multiplicity_distribution":dict(sorted(multiplicities.items())),
          "duplicate_timestamp_group_count":len(duplicate_groups),
          "exact_duplicate_group_count":exact,
          "distinct_duplicate_group_count":distinct,
          "distinct_raw_hashes_per_duplicate_group_distribution":dict(sorted(per_group_distinct_hash_counts.items())),
          "symbol_counts":dict(symbol_counts),
          "safety":{
            "ratio_numeric_values_parsed":False,
            "ratio_numeric_values_persisted":False,
            "metric_values_exposed":False,
            "prices_opened":False,
            "returns_opened":False,
            "pnl_opened":False,
            "2025_accessed":False,
            "2026_accessed":False
          }
        }
    except Exception as exc:
        receipt={"classification":"DIAGNOSTIC_TECHNICAL_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1200]}",
                 "safety":{"ratio_numeric_values_parsed":False,"prices_opened":False,"returns_opened":False,"pnl_opened":False,"2025_accessed":False,"2026_accessed":False}}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))
    return 0 if receipt["classification"] in ("EXACT_PROVIDER_ROW_DUPLICATION_CONFIRMED","MULTIPLE_DISTINCT_ROWS_PER_TIMESTAMP") else 2
if __name__=="__main__": sys.exit(main())

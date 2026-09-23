#!/usr/bin/env python3
"""DCV-001 source-only duplicate diagnostic. Never emits economic field values."""
import csv, hashlib, io, json, re, sys, time, urllib.request, zipfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
UA="Crypto-Lab-DCV001-DuplicateDiagnostic/0.1"
OUT=Path("dcv001_metrics_duplicate_diagnostic.json")

def req(url, attempts=4):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=60) as x:
                return x.read()
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(1.5*(i+1))
    raise RuntimeError(f"download_failed:{url}:{type(last).__name__}:{last}")

def checksum(url):
    t=req(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",t)
    if not m: raise RuntimeError("checksum_parse")
    return m.group(1).lower()

def inspect(ds):
    url=f"{BASE}/BTCUSDT-metrics-{ds}.zip"
    raw=req(url)
    sha=hashlib.sha256(raw).hexdigest()
    pub=checksum(url)
    if sha!=pub: raise RuntimeError(f"checksum_mismatch:{ds}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(names)!=1: raise RuntimeError(f"csv_count:{ds}:{len(names)}")
        rows=[r for r in csv.reader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))) if r]
    header=[x.strip() for x in rows[0]]
    ti=header.index("create_time")
    si=header.index("symbol")
    body=[r for r in rows[1:] if len(r)>max(ti,si) and r[si].strip()=="BTCUSDT"]
    groups=defaultdict(list)
    for r in body:
        groups[r[ti].strip()].append(tuple(x.strip() for x in r))
    dup_groups={k:v for k,v in groups.items() if len(v)>1}
    exact_dup_groups=sum(1 for v in dup_groups.values() if len(set(v))==1)
    conflicting_groups=sum(1 for v in dup_groups.values() if len(set(v))>1)
    max_mult=max((len(v) for v in dup_groups.values()),default=1)
    return {
        "date":ds,
        "checksum_verified":True,
        "row_count":len(body),
        "unique_create_time_count":len(groups),
        "duplicate_timestamp_group_count":len(dup_groups),
        "duplicate_row_excess_count":len(body)-len(groups),
        "exact_duplicate_timestamp_group_count":exact_dup_groups,
        "conflicting_duplicate_timestamp_group_count":conflicting_groups,
        "max_timestamp_multiplicity":max_mult,
        "economic_values_reported":False,
    }

def main():
    dates=[]
    d=date(2021,1,1)
    while d<=date(2021,1,31):
        dates.append(d.isoformat()); d+=timedelta(days=1)
    dates += ["2021-02-15","2021-03-15","2021-04-15","2021-05-15","2021-06-15"]
    rows=[inspect(ds) for ds in dates]
    out={
        "lab_id":"DCV-001",
        "diagnostic":"METRICS_DUPLICATE_SOURCE_ONLY_V0.1",
        "classification":"DIAGNOSTIC_COMPLETE",
        "economic_values_reported":False,
        "outcomes_opened":False,
        "protected_2025_accessed":False,
        "protected_2026_accessed":False,
        "dates":rows,
        "total_duplicate_timestamp_groups":sum(x["duplicate_timestamp_group_count"] for x in rows),
        "total_exact_duplicate_timestamp_groups":sum(x["exact_duplicate_timestamp_group_count"] for x in rows),
        "total_conflicting_duplicate_timestamp_groups":sum(x["conflicting_duplicate_timestamp_group_count"] for x in rows),
    }
    out["receipt_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":out["classification"],
        "dates_scanned":len(rows),
        "total_duplicate_timestamp_groups":out["total_duplicate_timestamp_groups"],
        "total_exact_duplicate_timestamp_groups":out["total_exact_duplicate_timestamp_groups"],
        "total_conflicting_duplicate_timestamp_groups":out["total_conflicting_duplicate_timestamp_groups"],
        "economic_values_reported":False,
        "outcomes_opened":False,
        "receipt_sha256":out["receipt_sha256"],
    },sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())

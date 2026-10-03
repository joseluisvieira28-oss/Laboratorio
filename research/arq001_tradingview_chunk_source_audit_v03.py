#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, math, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

LAB="ARQ-001-DRF-001"
ROOT=Path("research/arq001_source_inputs_v03")
OUT=Path("research/arq001_source_evidence_v03")
OUT.mkdir(parents=True,exist_ok=True)

SERIES=("BTC.D","USDT.D","TOTAL3")
START=datetime(2022,1,1,tzinfo=timezone.utc)
END=datetime(2024,12,31,23,59,tzinfo=timezone.utc)
TS_NAMES=("time","timestamp","datetime","date")
OHLC=("open","high","low","close")

def sha256_file(p: Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def parse_ts(v: str):
    s=v.strip()
    if re.fullmatch(r"\d{10,16}",s):
        n=int(s)
        if n>10**14: n=n/1_000_000
        elif n>10**11: n=n/1000
        return datetime.fromtimestamp(n,tz=timezone.utc)
    if s.endswith("Z"):
        s=s[:-1]+"+00:00"
    dt=datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("naive timestamp")
    return dt.astimezone(timezone.utc)

def norm_headers(fieldnames):
    return {str(x).strip().lower():x for x in fieldnames or []}

def read_chunk(p: Path):
    rows={}
    with p.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        hm=norm_headers(rd.fieldnames)
        ts_key=next((hm[k] for k in TS_NAMES if k in hm),None)
        keys={k:hm.get(k) for k in OHLC}
        if ts_key is None or any(v is None for v in keys.values()):
            raise RuntimeError(f"SCHEMA:{p.name}: headers={rd.fieldnames}")
        for idx,r in enumerate(rd,2):
            dt=parse_ts(str(r[ts_key]))
            if dt.second!=0 or dt.microsecond!=0:
                raise RuntimeError(f"NON_MINUTE_TIMESTAMP:{p.name}:{idx}:{dt.isoformat()}")
            vals=tuple(float(r[keys[k]]) for k in OHLC)
            if not all(math.isfinite(x) for x in vals):
                raise RuntimeError(f"NONFINITE_OHLC:{p.name}:{idx}")
            if START<=dt<=END:
                old=rows.get(dt)
                if old is not None and old!=vals:
                    raise RuntimeError(f"CONFLICTING_DUPLICATE_WITHIN_FILE:{p.name}:{dt.isoformat()}")
                rows[dt]=vals
    return rows, {"headers":rd.fieldnames}

def expected_required():
    x=START.replace(minute=0)
    end_hour=END.replace(minute=0)
    out=[]
    while x<=end_hour:
        out.extend([x,x+timedelta(minutes=1),x+timedelta(minutes=2)])
        x+=timedelta(hours=1)
    return out

receipt={
 "lab_id":LAB,
 "version":"0.3",
 "classification":"SOURCE_GATE_BLOCKED_MISSING_EXPORT",
 "source_only":True,
 "outcomes_opened":False,
 "year_2025_accessed":False,
 "year_2026_accessed":False,
 "series":{},
}
required=expected_required()
all_pass=True
missing_any=False
try:
  for s in SERIES:
    files=sorted((ROOT/s).glob("*.csv")) if (ROOT/s).exists() else []
    if not files:
        receipt["series"][s]={"files":[],"classification":"MISSING_EXPORT"}
        missing_any=True; all_pass=False; continue
    merged={}
    meta=[]
    for p in files:
        part,info=read_chunk(p)
        for ts,val in part.items():
            if ts in merged and merged[ts]!=val:
                raise RuntimeError(f"CONFLICTING_DUPLICATE_ACROSS_FILES:{s}:{ts.isoformat()}")
            merged[ts]=val
        meta.append({"path":str(p),"bytes":p.stat().st_size,"sha256":sha256_file(p),"rows_in_window":len(part),"headers":info["headers"]})
    missing=[ts for ts in required if ts not in merged]
    canonical=OUT/f"{s}_CANONICAL_1M_2022_2024.csv"
    with canonical.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["timestamp_utc","open","high","low","close"])
        for ts in sorted(merged):
            w.writerow([ts.isoformat().replace("+00:00","Z"),*merged[ts]])
    cls="SOURCE_SERIES_PASS" if not missing else "INSUFFICIENT_INTRADAY_HISTORY"
    if missing: all_pass=False
    receipt["series"][s]={
      "classification":cls,
      "files":meta,
      "merged_unique_minutes":len(merged),
      "required_regime_minutes":len(required),
      "required_regime_minutes_present":len(required)-len(missing),
      "required_regime_minutes_missing":len(missing),
      "first_missing_required":missing[0].isoformat().replace("+00:00","Z") if missing else None,
      "last_missing_required":missing[-1].isoformat().replace("+00:00","Z") if missing else None,
      "canonical_path":str(canonical),
      "canonical_sha256":sha256_file(canonical),
    }

  if missing_any:
      receipt["classification"]="SOURCE_GATE_BLOCKED_MISSING_EXPORT"
  elif all_pass:
      receipt["classification"]="SOURCE_DATA_PASS"
  else:
      receipt["classification"]="SOURCE_GATE_BLOCKED_INSUFFICIENT_INTRADAY_HISTORY"
except RuntimeError as e:
  msg=str(e)
  receipt["failure"]=msg
  receipt["classification"]="SOURCE_SCHEMA_FAILURE" if msg.startswith(("SCHEMA:","NON_MINUTE_TIMESTAMP:","NONFINITE_OHLC:")) else "SOURCE_PROVENANCE_FAILURE"
except Exception as e:
  receipt["failure"]=f"{type(e).__name__}:{e}"
  receipt["classification"]="SOURCE_SCHEMA_FAILURE"

out=OUT/"ARQ001_TRADINGVIEW_CHUNK_SOURCE_RECEIPT_V0_3.json"
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({
 "classification":receipt["classification"],
 "series":{k:{x:v.get(x) for x in ("classification","merged_unique_minutes","required_regime_minutes_present","required_regime_minutes_missing")} for k,v in receipt["series"].items()}
},sort_keys=True))

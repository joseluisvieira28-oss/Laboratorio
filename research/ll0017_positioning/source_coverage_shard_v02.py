#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, os, re, sys, time, zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
import requests

LAB_ID="LL-0017-POSITIONING-RATIO-001"
BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
SYMBOL="BTCUSDT"
EXPECTED_HEADER=[
 "create_time","symbol","sum_open_interest","sum_open_interest_value",
 "count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio",
 "count_long_short_ratio","sum_taker_long_short_vol_ratio"
]
TRANSIENT={429,500,502,503,504,529}

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def parse_checksum(text:str)->str:
    m=re.search(r"\b([0-9a-fA-F]{64})\b",text)
    if not m: raise ValueError("provider checksum not found")
    return m.group(1).lower()
def parse_ts(s:str)->int:
    s=s.strip()
    if re.fullmatch(r"\d+",s):
        n=int(s)
        if n>10**17: return n//10**9
        if n>10**14: return n//10**6
        if n>10**11: return n//1000
        return n
    dt=datetime.fromisoformat(s.replace("Z","+00:00"))
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())
def dayof(ts:int)->str:
    return datetime.fromtimestamp(ts,tz=timezone.utc).strftime("%Y-%m-%d")
def dates_inclusive(a:str,b:str):
    cur=date.fromisoformat(a); end=date.fromisoformat(b)
    while cur<=end:
        yield cur.isoformat()
        cur+=timedelta(days=1)
def fetch(session:requests.Session,url:str,stats:Counter)->requests.Response:
    if "2025" in url or "2026" in url: raise RuntimeError("protected-period URL rejected")
    last=None
    for attempt in range(6):
        try:
            r=session.get(url,timeout=(15,120),headers={"User-Agent":f"{LAB_ID}/coverage-v0.2"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1
                last=RuntimeError(f"transient HTTP {r.status_code}")
                r.close()
                if attempt<5:
                    time.sleep(min(8.0,0.75*(2**attempt))); continue
                raise last
            return r
        except requests.RequestException as exc:
            stats["network_retries"]+=1; last=exc
            if attempt<5:
                time.sleep(min(8.0,0.75*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def main()->int:
    shard_id=os.environ["SHARD_ID"]
    start=os.environ["SHARD_START_DATE"]
    end=os.environ["SHARD_END_DATE"]
    if start[:4] in ("2025","2026") or end[:4] in ("2025","2026"):
        raise SystemExit("protected period shard")
    expected_days=list(dates_inclusive(start,end))
    stats=Counter()
    day_rows=[]
    failures=[]
    session=requests.Session()
    try:
        for day in expected_days:
            try:
                zn=f"{SYMBOL}-metrics-{day}.zip"
                zu=f"{BASE}/{zn}"; cu=zu+".CHECKSUM"
                zr=fetch(session,zu,stats); cr=fetch(session,cu,stats)
                if zr.status_code!=200 or cr.status_code!=200:
                    failures.append({"date":day,"classification":"SOURCE_ACCESS_BLOCKED","detail":f"zip={zr.status_code} checksum={cr.status_code}"})
                    zr.close(); cr.close(); continue
                zbytes=zr.content; checksum_text=cr.text; zr.close(); cr.close()
                provider=parse_checksum(checksum_text); actual=sha(zbytes)
                if provider!=actual:
                    failures.append({"date":day,"classification":"SOURCE_CHECKSUM_FAILURE","detail":"checksum mismatch"}); continue
                with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
                    members=[x for x in zf.namelist() if not x.endswith("/")]
                    if len(members)!=1 or not members[0].lower().endswith(".csv"):
                        failures.append({"date":day,"classification":"SOURCE_SCHEMA_INADEQUATE","detail":f"members={members}"}); continue
                    text=zf.read(members[0]).decode("utf-8-sig")
                lines=text.splitlines()
                if not lines:
                    failures.append({"date":day,"classification":"SOURCE_SCHEMA_INADEQUATE","detail":"empty CSV"}); continue
                header=[x.strip() for x in next(csv.reader([lines[0]]))]
                if header!=EXPECTED_HEADER:
                    failures.append({"date":day,"classification":"SOURCE_SCHEMA_INADEQUATE","detail":f"header={header}"}); continue
                ti=0
                groups={}
                raw_rows=0
                malformed=False
                for line in lines[1:]:
                    if not line.strip(): continue
                    row=next(csv.reader([line]))
                    if len(row)!=len(EXPECTED_HEADER):
                        failures.append({"date":day,"classification":"PROVENANCE_FAILURE","detail":"row width mismatch"}); malformed=True; break
                    ts=parse_ts(row[ti])
                    groups.setdefault(ts,set()).add(sha(line.encode("utf-8")))
                    raw_rows+=1
                if malformed: continue
                divergent=sum(1 for hs in groups.values() if len(hs)>1)
                if divergent:
                    failures.append({"date":day,"classification":"PROVENANCE_FAILURE","detail":f"nonidentical duplicate groups={divergent}"}); continue
                unique=sorted(groups)
                if any(dayof(x)!=day for x in unique):
                    failures.append({"date":day,"classification":"PROVENANCE_FAILURE","detail":"timestamp outside requested UTC date"}); continue
                diffs=[b-a for a,b in zip(unique,unique[1:])]
                med=median(diffs) if diffs else None
                p95=sorted(diffs)[max(0,min(len(diffs)-1,int(.95*(len(diffs)-1))))] if diffs else None
                if len(unique)<280 or med is None or med>600:
                    failures.append({"date":day,"classification":"SOURCE_TEMPORAL_COVERAGE_INADEQUATE","detail":f"unique={len(unique)} median={med}"}); continue
                day_rows.append({
                    "date":day,"archive_sha256":actual,"archive_bytes":len(zbytes),
                    "raw_row_count":raw_rows,"normalized_unique_timestamp_count":len(unique),
                    "exact_duplicate_rows_removed":raw_rows-len(unique),
                    "median_interval_seconds":med,"p95_interval_seconds":p95,
                    "first_timestamp_utc":datetime.fromtimestamp(unique[0],tz=timezone.utc).isoformat(),
                    "last_timestamp_utc":datetime.fromtimestamp(unique[-1],tz=timezone.utc).isoformat()
                })
                stats["zip_pass"]+=1; stats["checksum_pass"]+=1
            except requests.RequestException as exc:
                failures.append({"date":day,"classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE","detail":f"{type(exc).__name__}: {str(exc)[:300]}"})
            except Exception as exc:
                failures.append({"date":day,"classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE","detail":f"{type(exc).__name__}: {str(exc)[:500]}"})
    finally:
        session.close()

    if failures:
        classes=[x["classification"] for x in failures]
        precedence=["PROVENANCE_FAILURE","SOURCE_CHECKSUM_FAILURE","SOURCE_SCHEMA_INADEQUATE","SOURCE_TEMPORAL_COVERAGE_INADEQUATE","SOURCE_ACCESS_BLOCKED","SOURCE_ACQUISITION_TECHNICAL_FAILURE"]
        classification=next((x for x in precedence if x in classes),"SOURCE_ACQUISITION_TECHNICAL_FAILURE")
    else:
        classification="SHARD_PASS"

    receipt={
      "lab_id":LAB_ID,"phase":"HISTORICAL_SOURCE_COVERAGE_SHARD_V0_2_OUTCOME_BLIND",
      "shard_id":shard_id,"start_date":start,"end_date":end,"expected_day_count":len(expected_days),
      "classification":classification,"resolved_day_count":len(day_rows),"failures":failures,
      "days":day_rows,"transport_stats":dict(stats),
      "safety":{"ratio_numeric_values_parsed":False,"metric_values_exposed":False,"prices_opened":False,"returns_opened":False,"pnl_opened":False,"2025_accessed":False,"2026_accessed":False,"live_trading":False,"exchange_mutation":False}
    }
    out=Path("ll0017_coverage_shards"); out.mkdir(parents=True,exist_ok=True)
    p=out/f"coverage_shard_{shard_id}.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard":shard_id,"classification":classification,"expected_days":len(expected_days),"resolved_days":len(day_rows),"failures":len(failures),"full_288_days":sum(1 for x in day_rows if x["normalized_unique_timestamp_count"]==288),"duplicate_rows_removed":sum(x["exact_duplicate_rows_removed"] for x in day_rows),"ratio_values_parsed":False},sort_keys=True))
    return 0 if classification=="SHARD_PASS" else 2
if __name__=="__main__": sys.exit(main())

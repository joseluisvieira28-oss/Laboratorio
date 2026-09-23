#!/usr/bin/env python3
import concurrent.futures, datetime as dt, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE="https://data.solarchive.org/txs"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SOLARCHIVE_FEASIBILITY_RECEIPT_V0.1.json")
UA="crypto-lab-dls-source-feasibility/0.1"

KAMINO_START=dt.date(2023,11,17)
SAVE11_START=dt.date(2024,7,19)
END=dt.date(2025,1,1)  # exclusive

def daterange(a,b):
    d=a
    while d<b:
        yield d
        d += dt.timedelta(days=1)

def fetch_json(url, timeout=30):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw=r.read()
            return {"status":int(r.status),"json":json.loads(raw),"bytes":len(raw),"url":r.geturl()}
    except urllib.error.HTTPError as e:
        return {"status":int(e.code),"error":"HTTPError","url":url}
    except Exception as e:
        return {"status":None,"error":type(e).__name__,"detail":str(e)[:300],"url":url}

def walk_files(obj, base_url):
    out=[]
    def rec(x):
        if isinstance(x, dict):
            # Common index shapes: {name/path/url, size/bytes/...}
            vals={str(k).lower():v for k,v in x.items()}
            candidate=None
            for key in ("url","download_url","href","path","name","key","file"):
                v=vals.get(key)
                if isinstance(v,str) and v.endswith(".parquet"):
                    candidate=v
                    break
            if candidate:
                u=urllib.parse.urljoin(base_url.rstrip("/")+"/", candidate)
                size=None
                for key in ("size","bytes","size_bytes","content_length","contentlength"):
                    v=vals.get(key)
                    if isinstance(v,(int,float)):
                        size=int(v); break
                    if isinstance(v,str) and v.isdigit():
                        size=int(v); break
                out.append({"url":u,"declared_bytes":size})
            for v in x.values(): rec(v)
        elif isinstance(x,list):
            for v in x: rec(v)
        elif isinstance(x,str) and x.endswith(".parquet"):
            out.append({"url":urllib.parse.urljoin(base_url.rstrip("/")+"/",x),"declared_bytes":None})
    rec(obj)
    # dedupe
    seen=set(); ded=[]
    for row in out:
        if row["url"] not in seen:
            seen.add(row["url"]); ded.append(row)
    return ded

all_dates=sorted(set(daterange(KAMINO_START,END)) | set(daterange(SAVE11_START,END)))

def probe_date(d):
    ds=d.isoformat()
    url=f"{BASE}/{ds}/index.json"
    x=fetch_json(url)
    rec={"date":ds,"http_status":x.get("status"),"index_url":url,"index_bytes":x.get("bytes")}
    if x.get("status")==200 and "json" in x:
        files=walk_files(x["json"],f"{BASE}/{ds}/")
        rec["published_file_count"]=len(files)
        rec["declared_partition_bytes"]=sum(v["declared_bytes"] or 0 for v in files)
        rec["declared_bytes_known_files"]=sum(1 for v in files if v["declared_bytes"] is not None)
        rec["first_file_url"]=files[0]["url"] if files else None
    else:
        rec["error"]=x.get("error")
        rec["detail"]=x.get("detail")
    return rec

rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    futs={ex.submit(probe_date,d):d for d in all_dates}
    for i,f in enumerate(concurrent.futures.as_completed(futs),1):
        rows.append(f.result())
        if i%50==0: print(f"INDEX_PROGRESS {i}/{len(all_dates)}",flush=True)
rows.sort(key=lambda r:r["date"])
by_date={r["date"]:r for r in rows}

def summarize(start):
    dates=[d.isoformat() for d in daterange(start,END)]
    missing=[d for d in dates if by_date[d].get("http_status")!=200 or by_date[d].get("published_file_count",0)<=0]
    known=[by_date[d] for d in dates if by_date[d].get("http_status")==200]
    return {
      "start":start.isoformat(),
      "end_exclusive":END.isoformat(),
      "required_dates":len(dates),
      "available_nonempty_dates":len(dates)-len(missing),
      "missing_or_empty_dates":missing,
      "index_http_200_dates":sum(1 for d in dates if by_date[d].get("http_status")==200),
      "published_file_count":sum(by_date[d].get("published_file_count",0) for d in dates),
      "declared_partition_bytes_sum_known":sum(by_date[d].get("declared_partition_bytes",0) for d in dates),
    }

coverage={"kamino":summarize(KAMINO_START),"save11":summarize(SAVE11_START)}

# Footer-only schema inspection for one file on each exact start date.
schema_samples={}
try:
    import duckdb
    con=duckdb.connect()
    try:
        con.execute("INSTALL httpfs")
    except Exception:
        pass
    con.execute("LOAD httpfs")
    for label,start in [("kamino",KAMINO_START),("save11",SAVE11_START)]:
        rec=by_date[start.isoformat()]
        url=rec.get("first_file_url")
        srec={"date":start.isoformat(),"file_url":url}
        if not url:
            srec["status"]="NO_FILE"
            schema_samples[label]=srec
            continue
        try:
            # parquet_schema reads metadata/footer, not transaction rows.
            data=con.execute("SELECT * FROM parquet_schema(?)",[url]).fetchdf()
            cols=[str(c) for c in data.columns]
            records=data.to_dict(orient="records")
            # JSON-safe normalization.
            clean=[]
            for rr in records:
                clean.append({k:(None if v is None else str(v)) for k,v in rr.items()})
            srec["status"]="SCHEMA_READ_PASS"
            srec["columns"]=cols
            srec["parquet_schema"]=clean
            blob=" ".join(" ".join(str(v) for v in rr.values()) for rr in clean).lower()
            terms={
              "signature": any(t in blob for t in ["signature","signatures"]),
              "slot_or_block": any(t in blob for t in ["slot","block_id","block_timestamp","blocktime","block_time"]),
              "transaction_or_message": any(t in blob for t in ["transaction","message","account_keys","accountkeys"]),
              "outer_instruction": "instruction" in blob,
              "inner_instruction": any(t in blob for t in ["inner_instruction","innerinstructions","inner instructions"]),
              "status_or_error": any(t in blob for t in ["status","err","error","meta"]),
              "raw_or_json_payload": any(t in blob for t in ["json","bytes","blob","binary","data"]),
            }
            srec["capability_terms"]=terms
        except Exception as e:
            srec["status"]="SCHEMA_READ_BLOCKED"
            srec["error"]=type(e).__name__
            srec["detail"]=str(e)[:1000]
        schema_samples[label]=srec
except Exception as e:
    schema_samples["global_error"]={"error":type(e).__name__,"detail":str(e)[:1000]}

full_coverage=all(not coverage[k]["missing_or_empty_dates"] for k in ("kamino","save11"))
schema_reads=all(schema_samples.get(k,{}).get("status")=="SCHEMA_READ_PASS" for k in ("kamino","save11"))

# We deliberately do not auto-upgrade schema sufficiency to PASS from keyword matching.
# Human/explicit adjudication must verify inner/CPI recoverability from the nested schema.
if not full_coverage:
    classification="SOLARCHIVE_EVENT_CENSUS_ROUTE_PARTIAL"
elif not schema_reads:
    classification="SOLARCHIVE_EVENT_CENSUS_ROUTE_BLOCKED"
else:
    classification="SOLARCHIVE_EVENT_CENSUS_ROUTE_SCHEMA_REVIEW_REQUIRED"

receipt={
  "schema_version":"0.1",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "source":"solarchive.org",
  "source_root":BASE,
  "probe_timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z"),
  "coverage":coverage,
  "schema_samples":schema_samples,
  "daily_index_rows":rows,
  "firewall":{
    "transaction_rows_read":False,
    "parquet_footer_only":True,
    "prices":False,"returns":False,"pnl":False,"direction":False,
    "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
    "live_trading":False,"orders":False,"wallets":False,
    "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False
  }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({
 "classification":classification,
 "kamino":coverage["kamino"],
 "save11":coverage["save11"],
 "schema_status":{k:v.get("status") for k,v in schema_samples.items() if isinstance(v,dict)}
},indent=2,sort_keys=True))

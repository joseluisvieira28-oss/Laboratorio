#!/usr/bin/env python3
"""One-off publicly advertised FREE sample coverage audit, no login or payment.
No trading or wallet aggregation. Never mistake one sample day for an edge.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent;OUT=HERE/"sample_results"
API="https://huggingface.co/api/datasets/liquidvision/crypto-derivatives-sample/tree/main?recursive=true"
BASE="https://huggingface.co/datasets/liquidvision/crypto-derivatives-sample/resolve/main/"
def get(url,max_bytes):
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQMAP001-FreeSample-Audit/1.0",
                                              "Accept":"application/json,text/csv,text/plain"})
    with urllib.request.urlopen(req,timeout=35) as f:
        raw=f.read(max_bytes+1)
    end=dt.datetime.now(dt.timezone.utc).isoformat()
    if len(raw)>max_bytes:raise ValueError("MAX_FREE_SAMPLE_BYTES_EXCEEDED")
    return raw,{"url":url,"start_utc":start,"end_utc":end,"bytes":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest()}

def audit_csv(raw):
    text=raw.decode("utf-8-sig","replace")
    reader=csv.DictReader(io.StringIO(text))
    fields=reader.fieldnames or []
    rows=0;empty=0;dates={}; symbols={};nulls={}
    # No user account identifiers retained or shipped in sample results.
    named=[x for x in fields if any(s in x.lower() for s in ("time","date","timestamp","coin","symbol","liq","price","side","size","value","ts"))]
    interesting=named[:24]
    first_safe=None
    for row in reader:
        rows+=1
        if rows==1:first_safe={k:row.get(k) for k in interesting if not any(p in k.lower() for p in ("wallet","account","user","address"))}
        for key in interesting:
            val=row.get(key)
            if not val:
                nulls[key]=nulls.get(key,0)+1;continue
            if key.lower()=="ts" or any(t in key.lower() for t in ("time","date")):
                if key not in dates:dates[key]={"first":val,"last":val,"sample_uniques":set()}
                d=dates[key];d["first"]=min(d["first"],val);d["last"]=max(d["last"],val)
                if len(d["sample_uniques"])<10000:d["sample_uniques"].add(val)
            if any(t in key.lower() for t in ("coin","symbol")):
                symbols[(key,val)]=symbols.get((key,val),0)+1
    for d in dates.values():d["n_unique_capped"]=len(d.pop("sample_uniques"))
    return {"rows":rows,"columns":fields,"timing":dates,
            "top_symbols":[{"column":k[0],"value":k[1],"count":v} for k,v in sorted(symbols.items(),key=lambda x:-x[1])[:20]],
            "nonempty_column_coverage":{k:rows-nulls.get(k,0) for k in interesting},
            "first_safe_example":first_safe}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"experiment":"LIQMAP-DIAMANTE-001 sample availability feasibility",
       "no_trading":True,"no_payments":True,"not_historical_model_backtest":True,
       "source":"public LiquidVision HF free sample","status":"SOURCE_BLOCKED","receipts":[],"files":{}}
    try:
        tree,meta=get(API,2_000_000);report["receipts"].append(meta)
        allfiles=json.loads(tree)
        candidates=[x.get("path") for x in allfiles if x.get("type")=="file"
            and (x.get("path","").endswith("hl_positions_sample.csv") or
                 x.get("path","").endswith("liquidations_sample.csv"))]
        report["files_in_public_tree"]=candidates
        for path in candidates:
            url=BASE+urllib.parse.quote(path,safe="/")
            try:
                raw,meta=get(url,40_000_000)
                report["receipts"].append(meta)
                report["files"][path]={"status":"SOURCE_PASS",**audit_csv(raw)}
            except Exception as e:
                report["files"][path]={"status":"SOURCE_BLOCKED","error":str(e)}
        if not candidates:raise ValueError("FREE_SAMPLE_PATHS_NOT_FOUND")
        report["status"]="SAMPLE_METADATA_PASS" if all(
            r["status"]=="SOURCE_PASS" for r in report["files"].values()) else "PARTIAL_SOURCE_BLOCKED"
    except Exception as e:
        report["error"]=type(e).__name__+": "+str(e)
    (OUT/"FREE_SAMPLE_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    lines=["# LIQMAP-001 public actual-position sample feasibility","",
     "This tests whether FREE independent positions with EXCHANGE-REPORTED liquidation prices can be timestamped.",
     "No historical mapping predictivity claimed; point-in-time sample may be ONE DAY only.",
     "Source HTTP and SHA256 per response in FREE_SAMPLE_AUDIT.json.","",
     "Status: "+report["status"]]
    for path,f in report["files"].items():
        lines+=["","## "+path,"Status: "+f["status"],
            "Rows: "+str(f.get("rows","unavailable")),
            "Timestamp span: "+str(f.get("timing","unavailable"))[:1500]]
    if report.get("error"):lines+=["",report["error"]]
    (OUT/"FREE_SAMPLE_REPORT.md").write_text("\n".join(lines)+"\n")
    print("FREE_SAMPLE_FEASIBILITY",report["status"],
          [(k,x["status"],x.get("rows")) for k,x in report["files"].items()],flush=True)
    if report["status"]!="SAMPLE_METADATA_PASS":raise RuntimeError(report["status"])
if __name__=="__main__":main()

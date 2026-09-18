#!/usr/bin/env python3
import hashlib, json, re, sys, time
from pathlib import Path
import requests

ROOT=Path("research/binance_premium_compression")
AUTH=json.loads((ROOT/"BPC_SOURCE_AUTHORITY_V0_1.json").read_text())
OUT=Path("artifacts/binance_premium_compression_source_v01")
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://data.binance.vision"
S=requests.Session()
S.headers.update({"User-Agent":"SRC-Crypto-Lab-BPC-Source/0.1","Accept":"text/plain,*/*"})
HEX64=re.compile(r"^[0-9a-fA-F]{64}$")

def sha(b): return hashlib.sha256(b).hexdigest()

def months(a,b):
    y,m=map(int,a.split("-")); ey,em=map(int,b.split("-"))
    while (y,m)<=(ey,em):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13:y+=1;m=1

def request_checksum(path):
    url=f"{BASE}/{path}.CHECKSUM"
    last=None
    for attempt,wait in enumerate((1,2,4)):
        try:
            r=S.get(url,timeout=30)
            raw=r.content
            rc={"url":url,"status":r.status_code,"bytes":len(raw),"sha256_body":sha(raw)}
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f"HTTP {r.status_code} {url}")
                if attempt<2: time.sleep(wait); continue
            if r.status_code!=200:
                return None,rc
            line=raw.decode("utf-8","replace").strip().split()
            if len(line)<2 or not HEX64.match(line[0]):
                rc["valid_checksum_line"]=False
                return None,rc
            expected=path.rsplit("/",1)[-1]
            name=line[-1].lstrip("*")
            rc["valid_checksum_line"]=(name==expected)
            rc["archive_sha256"]=line[0].lower()
            rc["archive_name"]=name
            return (line[0].lower() if rc["valid_checksum_line"] else None),rc
        except requests.RequestException as e:
            last=e
            if attempt<2: time.sleep(wait); continue
            raise
    raise last or RuntimeError("unreachable")

def main():
    result={
      "lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":None,
      "access_2025":False,"access_2026":False,"market_zip_opened":False,
      "prices_opened":False,"premium_values_opened":False,"returns_opened":False,"pnl_opened":False,
      "live_trading":False,"exchange_mutation":False,"merge_to_main":False
    }
    receipts=[]; missing=[]; invalid=[]
    try:
        ms=list(months(AUTH["source"]["start_month"],AUTH["source"]["end_month"]))
        if any(x.startswith("2025-") or x.startswith("2026-") for x in ms):
            raise RuntimeError("PROTECTED_MONTH_IN_SOURCE_WINDOW")
        for ds in AUTH["source"]["required_datasets"]:
            for sym in AUTH["source"]["symbols"]:
                for ym in ms:
                    path=ds["path_template"].replace("{SYMBOL}",sym).replace("{YYYY-MM}",ym)
                    dg,rc=request_checksum(path)
                    rc.update({"dataset":ds["id"],"symbol":sym,"month":ym,"path":path})
                    receipts.append(rc)
                    if rc.get("status")!=200: missing.append(path)
                    elif dg is None: invalid.append(path)
                print(f"SOURCE_PROGRESS {ds['id']} {sym} {len(ms)}/{len(ms)}",flush=True)
        expected=AUTH["source_gates"]["expected_dataset_symbol_month_receipts"]
        valid_status=sum(1 for r in receipts if r.get("status")==200)
        valid_line=sum(1 for r in receipts if r.get("valid_checksum_line") is True)
        checks={
          "receipt_count_eq_expected":len(receipts)==expected,
          "checksum_http_200_fraction_eq":(valid_status/expected if expected else 0)==AUTH["source_gates"]["checksum_http_200_fraction"],
          "valid_sha256_line_fraction_eq":(valid_line/expected if expected else 0)==AUTH["source_gates"]["valid_sha256_line_fraction"],
          "protected_year_accesses_eq":True
        }
        cls=AUTH["classifications"]["pass"] if all(checks.values()) else AUTH["classifications"]["insufficient"]
        result.update({
          "classification":cls,
          "months_per_symbol":len(ms),
          "receipt_count":len(receipts),
          "http_200_count":valid_status,
          "valid_checksum_count":valid_line,
          "missing_count":len(missing),
          "invalid_checksum_count":len(invalid),
          "gate_checks":checks,
          "receipt_manifest_sha256":sha(json.dumps(receipts,sort_keys=True).encode()),
          "missing_paths":missing,
          "invalid_checksum_paths":invalid
        })
    except Exception as e:
        txt=repr(e)
        result["classification"]=AUTH["classifications"]["provenance_failure"] if "PROTECTED" in txt else AUTH["classifications"]["technical_failure"]
        result["error"]=txt
    p=OUT/"source_result.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (OUT/"manifest.json").write_text(json.dumps({
      "authority_sha256":sha((ROOT/"BPC_SOURCE_AUTHORITY_V0_1.json").read_bytes()),
      "result_sha256":sha(p.read_bytes())
    },indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 2 if result["classification"] in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 0

if __name__=="__main__":
    sys.exit(main())

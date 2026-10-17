"""Read ONLY already published immutable Actions 39026521571 V03B JSON artifacts.

No venue GETs, no additional bookTicker market fetch, no 2026 or trades.
"""
import argparse,collections,hashlib,json
from pathlib import Path

EXPECTED={"SOLUSDT":33,"BNBUSDT":6}

def audit_folder(base):
    out={}
    for symbol,expected in EXPECTED.items():
        files=list((base/symbol).rglob("ALL_ORIGINAL_ELIGIBLE_L1_RECEIPTS.json"))
        if len(files)!=1:raise ValueError("ORIGINAL_RECEIPT_NOT_UNIQUE:"+symbol)
        f=files[0];r=json.loads(f.read_text(encoding="utf-8"))
        if r.get("count")!=expected or r.get("symbol")!=symbol or r.get("trading_authority")!="NONE":
            raise ValueError("CANONICAL_FULL_DENOMINATOR_NOT_MATCHED")
        source_err=collections.Counter()
        bad_dates=[]
        for item in r["source_files"]:
            if item["status"]=="SOURCE_BLOCKED":
                reason=item.get("reason","UNSPECIFIED")
                source_err[reason]+=1
                bad_dates.append({"day":item["day"],"reason":reason})
        out[symbol]={"source_artifact_sha256":hashlib.sha256(f.read_bytes()).hexdigest(),
                     "expected_trades":expected,
                     "quoted_fresh":r["counts"].get("BOOK_QUOTE_CAUSAL_CANDIDATE",0)+r["counts"].get("TOP_OF_BOOK_SIZE_INSUFFICIENT",0),
                     "size_sufficient":r["counts"].get("BOOK_QUOTE_CAUSAL_CANDIDATE",0),
                     "source_error_classes":dict(sorted(source_err.items())),
                     "source_blocked_dates":bad_dates,
                     "true_L2_book_or_broker_fills_proven":False}
    return {"status":"V03B_ARTIFACT_ONLY_ROOT_CAUSE_NO_MARKET_RERUN",
            "source_run":39026521571,"summary":out,
            "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifacts-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    doc=audit_folder(a.artifacts_dir)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"L1_MISSING_SOURCE_ROOTCAUSE.json").write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    print("ROOT_CAUSE_READOUT",json.dumps(doc,sort_keys=True))
if __name__=="__main__":
    main()

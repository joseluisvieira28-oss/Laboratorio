"""SOURCE-ONLY forensic for checksummed public missing SOL/XRP futures 5m bars."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
from research.convex_multialt_4tf_20261013.multialt_matrix import (
    fetch_archive, MONTHS, START_PRICE, START, END
)
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src

STEP=300000

def diagnose(symbol):
    if symbol not in ("SOLUSDT","XRPUSDT"):
        raise ValueError("NON_FROZEN_SOURCE_PROBE_SYMBOL")
    buckets=[]
    gaps=[]
    prev_t=None
    total=0
    for mo in MONTHS:
        rows,manifest=fetch_archive(symbol,"5m",mo)
        b=src.candles(rows,STEP)
        ordered=sorted(b)
        tstart=int(datetime(int(mo[:4]),int(mo[5:]),1,tzinfo=timezone.utc).timestamp()*1000)
        y,m=int(mo[:4]),int(mo[5:])
        y1,m1=(y+1,1) if m==12 else (y,m+1)
        tend=int(datetime(y1,m1,1,tzinfo=timezone.utc).timestamp()*1000)
        if any(t<tstart or t>=tend for t in ordered):
            raise ValueError("SOURCE_WRONG_MONTH")
        expected=(tend-tstart)//STEP
        missing=[t for t in range(tstart,tend,STEP) if t not in b]
        buckets.append({"month":mo,"expected":expected,"observed":len(b),
                        "missing":len(missing),"first":ordered[0] if ordered else None,
                        "last":ordered[-1] if ordered else None,"zip_sha256":manifest["sha256_zip"]})
        if missing:
            start=last=missing[0]
            for t in missing[1:]:
                if t!=last+STEP:
                    gaps.append({"start":start,"end_exclusive":last+STEP,
                                 "bars":(last-start)//STEP+1,"warmup_only":last<START})
                    start=t
                last=t
            gaps.append({"start":start,"end_exclusive":last+STEP,
                         "bars":(last-start)//STEP+1,"warmup_only":last<START})
        total+=len(b)
        print("SOURCE_DIAG_MONTH",symbol,mo,"observed",len(b),"expected",expected,flush=True)
    missing_total=sum(b["missing"] for b in buckets)
    economic_missing=sum(g["bars"] for g in gaps if not g["warmup_only"])
    warmup_missing=missing_total-economic_missing
    return {"symbol":symbol,"observed":total,"expected":(END-START_PRICE)//STEP,
            "missing_total":missing_total,"economic_missing":economic_missing,
            "warmup_missing":warmup_missing,"month_records":buckets,"gap_groups":gaps,
            "classification":"WARMUP_ONLY_PRE_2021" if warmup_missing>0 and economic_missing==0
                else "ECONOMIC_WINDOW_2021_25_MISSING" if economic_missing else "COMPLETE_SOURCE",
            "performance_outcomes_used":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=("SOLUSDT","XRPUSDT"))
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    result={"symbol":a.symbol,"status":"SOURCE_BLOCKED"}
    try:
        result.update(diagnose(a.symbol))
        result["status"]="SOURCE_AUDIT_VALID"
    except Exception as e:result["reason"]=f"{type(e).__name__}:{e}"
    (a.output_dir/"SOURCE_DIAGNOSTIC.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("SOURCE_AUDIT_FINAL",json.dumps({k:v for k,v in result.items() if k not in ("month_records",)},sort_keys=True),flush=True)
    if result["status"]!="SOURCE_AUDIT_VALID":raise SystemExit(2)
if __name__=="__main__":main()

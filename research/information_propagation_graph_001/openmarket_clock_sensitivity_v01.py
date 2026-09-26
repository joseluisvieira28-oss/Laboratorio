#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from huggingface_hub import snapshot_download

REPO="gregyoung14/openmarket-btc-polymarket"
REV="74502466d1a7cef56395bfd8d0b465fbebc849cf"
OFFSETS=[-1000,-500,-250,-100,-50,0,50,100,250,500,1000]
OUT=Path("artifacts/ipg001_openmarket_clock_sensitivity_v01.json")

root=Path(snapshot_download(repo_id=REPO,repo_type="dataset",revision=REV,allow_patterns=["unified/lag_pairs_ms/**/*.parquet"]))
files=sorted((root/"unified"/"lag_pairs_ms").rglob("*.parquet"))
arrs=[]
for p in files:
    t=pq.read_table(p,columns=["lead_lag_ms"])
    a=t["lead_lag_ms"].to_numpy(zero_copy_only=False)
    a=a[np.isfinite(a)].astype(np.int64,copy=False)
    arrs.append(a)
arr=np.concatenate(arrs) if arrs else np.array([],dtype=np.int64)
base=float(np.percentile(arr,50)) if len(arr) else float("nan")
rows=[];exact=True
for off in OFFSETS:
    shifted=arr+off
    med=float(np.percentile(shifted,50))
    p5=float(np.percentile(shifted,5));p95=float(np.percentile(shifted,95))
    exact=exact and abs(med-(base+off))<=1e-9
    rows.append({"offset_ms":off,"median_ms":med,"p5_ms":p5,"p95_ms":p95,
                 "share_positive":float(np.mean(shifted>0)),"share_negative":float(np.mean(shifted<0))})
negative_interpretation=any(r["median_ms"]<0 for r in rows)
positive_interpretation=any(r["median_ms"]>0 for r in rows)
passed=exact and negative_interpretation and positive_interpretation and len(arr)==2936031
receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001","stage":"OPENMARKET_CLOCK_OFFSET_SENSITIVITY_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),"dataset_repo":REPO,"revision":REV,
 "n":int(len(arr)),"base_median_ms":base,"offset_grid_ms":OFFSETS,"rows":rows,
 "shift_identity_exact":exact,"negative_direction_interpretation_present":negative_interpretation,
 "positive_direction_interpretation_present":positive_interpretation,
 "interpretation":"CLOCK_OFFSET_SENSITIVE",
 "classification":"NEGATIVE_CONTROL_CLOCK_SENSITIVITY_PASS" if passed else "NEGATIVE_CONTROL_CLOCK_SENSITIVITY_FAIL",
 "predictive_analysis_performed":False,"ipg_market_outcomes_opened":False,"pnl_opened":False,"mutation":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not passed:raise SystemExit(2)

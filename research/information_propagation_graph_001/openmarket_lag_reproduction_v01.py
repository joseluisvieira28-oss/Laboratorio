#!/usr/bin/env python3
import json,math
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from huggingface_hub import snapshot_download

REPO="gregyoung14/openmarket-btc-polymarket"
REV="74502466d1a7cef56395bfd8d0b465fbebc849cf"
OUT=Path("artifacts/ipg001_openmarket_lag_reproduction_v01.json")

root=Path(snapshot_download(repo_id=REPO,repo_type="dataset",revision=REV,allow_patterns=["full/lag_pairs_ms/**/*.parquet"]))
files=sorted((root/"full"/"lag_pairs_ms").rglob("*.parquet"))
chunks=[];violations=0;rows_raw=0
for p in files:
    t=pq.read_table(p,columns=["lead_lag_ms","binance_source_ts_ms","polymarket_source_ts_ms"])
    lag=t["lead_lag_ms"].to_numpy(zero_copy_only=False)
    b=t["binance_source_ts_ms"].to_numpy(zero_copy_only=False)
    pm=t["polymarket_source_ts_ms"].to_numpy(zero_copy_only=False)
    rows_raw+=len(lag)
    mask=np.isfinite(lag)&np.isfinite(b)&np.isfinite(pm)
    lag=lag[mask].astype(np.int64,copy=False);b=b[mask].astype(np.int64,copy=False);pm=pm[mask].astype(np.int64,copy=False)
    violations+=int(np.count_nonzero(lag!=(pm-b)))
    chunks.append(lag)
arr=np.concatenate(chunks) if chunks else np.array([],dtype=np.int64)
if len(arr):
    med=float(np.percentile(arr,50));p5=float(np.percentile(arr,5));p95=float(np.percentile(arr,95))
else:
    med=p5=p95=float("nan")
published={"n":2936031,"median_ms":16,"p5_ms":-186,"p95_ms":316}
reproduced={"n":int(len(arr)),"median_ms":med,"p5_ms":p5,"p95_ms":p95}
passed=(violations==0 and len(arr)==published["n"] and round(med)==16 and round(p5)==-186 and round(p95)==316)
receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001",
 "stage":"OPENMARKET_UNIFIED_LAG_REPRODUCTION_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "dataset_repo":REPO,"revision":REV,
 "parquet_files":len(files),"raw_rows":rows_raw,
 "lead_lag_identity_violations":violations,
 "published":published,"reproduced":reproduced,
 "classification":"NEGATIVE_CONTROL_LAG_REPRODUCTION_PASS" if passed else "NEGATIVE_CONTROL_LAG_REPRODUCTION_FAIL",
 "sampling":False,
 "ipg_market_outcomes_opened":False,"pnl_opened":False,"mutation":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not passed: raise SystemExit(2)

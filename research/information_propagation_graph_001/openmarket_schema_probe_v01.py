#!/usr/bin/env python3
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_download
import pyarrow.parquet as pq

REPO="gregyoung14/openmarket-btc-polymarket"
REV="74502466d1a7cef56395bfd8d0b465fbebc849cf"
OUT=Path("artifacts/ipg001_openmarket_schema_probe_v01.json")
api=HfApi()
info=api.dataset_info(REPO,revision=REV,files_metadata=True)
cands=[]
for s in info.siblings or []:
    path=getattr(s,"rfilename",None)
    size=getattr(s,"size",None)
    if isinstance(path,str) and path.startswith("full/lag_pairs_ms/") and path.endswith(".parquet") and isinstance(size,int) and size>=100000:
        cands.append((path,size))
cands.sort()
if not cands: raise SystemExit("NO_DETERMINISTIC_FIXTURE")
path,manifest_size=cands[0]
local=hf_hub_download(repo_id=REPO,repo_type="dataset",filename=path,revision=REV)
raw=Path(local).read_bytes()
pf=pq.ParquetFile(local)
schema=[]
for i in range(pf.metadata.num_columns):
    col=pf.metadata.schema.column(i)
    schema.append({"name":col.name,"physical_type":str(col.physical_type),"logical_type":str(col.logical_type)})
receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001",
 "stage":"OPENMARKET_NEGATIVE_CONTROL_SCHEMA_FIXTURE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "dataset_repo":REPO,"revision":REV,
 "selection_rule":"lexicographically first full/lag_pairs_ms/*.parquet with manifest size >=100000",
 "selected_path":path,"manifest_size":manifest_size,"downloaded_size":len(raw),
 "file_sha256":hashlib.sha256(raw).hexdigest(),
 "num_rows":pf.metadata.num_rows,"num_row_groups":pf.metadata.num_row_groups,
 "schema":schema,
 "classification":"SCHEMA_FIXTURE_PASS",
 "row_data_analysis_performed":False,
 "predictive_analysis_performed":False,
 "market_outcomes_opened":False,"mutation":False,"pnl_opened":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

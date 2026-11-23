#!/usr/bin/env python3
"""DIGUI-008 source inspection: download only source files, no trades, no orders."""
import hashlib, json, pathlib
from huggingface_hub import HfApi, hf_hub_download
import pyarrow.parquet as pq

DATASET="Slinky21/Pumpfun_Memecoin_Corpus"
p=pathlib.Path("digui008-evidence")
p.mkdir(exist_ok=True)
info=HfApi().repo_info(DATASET,repo_type="dataset")
revision=info.sha
out={"dataset":DATASET,"revision":revision,"files":{}}
for name in ("tokens.parquet","postgard_outcomes.parquet","migrations.parquet"):
    path=hf_hub_download(DATASET,name,repo_type="dataset",revision=revision)
    tbl=pq.ParquetFile(path)
    raw=pathlib.Path(path).read_bytes()
    summary={"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
         "rows":tbl.metadata.num_rows,"schema":str(tbl.schema),
         "columns":tbl.schema.names}
    preview=tbl.read_row_group(0).slice(0,3).to_pylist()
    # no wallet addresses or creator identities exported in results
    summary["preview_sanitized"]=[{
        k:(str(v)[:70] if v is not None else None)
        for k,v in rec.items() if not any(z in k.lower() for z in ["address","wallet","creator","mint","signature","token_name","symbol"])} for rec in preview]
    out["files"][name]=summary
    print("INSPECT",name,"rows",summary["rows"],"bytes",summary["bytes"],"sha256",summary["sha256"],flush=True)
    print("COLUMNS",name,json.dumps(summary["columns"]),flush=True)
(p/"schema.json").write_text(json.dumps(out,indent=2,default=str),encoding="utf-8")
print("SOURCE_INSPECTION_COMPLETE",json.dumps({"revision":revision,"sizes":{k:v['rows'] for k,v in out['files'].items()}}),flush=True)

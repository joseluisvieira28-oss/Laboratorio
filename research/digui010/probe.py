#!/usr/bin/env python3
"""DIGUI-010 verified historical pool-liquidity source schema + timestamp quality.
Read-only, no orders or secrets; pinned immutable HF dataset revision.
"""
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pandas as pd
import json, hashlib, collections, time
REV="13bec2bf3089d56d50c35e602616d1b993bb37f5"
REPO="Slinky21/Pumpfun_Memecoin_Corpus"
OUT=Path("digui010-evidence");OUT.mkdir(exist_ok=True)
NAMES=["postgard_snapshots.parquet","migrations.parquet","postgard_outcomes.parquet"]
info=HfApi().repo_info(REPO,repo_type="dataset",revision=REV,files_metadata=True)
lookup={x.rfilename:x for x in info.siblings}
result={"revision":REV,"files":{}}
for name in NAMES:
    t=time.monotonic()
    p=Path(hf_hub_download(REPO,name,revision=REV,repo_type="dataset"))
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    expected=getattr(lookup[name].lfs,"sha256",None)
    if expected and sha!=expected:raise ValueError("SHA drift "+name)
    pf=pq.ParquetFile(p)
    cols=pf.schema.names
    sample=pf.read_row_group(0).slice(0,4).to_pylist()
    row={"bytes":p.stat().st_size,"sha256":sha,
         "rows":pf.metadata.num_rows,"row_groups":pf.metadata.num_row_groups,
         "fields":[{"name":f.name,"type":str(f.type)} for f in pf.schema_arrow],
         "preview":[{k:(str(v)[:120] if v is not None else None) for k,v in rec.items()
                     if k not in ("mint","pool_address","creator","wallet","tx_signature")} for rec in sample],
         "elapsed_s":round(time.monotonic()-t,2)}
    if name=="postgard_snapshots.parquet":
        df=pq.read_table(p,columns=cols[:min(len(cols),16)]).to_pandas()
        time_names=[x for x in cols if any(t in x.lower() for t in ["time","at","bucket"])]
        row["temporal_fields"]=time_names
        if "mint" in df:row["mints"]=int(df.mint.nunique())
        for col in time_names:
            if col not in df:continue
            v=pd.to_datetime(df[col],utc=True,errors="coerce")
            row[col+"_valid_pct"]=float(100*v.notna().mean())
            row[col+"_min"]=str(v.min())
            row[col+"_max"]=str(v.max())
    result["files"][name]=row
    print("PROBED",name,json.dumps(row,default=str)[:18000],flush=True)
(OUT/"schema_quality.json").write_text(json.dumps(result,indent=2,default=str))
print("PROBE_COMPLETE",json.dumps({"revision":REV,"rows":{k:v["rows"] for k,v in result["files"].items()},"sha":{k:v["sha256"] for k,v in result["files"].items()}}),flush=True)

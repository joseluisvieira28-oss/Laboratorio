#!/usr/bin/env python3
"""DIGUI-009 first check: pinned raw trade/snapshot file metadata and parquet schema.
No keys, orders or market action. Fall back gracefully when remote parquet range reads fail.
"""
from huggingface_hub import HfApi, HfFileSystem
import pyarrow.parquet as pq
import json, time, hashlib, os
from pathlib import Path

repo="Slinky21/Pumpfun_Memecoin_Corpus"
revision="13bec2bf3089d56d50c35e602616d1b993bb37f5"
out=Path("digui009-evidence");out.mkdir(exist_ok=True)
info=HfApi().repo_info(repo,repo_type="dataset",revision=revision,files_metadata=True)
meta={}
for item in info.siblings:
    if item.rfilename in ("trades.parquet","snapshots.parquet","tokens.parquet"):
        meta[item.rfilename]={"bytes":item.size,"lfs":str(getattr(item,"lfs",None))[:250]}
print("SOURCE_METADATA",json.dumps(meta),flush=True)
fs=HfFileSystem()
for name in ("trades.parquet","snapshots.parquet"):
    path=f"datasets/{repo}@{revision}/{name}"
    try:
        t0=time.time()
        with fs.open(path,"rb") as f:
            pf=pq.ParquetFile(f)
            columns=pf.schema.names
            fields=[{"name":x.name,"type":str(x.type)} for x in pf.schema_arrow]
            preview=pf.read_row_group(0).slice(0,3).to_pylist()
        clean=[]
        for rec in preview:
            clean.append({k:str(v)[:100] for k,v in rec.items() if not any(w in k.lower() for w in ("wallet","address","mint","signature","creator"))})
        meta[name].update({"rows":pf.metadata.num_rows,"row_groups":pf.metadata.num_row_groups,
          "fields":fields,"preview":clean,"remote_elapsed_s":round(time.time()-t0,2),
          "schema_read_ok":True})
        print("PARQUET_SCHEMA",name,json.dumps({"rows":pf.metadata.num_rows,"row_groups":pf.metadata.num_row_groups,"fields":fields,"preview":clean})[:17000],flush=True)
    except Exception as e:
        meta[name]["error"]=repr(e)[:350]
        print("PARQUET_REMOTE_READ_BLOCKED",name,meta[name]["error"],flush=True)
(out/"schema_probe.json").write_text(json.dumps({"sha":revision,"files":meta},indent=2,default=str))

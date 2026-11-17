#!/usr/bin/env python3
"""DIGUI-009: audit exact public parquet shards, schema and timestamp fields. No trades."""
import json,time
from pathlib import Path
import pyarrow.parquet as pq
from huggingface_hub import HfApi,HfFileSystem
repo="Slinky21/Pumpfun_Memecoin_Corpus"
revision="13bec2bf3089d56d50c35e602616d1b993bb37f5"
out=Path("digui009-evidence");out.mkdir(exist_ok=True)
info=HfApi().repo_info(repo,repo_type="dataset",revision=revision,files_metadata=True)
names=sorted(s.rfilename for s in info.siblings if s.rfilename.startswith("trades/") and s.rfilename.endswith(".parquet"))
meta={s.rfilename:{"bytes":s.size,"lfs_sha256":getattr(getattr(s,"lfs",None),"sha256",None)} for s in info.siblings if s.rfilename in names or s.rfilename in ("snapshots.parquet","tokens.parquet")}
print("TRADE_SHARDS",json.dumps({"count":len(names),"total_bytes":sum(meta[n]["bytes"] or 0 for n in names),"names":names}),flush=True)
fs=HfFileSystem()
for name in ([names[0],names[-1]] if names else [])+["snapshots.parquet"]:
    t0=time.time()
    try:
        path=f"datasets/{repo}@{revision}/{name}"
        with fs.open(path,"rb") as f:
            pf=pq.ParquetFile(f)
            col=pf.schema.names
            sample=pf.read_row_group(0, columns=col[:min(8,len(col))]).slice(0,3).to_pylist()
            stats={"rows":pf.metadata.num_rows,"rowgroups":pf.metadata.num_row_groups,
                   "schema":[{"name":a.name,"type":str(a.type)} for a in pf.schema_arrow],
                   "preview":[{k:str(v)[:80] for k,v in rec.items() if not any(t in k.lower() for t in ("wallet","mint","signature"))} for rec in sample],
                   "elapsed_s":round(time.time()-t0,1)}
        meta.setdefault(name,{})["probe"]=stats
        print("SCHEMA",name,json.dumps(stats)[:12000],flush=True)
    except Exception as e:
        meta.setdefault(name,{})["probe_error"]=repr(e)[:500]
        print("PROBE_BLOCKED",name,repr(e)[:500],flush=True)
(out/"schema_probe.json").write_text(json.dumps({"revision":revision,"shards":names,"files":meta},indent=2))
if not names:raise RuntimeError("No trade shards found")

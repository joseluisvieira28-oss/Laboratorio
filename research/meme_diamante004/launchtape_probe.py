#!/usr/bin/env python3
"""License-respecting source-only schema probe. Never copies raw events into output."""
import gzip,hashlib,json,collections,sys
from pathlib import Path
p=Path(sys.argv[1])
k=collections.Counter();typ=collections.Counter();times=collections.defaultdict(lambda:[10**20,0,0]);n=0;bad=0
ex=[]
with gzip.open(p,"rt",encoding="utf8") as f:
    for line in f:
        if not line.strip():continue
        try:
            x=json.loads(line)
            if not isinstance(x,dict):raise ValueError("not object")
            n+=1;k.update(x.keys())
            t=str(x.get("ev",x.get("type","unknown")))
            typ[t]+=1
            if len(ex)<3:
                ex.append({name:{"type":type(value).__name__,"sample":value if name.lower() in ("ev","type","side","pool_type") else None} for name,value in x.items()})
            mint=str(x.get("mint",x.get("token","")))
            rawts=x.get("t",x.get("timestamp",x.get("ts",x.get("timestamp_ms"))))
            if mint and isinstance(rawts,(int,float)):
                timev=float(rawts)/1000 if rawts>1e12 else float(rawts)
                b=times[mint]
                b[0]=min(b[0],timev);b[1]=max(b[1],timev);b[2]+=1
        except (ValueError,TypeError,json.JSONDecodeError):
            bad+=1
print("LAUNCHTAPE_SCHEMA="+json.dumps({"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
    "records":n,"invalid":bad,"field_frequency":dict(k.most_common(60)),
    "record_kinds":dict(typ.most_common(20)),"first_record_field_types_only":ex,
    "mint_ids_with_parseable_time":len(times),
    "mint_spans_5m":sum(v[1]-v[0]>=300 for v in times.values()),
    "mint_spans_10m":sum(v[1]-v[0]>=600 for v in times.values())}))

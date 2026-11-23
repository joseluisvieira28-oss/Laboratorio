#!/usr/bin/env python3
"""Read-only source probe; schema, SHA, coverage and basic event counts only."""
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import pathlib

def inspect(path):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    counts=collections.Counter(); shapes=collections.Counter(); eventkeys=collections.Counter()
    topkeys=collections.Counter(); first=None; examples=[]; errors=[]; n=0; events=0
    with gzip.open(path,"rt",encoding="utf-8") as h:
        for i,line in enumerate(h):
            if not line.strip():continue
            try:r=json.loads(line)
            except (ValueError,UnicodeError) as e:
                errors.append({"row":i,"error":str(e)[:80]});continue
            n+=1
            if isinstance(r,dict):
                topkeys.update(r.keys())
                if first is None: first={k:({"list_len":len(v),"item_keys":list(v[0])[:30] if v and isinstance(v[0],dict) else None} if isinstance(v,list) else {"type":type(v).__name__}) for k,v in r.items()}
                for k,v in r.items():
                    if isinstance(v,list) and v and isinstance(v[0],dict):
                        shapes[k]+=len(v)
                        eventkeys.update(v[0].keys())
                        events+=len(v)
                        if len(examples)<3:
                            ex={a:(type(b).__name__ if a.lower() in ("trader","wallet","signature","mint","creator") else str(b)[:80]) for a,b in list(v[0].items())[:20]}
                            examples.append({"container":k,"example_types_values":ex})
    return {"file":path.name,"sha256":digest,"objects":n,"event_count_nested_lists":events,
            "top_keys":dict(topkeys.most_common(30)),
            "list_sizes":dict(shapes.most_common(20)),
            "first_object_shape":first,"event_keys_first":dict(eventkeys.most_common(40)),
            "examples_masked":examples,"bad_rows":errors[:10]}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("paths",nargs="+",type=pathlib.Path)
    args=p.parse_args()
    for path in args.paths: print("DATA_PROBE_REPORT="+json.dumps(inspect(path),sort_keys=True))

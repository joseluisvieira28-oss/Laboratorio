#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_audit", HERE/"r1_scaled_ledger_audit_v01.py")
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

RANGES=[
(16490000,17119486),(17119487,17748973),(17748974,18378460),(18378461,19007946),
(19007947,19637432),(19637433,20266918),(20266919,20896404),(20896405,21525890)
]

def canon(ts):
    return json.dumps(ts, sort_keys=True, separators=(",",":"))

def main():
    assert RANGES[0][0]==base.FROM_BLOCK and RANGES[-1][1]==base.TO_BLOCK
    for i,(a,b) in enumerate(RANGES):
        assert a<=b
        if i: assert RANGES[i-1][1]+1==a

    u1="0x"+"11"*20; u2="0x"+"22"*20
    t1="0x"+"aa"*20; t2="0x"+"bb"*20
    token_meta={
      t1:{"kind":"ATOKEN","underlying":"0x"+"01"*20},
      t2:{"kind":"VARIABLE_DEBT","underlying":"0x"+"02"*20},
    }
    mono=defaultdict(lambda:defaultdict(int))
    events=[
      (u1,t1,16500000,100),(u1,t1,17119487,5),(u1,t1,17748972,-20),
      (u1,t1,19007945,17),(u1,t1,20266917,-9),(u1,t1,21525890,3),
      (u2,t2,17000000,200),(u2,t2,18378460,13),(u2,t2,19637432,-30),
      (u2,t2,20896404,11),
    ]
    for u,t,b,d in events: mono[(u,t)][b]+=d

    shards=[]
    for a,b in RANGES:
        s=defaultdict(lambda:defaultdict(int))
        for (u,t),by in mono.items():
            for bn,d in by.items():
                if a<=bn<=b: s[(u,t)][bn]+=d
        shards.append(s)

    merged=defaultdict(lambda:defaultdict(int))
    for s in shards:
        for key,by in s.items():
            for bn,d in by.items(): merged[key][bn]+=d

    mono_targets,mono_neg=base.replay_targets(mono,token_meta)
    merged_targets,merged_neg=base.replay_targets(merged,token_meta)
    if canon(mono_targets)!=canon(merged_targets) or canon(mono_neg)!=canon(merged_neg):
        raise SystemExit("SHARD_MERGE_EQUIVALENCE_FAIL")
    print(json.dumps({
      "classification":"SHARD_MERGE_EQUIVALENCE_PASS",
      "range_count":len(RANGES),
      "event_count":len(events),
      "target_count":len(mono_targets),
      "negative_count":len(mono_neg),
      "health_factor_computed":False,
      "overhang_computed":False,
      "returns_opened":False,
      "pnl_opened":False
    },sort_keys=True))
if __name__=="__main__": main()

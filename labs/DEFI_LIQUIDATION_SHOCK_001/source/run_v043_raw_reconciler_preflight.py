#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

base=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
q=base/"KAMINO_SAVE11_RAW_SAMPLE_QUEUE_V0.4.3.json"
queue={
  "kamino":{
    "mandatory_first":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
    "mandatory_last":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
    "selected_count":1,
    "distinct_successful_signatures":1,
    "entries":[{
      "signature":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
      "slot":230572965,
      "timestamp":"2023-11-17T14:48:24Z",
      "expected_path_classes":["outer"],
      "instruction_addresses":[[7]]
    }]
  },
  "save11":{
    "mandatory_first":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
    "mandatory_last":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
    "selected_count":1,
    "distinct_successful_signatures":1,
    "entries":[{
      "signature":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
      "slot":278496102,
      "timestamp":"2024-07-19T19:30:52Z",
      "expected_path_classes":["inner"],
      "instruction_addresses":[[4,0]]
    }]
  }
}
q.write_text(json.dumps(queue,indent=2,sort_keys=True)+"\n")
subprocess.run([sys.executable,str(base/"source/reconcile_sqd_census_raw_sample_v0_4_3.py")],check=True)
r=json.loads((base/"KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.4.3.json").read_text())
assert r.get("classification")=="RAW_SAMPLE_RECONCILIATION_PASS",r
assert r.get("sample_count")==2,r
assert r.get("pass_count")==2,r
assert {x["protocol"] for x in r.get("results",[])}=={"kamino","save11"}
print(json.dumps({
  "classification":"V043_RAW_RECONCILER_PREFLIGHT_PASS",
  "sample_count":r["sample_count"],
  "pass_count":r["pass_count"],
},indent=2))

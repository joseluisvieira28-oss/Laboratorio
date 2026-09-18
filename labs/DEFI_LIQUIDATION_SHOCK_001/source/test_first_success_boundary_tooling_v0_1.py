#!/usr/bin/env python3
import csv,importlib.util,json,pathlib,sys,tempfile
from datetime import datetime,timezone
HERE=pathlib.Path(__file__).resolve().parent

def load(name,fn):
    spec=importlib.util.spec_from_file_location(name,HERE/fn)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

gen=load("firstq","generate_first_success_probe_queue_v0_1.py")
adj=load("firstadj","adjudicate_first_success_probe_chunk_v0_1.py")

rows=gen.build()
assert rows
for protocol in {r["protocol"] for r in rows}:
    xs=[r for r in rows if r["protocol"]==protocol]
    assert [r["chunk_sequence"] for r in xs]==list(range(1,len(xs)+1))
    for i,r in enumerate(xs):
        s=gen.dt(r["chunk_start_utc"]);e=gen.dt(r["chunk_end_utc_exclusive"])
        assert s<e and (e-s).total_seconds()<=7*86400
        if i: assert xs[i-1]["chunk_end_utc_exclusive"]==r["chunk_start_utc"]
    assert xs[-1]["chunk_end_utc_exclusive"]=="2025-01-01T00:00:00Z"

kam=[r for r in rows if r["protocol"]=="kamino_lend"]
assert kam[0]["chunk_start_utc"]=="2023-11-17T13:25:35Z"
assert all("b1479abce2854a37" in r["active_reference_classes"] for r in kam)
assert all("b1479acce2854a37" not in r["active_reference_classes"] for r in kam)

drift=[r for r in rows if r["protocol"]=="drift_v2"]
assert all("0c2bb0539cfb750d" not in r["active_reference_classes"] for r in drift)
assert all("8e58a3a0df4b37e1" not in r["active_reference_classes"] for r in drift)

fields=[
 "protocol","family","program_id","match_name","encoding","reference_prefix_hex","source_supported_from",
 "block_slot","block_timestamp","tx_signature","instruction_index","parent_index","instruction_type","data",
 "data_prefix_8_hex","status","err","status_err_consistency","classification","instruction_location"
]
def mk(protocol,name,prefix,stamp,status,err,classification,sig="sig",parent=""):
    return {
      "protocol":protocol,"family":"x","program_id":adj.PROGRAMS[protocol],"match_name":name,
      "encoding":"anchor_discriminator_8","reference_prefix_hex":prefix,
      "source_supported_from":"2023-11-17T13:25:35Z" if protocol=="kamino_lend" else "2022-11-04T15:17:54Z",
      "block_slot":"1","block_timestamp":stamp,"tx_signature":sig,"instruction_index":"0",
      "parent_index":parent,"instruction_type":"","data":"abc","data_prefix_8_hex":prefix,
      "status":status,"err":err,
      "status_err_consistency":"SUCCESS_CONSISTENT" if status=="Success" and err=="" else "FAIL_CONSISTENT",
      "classification":classification,"instruction_location":"outer" if parent=="" else "inner"
    }

with tempfile.TemporaryDirectory() as td:
    p=pathlib.Path(td)/"x.csv"
    rr=[
      mk("kamino_lend","liquidate_obligation_and_redeem_reserve_collateral","b1479abce2854a37",
         "2023-11-18 00:00:00 UTC","Fail","err","LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED","fail"),
      mk("kamino_lend","liquidate_obligation_and_redeem_reserve_collateral","b1479abce2854a37",
         "2023-11-18 01:00:00 UTC","Success","","SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_ONCHAIN_BOUNDARY_AND_RAW_CLASS_VALIDATION","ok")
    ]
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rr)
    got=adj.load(p,"kamino_lend",adj.ts("2023-11-17T13:25:35Z"),adj.ts("2023-11-24T13:25:35Z"))
    assert len(got)==2
    succ=[r for r in got if r["classification"].startswith("SUCCESSFUL")]
    assert len(succ)==1 and succ[0]["tx_signature"]=="ok"

print("DLS_FIRST_SUCCESS_BOUNDARY_TOOLING_V01_QA_PASS")

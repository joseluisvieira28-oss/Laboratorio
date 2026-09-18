#!/usr/bin/env python3
import csv,importlib.util,pathlib,sys,tempfile
HERE=pathlib.Path(__file__).resolve().parent

def load(name,fn):
    spec=importlib.util.spec_from_file_location(name,HERE/fn)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

m=load("kamino_adj","adjudicate_kamino_corrected_smoke_v0_2.py")
fields=[
 "protocol","program_id","match_name","reference_prefix_hex","source_supported_from",
 "block_slot","block_timestamp","tx_signature","instruction_index","parent_index",
 "instruction_location","instruction_type","data","data_prefix_8_hex","status","err","classification"
]

def row(sig,status,err,cls,parent=""):
    return {
      "protocol":m.PROTOCOL,"program_id":m.PROGRAM,"match_name":m.MATCH,
      "reference_prefix_hex":m.PREFIX,"source_supported_from":m.SOURCE_FROM,
      "block_slot":"300000000","block_timestamp":"2024-12-15 12:00:00 UTC",
      "tx_signature":sig,"instruction_index":"0","parent_index":parent,
      "instruction_location":"outer" if parent=="" else "inner",
      "instruction_type":"","data":"abc","data_prefix_8_hex":m.PREFIX,
      "status":status,"err":err,"classification":cls
    }

with tempfile.TemporaryDirectory() as td:
    p=pathlib.Path(td)/"x.csv"
    rows=[
      row("sig_success","Success","","SUCCESSFUL_REFERENCE_CANDIDATE_REQUIRES_RAW_VALIDATION"),
      row("sig_fail","Fail","InstructionError","LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED","1"),
    ]
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    got=m.load(p)
    status,succ,fail,anom=m.adjudicate(got)
    assert status=="KAMINO_CORRECTED_SMOKE_CANDIDATES_FOUND_RAW_VALIDATION_REQUIRED"
    assert len(succ)==1 and len(fail)==1 and len(anom)==0

    # Retired wrong prefix must fail closed before classification.
    bad=rows[0].copy()
    bad["reference_prefix_hex"]=m.RETIRED
    bad["data_prefix_8_hex"]=m.RETIRED
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerow(bad)
    try:
        m.load(p)
        raise AssertionError("retired prefix accepted")
    except RuntimeError as e:
        assert "REFERENCE_PREFIX_MISMATCH" in str(e) or "RETIRED_PREFIX_PRESENT" in str(e)

    # Inconsistent success/error semantics cannot be silently coerced.
    weird=rows[0].copy()
    weird["err"]="unexpected"
    weird["classification"]="SUCCESSFUL_REFERENCE_CANDIDATE_REQUIRES_RAW_VALIDATION"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerow(weird)
    try:
        m.load(p)
        raise AssertionError("status/err anomaly accepted")
    except RuntimeError as e:
        assert "CLASSIFICATION_MISMATCH" in str(e)

print("DLS_KAMINO_CORRECTED_SMOKE_ADJUDICATOR_V02_QA_PASS")

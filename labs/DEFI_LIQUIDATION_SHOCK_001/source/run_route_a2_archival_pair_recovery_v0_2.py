#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_alternative_source_equivalence_v0_1 as g

LAB="DEFI-LIQUIDATION-SHOCK-001"
REFS={
 "save0c":{"slot":110526981,"sig":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V"},
 "save11":{"slot":278496102,"sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L"},
 "marginfi":{"slot":177590210,"sig":"2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK"},
 "kamino":{"slot":230572965,"sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv"}
}
ARTIFACTS={
 "save0c":{"run":36263998920,"artifact":10925546081,"name":"dls-field-enrichment-ms-save0c-202112"},
 "marginfi":{"run":36263998920,"artifact":10913369291,"name":"dls-field-enrichment-ms-marginfi-202302"},
 "kamino":{"run":36264171014,"artifact":10914381181,"name":"dls-field-enrichment-ks-kamino-202311"},
 "save11":{"run":36313729668,"artifact":10930811495,"name":"dls-save11-field-v04-save11-202407"},
 "save11_unit":{"run":36313729668,"artifact":10930621736,"name":"dls-save11-unit-v04-save11-202407"},
 "raw":{"run":36897600425,"artifact":11179957023,"name":"dls-route-a2-four-class-pair-v01"},
 "previous":{"run":36898066100,"artifact":11179999081,"name":"dls-route-a2-equivalence-v01"}
}

def load_jsons(root:Path):
    out=[]
    for p in sorted(root.rglob("*.json")):
        try: out.append((p,json.loads(p.read_text())))
        except Exception: pass
    return out

def find_sqd_row(root:Path,sig:str):
    hits=[]
    for p,x in load_jsons(root):
        if not isinstance(x,dict): continue
        for key,val in x.items():
            if isinstance(val,list):
                for r in val:
                    if isinstance(r,dict) and r.get("signature")==sig and "accounts" in r and "instruction_data_base58" in r:
                        hits.append((p,x.get("classification"),r))
    if len(hits)!=1: raise ValueError(f"sqd_row_count:{sig}:{len(hits)}")
    return hits[0]

def find_raw(root:Path,sig:str):
    hits=[]
    for p,x in load_jsons(root):
        r=x.get("result") if isinstance(x,dict) else None
        if isinstance(r,dict):
            sigs=(r.get("transaction") or {}).get("signatures") or []
            if sigs and sigs[0]==sig: hits.append((p,r))
    if len(hits)!=1: raise ValueError(f"raw_row_count:{sig}:{len(hits)}")
    return hits[0]

def find_unit(root:Path,sig:str):
    hits=[]
    for p,x in load_jsons(root):
        if not isinstance(x,dict): continue
        for key,val in x.items():
            if isinstance(val,list):
                for r in val:
                    if isinstance(r,dict) and r.get("signature")==sig and "collateral_underlying" in r:
                        hits.append((p,x.get("classification"),r))
    if len(hits)!=1: raise ValueError(f"unit_row_count:{len(hits)}")
    return hits[0]

def iso_epoch(s):
    return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def main():
    ap=argparse.ArgumentParser()
    for k in ("save0c","save11","marginfi","kamino","save11_unit","raw","previous"):
        ap.add_argument("--"+k.replace("_","-"),required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    roots={k:Path(getattr(a,k)) for k in ("save0c","save11","marginfi","kamino","save11_unit","raw","previous")}
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    cfg=g.cfg();results=[]
    for proto,ref in REFS.items():
        sqd_path,sqd_class,row=find_sqd_row(roots[proto],ref["sig"])
        raw_path,raw=find_raw(roots["raw"],ref["sig"])
        n=g.normalize(raw)
        ms=[ix for p,ix in g.matches(n,cfg) if p==proto and ix["path"]==row["instructionAddress"]]
        checks={
          "signature_exact":n["signature"]==ref["sig"]==row["signature"],
          "slot_exact":n["slot"]==ref["slot"]==row["slot"],
          "timestamp_exact":n["timestamp"]==iso_epoch(row["timestamp"]),
          "raw_success":n["err"] is None,
          "exact_match_count":len(ms)==1,
          "sqd_partition_pass":sqd_class=="FIELD_ENRICHMENT_PARTITION_PASS"
        }
        if len(ms)==1:
            ix=ms[0]
            checks.update({
              "path_exact":ix["path"]==row["instructionAddress"],
              "program_exact":ix["program"]==row["programId"],
              "accounts_exact":ix["accounts"]==row["accounts"],
              "data_exact":ix["data"]==g.b58(row["instruction_data_base58"]),
              "canonical_shape_pass":g.shape(proto,ix)
            })
            if len(row["instructionAddress"])==1:
                checks["target_path_unambiguous"]=ix["path"]==[row["instructionAddress"][0]]
            else:
                checks["target_path_unambiguous"]=ix["path"] is not None and not any(
                    e.get("outer")==row["instructionAddress"][0] and e.get("ordinal")==row["instructionAddress"][1]
                    for e in n["depth_errors"]
                )
        unit_evidence=None
        if proto=="save11" and len(ms)==1:
            up,uc,ur=find_unit(roots["save11_unit"],ref["sig"])
            pair,opt=g.unit(n,ms[0])
            u=ur["collateral_underlying"]
            expected=[[u["mint"],u["decimals"]]]
            unit_evidence={
              "unit_partition_classification":uc,
              "unit_artifact_row":str(up),
              "canonical_unit_primary":pair,
              "canonical_optional_available":opt,
              "frozen_expected_primary":expected,
              "primary_exact":pair==expected,
              "primary_source_account_exact":u["primary_source_account"]==ms[0]["accounts"][8],
              "optional_account_exact":u["optional_crosscheck_account"]==ms[0]["accounts"][2]
            }
            checks["save11_unit_pass"]=(
              uc=="KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS" and
              unit_evidence["primary_exact"] and
              unit_evidence["primary_source_account_exact"] and
              unit_evidence["optional_account_exact"]
            )
        passed=all(checks.values())
        results.append({
          "protocol":proto,"signature":ref["sig"],"slot":ref["slot"],
          "sqd_artifact":ARTIFACTS[proto],"sqd_member":str(sqd_path),
          "raw_artifact":ARTIFACTS["raw"],"raw_member":str(raw_path),
          "instruction_address":row["instructionAddress"],
          "raw_depth_errors_recorded":n["depth_errors"],
          "checks":checks,"unit_evidence":unit_evidence,"pass":passed
        })
    pair_receipt={
      "schema_version":"0.2","lab_id":LAB,
      "classification":"FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_PASS" if len(results)==4 and all(r["pass"] for r in results) else "FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_BLOCKED",
      "pass":len(results)==4 and all(r["pass"] for r in results),
      "provenance":"Exact frozen decoder REFS; pre-Discovery SQD field-enrichment artifacts paired to Helius archival RAW for same signatures; no reselection.",
      "artifact_pins":ARTIFACTS,"results":results,
      "firewall":{"economic_outcomes_opened":False,"protected_2025_acquisition":False,"prices":False,"returns":False,"pnl":False,"science_changed":False,"live_trading":False,"merge_main":False},
      "trading_authority":"NONE"
    }
    (out/"FOUR_CLASS_PAIRED_SOURCE_RECEIPT_V0.2.json").write_text(json.dumps(pair_receipt,indent=2,sort_keys=True)+"\n")
    # Finalize equivalence from latest completed six-test receipt + archival pair.
    prev_hits=[]
    for p,x in load_jsons(roots["previous"]):
        if isinstance(x,dict) and x.get("schema_version")=="0.2" and "tests" in x and x.get("lab_id")==LAB:
            prev_hits.append((p,x))
    if len(prev_hits)!=1: raise ValueError(f"previous_receipt_count:{len(prev_hits)}")
    prev_path,prev=prev_hits[0]
    required=("1_transaction_census","2_raw_fidelity","3_versioned_alt","4_cpi_instruction_address","6_save11_balance_mapping")
    fixed_tests={k:prev["tests"][k] for k in prev["tests"]}
    base_ok=all(prev["tests"][k]["status"]=="PASS" for k in required)
    prev_sem=prev["tests"]["5_frozen_semantics"]
    existing=[r for r in prev_sem.get("results",[]) if r.get("pass")]
    save0c_pair=next((r for r in results if r["protocol"]=="save0c"),None)
    combined_coverage=sorted(set(prev_sem.get("coverage",[]))|({"save0c"} if save0c_pair and save0c_pair["pass"] else set()))
    semantic_pass=(
      base_ok and all(r.get("pass") for r in prev_sem.get("results",[])) and
      save0c_pair is not None and save0c_pair["pass"] and
      combined_coverage==sorted(cfg)
    )
    fixed_tests["5_frozen_semantics"]={
      "status":"PASS" if semantic_pass else "BLOCKED","executed":True,
      "coverage":combined_coverage,"missing_classes":sorted(set(cfg)-set(combined_coverage)),
      "results":existing+[{
        "signature":save0c_pair["signature"],"protocol":"save0c",
        "path":save0c_pair["instruction_address"],
        "pass":bool(save0c_pair["pass"]),
        "provenance":"FOUR_CLASS_PAIRED_SOURCE_RECEIPT_V0.2 exact frozen pre-Discovery SQD row + canonical RAW shape"
      }] if save0c_pair else existing
    }
    blockers=[k for k,v in fixed_tests.items() if v["status"]!="PASS"]
    if not pair_receipt["pass"]: blockers.append("FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_INCOMPLETE")
    errors=list(prev.get("errors") or [])
    classification="ALTERNATIVE_SOURCE_EQUIVALENCE_PASS" if not blockers and not errors else "ALTERNATIVE_SOURCE_EQUIVALENCE_BLOCKED"
    final={
      "schema_version":"0.3","lab_id":LAB,"classification":classification,
      "blockers":blockers,"tests":fixed_tests,"errors":errors,
      "four_class_paired_evidence_v02":pair_receipt,
      "prior_equivalence_receipt":{"run":ARTIFACTS["previous"]["run"],"artifact":ARTIFACTS["previous"]["artifact"],"member":str(prev_path),"classification":prev.get("classification")},
      "adjudication_note":"V0.3 completes only missing archival source evidence. No decoder, semantics, population, threshold or economic rule changed.",
      "firewall":{"economic_outcomes_opened":False,"protected_2025_acquisition":False,"data_2026":False,"science_changed":False,"secret_values_exposed":False,"purchases":False,"live_trading":False,"merge_main":False},
      "trading_authority":"NONE"
    }
    (out/"DLS_ALTERNATIVE_SOURCE_EQUIVALENCE_RECEIPT_V0.3.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "pair_classification":pair_receipt["classification"],
      "pair_protocols":{r["protocol"]:r["pass"] for r in results},
      "semantic_coverage":combined_coverage,
      "equivalence_classification":classification,
      "blockers":blockers
    },indent=2,sort_keys=True))
    if classification!="ALTERNATIVE_SOURCE_EQUIVALENCE_PASS": raise SystemExit(2)

if __name__=="__main__": main()

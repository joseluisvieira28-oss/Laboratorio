#!/usr/bin/env python3
import argparse,json
from collections import defaultdict
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--sample-gate",required=True)
ap.add_argument("--clusters",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json")

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

sample,sp=find_one(args.sample_gate,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
errors=[]
if not sample:
    errors.append({"reason":"missing_sample_gate_receipt"})
elif sample.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
    errors.append({"reason":"sample_gate_not_pass","classification":sample.get("classification")})

cp=Path(args.clusters)
if cp.is_dir():
    hits=sorted(cp.rglob("SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"))
    cp=hits[0] if hits else cp/"SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"
if not cp.exists():
    errors.append({"reason":"missing_cluster_census","path":str(cp)})

def target_for(protocol,cls,market):
    if protocol in ("marginfi","save0c","save11","kamino"):
        if isinstance(market,str) and market.startswith("mint:") and len(market)>5:
            return market
        raise ValueError("lending_primary_identity_not_mint")
    if protocol!="drift":
        raise ValueError("unknown_protocol")
    parts=str(market).split(":")
    if cls=="liquidate_perp":
        if len(parts)==2 and parts[0]=="perp":return f"drift_perp:{int(parts[1])}"
        raise ValueError("bad_drift_perp_identity")
    if cls=="liquidate_spot":
        if len(parts)==3 and parts[0]=="spotpair":return f"drift_spot:{int(parts[1])}"
        raise ValueError("bad_drift_spot_identity")
    if cls in ("liquidate_borrow_for_perp_pnl","liquidate_perp_pnl_for_deposit"):
        if len(parts)==3 and parts[0]=="perpspot":return f"drift_perp:{int(parts[1])}"
        raise ValueError("bad_drift_perpspot_identity")
    raise ValueError("unknown_drift_class")

agg={}
row_count=0
if cp.exists():
    with cp.open("r",encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():continue
            row_count+=1
            try:r=json.loads(line)
            except Exception as e:
                errors.append({"reason":"cluster_json_parse","row":row_count,"error":str(e)});continue
            protocol=r.get("protocol");cls=r.get("instruction_class");market=r.get("primary_market_identity")
            try:target=target_for(protocol,cls,market)
            except Exception as e:
                errors.append({"reason":"target_identity_decode","row":row_count,"protocol":protocol,
                               "class":cls,"market":market,"error":str(e)});continue
            t0=r.get("t0");split=r.get("split")
            ent=agg.setdefault(target,{"target_identity":target,"contributors":set(),
                                      "first_t0":t0,"last_t0":t0,
                                      "discovery_cluster_count":0,"oos_cluster_count":0,
                                      "monthly_probe_dates":{},"contributor_counts":{}})
            ent["contributors"].add((protocol,cls))
            ck=str(protocol)+"\u241f"+str(cls)
            cc=ent["contributor_counts"].setdefault(ck,{
                "protocol":protocol,"instruction_class":cls,
                "discovery_cluster_count":0,"oos_cluster_count":0})
            if t0 and (ent["first_t0"] is None or t0<ent["first_t0"]):ent["first_t0"]=t0
            if t0 and (ent["last_t0"] is None or t0>ent["last_t0"]):ent["last_t0"]=t0
            if t0:
                month=t0[:7]
                day=t0[:10]
                prior=ent["monthly_probe_dates"].get(month)
                if prior is None or day<prior: ent["monthly_probe_dates"][month]=day
            if split=="discovery":
                ent["discovery_cluster_count"]+=1
                cc["discovery_cluster_count"]+=1
            elif split=="oos":
                ent["oos_cluster_count"]+=1
                cc["oos_cluster_count"]+=1

requirements=[]
for target,ent in sorted(agg.items()):
    contributors=[{"protocol":p,"instruction_class":c} for p,c in sorted(ent.pop("contributors"))]
    ent["monthly_probe_dates"]=[ent["monthly_probe_dates"][m] for m in sorted(ent["monthly_probe_dates"])]
    ent["contributor_counts"]=sorted(ent["contributor_counts"].values(),
                                     key=lambda x:(str(x.get("protocol")),str(x.get("instruction_class"))))
    inferential=any(
      (x.get("protocol"),x.get("class")) in {(c["protocol"],c["instruction_class"]) for c in contributors}
      and x.get("status") not in (None,"DESCRIPTIVE_ONLY_INSUFFICIENT_INDEPENDENT_N")
      for x in (sample or {}).get("subgroups") or []
    )
    requirements.append({**ent,"contributors":contributors,"inferential_dependency":bool(inferential)})

classification="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS" if not errors and requirements else "MARKET_MAPPING_REQUIREMENTS_BLOCKED_FAIL_CLOSED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "sample_gate_classification":(sample or {}).get("classification"),
 "cluster_census_path":str(cp),"cluster_row_count":row_count,
 "unique_target_count":len(requirements),"requirements":requirements,
 "source_sample_primary":(sample or {}).get("primary"),
 "source_sample_subgroups":(sample or {}).get("subgroups") or [],
 "error_count":len(errors),"errors":errors[:500],
 "frozen_authorities":["MARKET_MAPPING_REQUIREMENTS_FREEZE_V0.1.md",
                       "OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md",
                       "MARKET_DATA_SOURCE_GATE_FREEZE_V0.1.md"],
 "firewall":{"exchange_selected":False,"archive_payload_downloaded":False,"candles_opened":False,
             "prices_opened":False,"returns_computed":False,"pnl_computed":False,
             "economic_outcomes_opened":False,"protected_2025_2026_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"cluster_row_count":row_count,
                  "unique_target_count":len(requirements),"error_count":len(errors)},indent=2))
if classification!="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS":raise SystemExit(2)

#!/usr/bin/env python3
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--requirements",required=True)
ap.add_argument("--registry",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_DATA_MAPPING_REGISTRY_VALIDATION_RECEIPT_V0.1.json")

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as fh:
        for block in iter(lambda:fh.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

req,rp=find_one(args.requirements,"MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json")
reg=json.loads(Path(args.registry).read_text()) if Path(args.registry).exists() else None
errors=[]

if not req:
    errors.append({"reason":"missing_mapping_requirements"})
elif req.get("classification")!="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS":
    errors.append({"reason":"mapping_requirements_not_pass","classification":req.get("classification")})
if not reg:
    errors.append({"reason":"missing_mapping_registry"})

requirements={x["target_identity"]:x for x in (req or {}).get("requirements") or []}
rows=(reg or {}).get("mappings") or []
by_target={}
for row in rows:
    t=row.get("target_identity")
    if not t:
        errors.append({"reason":"mapping_row_missing_target","row":row});continue
    if t in by_target:
        errors.append({"reason":"duplicate_mapping_target","target_identity":t})
    by_target[t]=row

extra=sorted(set(by_target)-set(requirements))
missing=sorted(set(requirements)-set(by_target))
if extra:errors.append({"reason":"extra_mapping_targets","targets":extra})
if missing:errors.append({"reason":"missing_mapping_targets","targets":missing})

QUOTE_RANK={"USDT":0,"USD":1,"USDC":2}
direct_targets=set(); unavailable_targets=set()

for target,need in requirements.items():
    row=by_target.get(target)
    if not row:continue
    status=row.get("status")
    auth=row.get("identity_authority")
    if not isinstance(auth,list) or not auth:
        errors.append({"reason":"identity_authority_missing","target_identity":target})
    if not row.get("canonical_asset_id"):
        errors.append({"reason":"canonical_asset_id_missing","target_identity":target})

    if status=="BINANCE_DIRECT":
        direct_targets.add(target)
        required_fields=["symbol","base_asset","quote_asset","venue_metadata_authority",
                         "archive_route_template","checksum_route_template"]
        if not isinstance(row.get("current_product_metadata_expected"),bool):
            errors.append({"reason":"current_product_metadata_expected_missing","target_identity":target})
        if row.get("current_product_metadata_expected") is False and not row.get("historical_product_metadata_authority"):
            errors.append({"reason":"historical_product_authority_missing","target_identity":target})
        for fld in required_fields:
            if not row.get(fld):
                errors.append({"reason":"binance_field_missing","target_identity":target,"field":fld})
        quote=row.get("quote_asset")
        if quote not in QUOTE_RANK:
            errors.append({"reason":"unsupported_quote","target_identity":target,"quote":quote})
        elif QUOTE_RANK[quote]>0 and not row.get("higher_priority_quote_unavailable_evidence"):
            errors.append({"reason":"lower_priority_quote_without_evidence","target_identity":target,"quote":quote})
        if row.get("listing_start_utc") is None and row.get("listing_start_status")!="SOURCE_NOT_AVAILABLE":
            errors.append({"reason":"listing_boundary_missing","target_identity":target})

    elif status=="OKX_DIRECT":
        direct_targets.add(target)
        for fld in ["instrument_id","base_asset","quote_asset","venue_metadata_authority",
                    "listing_start_utc","historical_candle_route_authority","binance_unavailable_evidence"]:
            if not row.get(fld):
                errors.append({"reason":"okx_field_missing","target_identity":target,"field":fld})
        quote=row.get("quote_asset")
        if quote not in QUOTE_RANK:
            errors.append({"reason":"unsupported_quote","target_identity":target,"quote":quote})
        elif QUOTE_RANK[quote]>0 and not row.get("higher_priority_quote_unavailable_evidence"):
            errors.append({"reason":"lower_priority_quote_without_evidence","target_identity":target,"quote":quote})

    elif status=="MARKET_MAPPING_UNAVAILABLE":
        unavailable_targets.add(target)
        if not row.get("reason") or not row.get("evidence"):
            errors.append({"reason":"unavailable_without_evidence","target_identity":target})
    else:
        errors.append({"reason":"invalid_mapping_status","target_identity":target,"status":status})

# Source-only sample adequacy after deterministic mapping exclusion.
mapped_discovery=sum(int(requirements[t].get("discovery_cluster_count") or 0) for t in direct_targets if t in requirements)
mapped_oos=sum(int(requirements[t].get("oos_cluster_count") or 0) for t in direct_targets if t in requirements)
unmapped_discovery=sum(int(requirements[t].get("discovery_cluster_count") or 0) for t in unavailable_targets if t in requirements)
unmapped_oos=sum(int(requirements[t].get("oos_cluster_count") or 0) for t in unavailable_targets if t in requirements)

sample_errors=[]
if mapped_discovery<1000:
    sample_errors.append({"reason":"mapped_discovery_clusters_below_gate","observed":mapped_discovery,"required":1000})
if mapped_oos<500:
    sample_errors.append({"reason":"mapped_oos_clusters_below_gate","observed":mapped_oos,"required":500})

mapped_sub=defaultdict(lambda:{"discovery_cluster_count":0,"oos_cluster_count":0})
for t in direct_targets:
    need=requirements.get(t) or {}
    for cc in need.get("contributor_counts") or []:
        k=(cc.get("protocol"),cc.get("instruction_class"))
        mapped_sub[k]["discovery_cluster_count"]+=int(cc.get("discovery_cluster_count") or 0)
        mapped_sub[k]["oos_cluster_count"]+=int(cc.get("oos_cluster_count") or 0)

post_mapping_subgroups=[]
for sg in (req or {}).get("source_sample_subgroups") or []:
    k=(sg.get("protocol"),sg.get("class"))
    c=mapped_sub[k]
    original=sg.get("status")
    if original=="INFERENTIAL_DISCOVERY_AND_OOS":
        status=("INFERENTIAL_DISCOVERY_AND_OOS"
                if c["discovery_cluster_count"]>=200 and c["oos_cluster_count"]>=100
                else "DESCRIPTIVE_ONLY_AFTER_MARKET_MAPPING")
    elif original=="EXTERNAL_CONFIRMATORY_INFERENTIAL":
        status=("EXTERNAL_CONFIRMATORY_INFERENTIAL"
                if c["oos_cluster_count"]>=200
                else "DESCRIPTIVE_ONLY_AFTER_MARKET_MAPPING")
    else:
        status="DESCRIPTIVE_ONLY_INSUFFICIENT_INDEPENDENT_N"
    post_mapping_subgroups.append({
        "protocol":k[0],"class":k[1],"original_status":original,
        "mapped_discovery_clusters":c["discovery_cluster_count"],
        "mapped_oos_clusters":c["oos_cluster_count"],
        "post_mapping_status":status
    })

classification=("MARKET_DATA_MAPPING_REGISTRY_PASS"
                if not errors and not sample_errors
                else "MARKET_DATA_MAPPING_REGISTRY_BLOCKED_FAIL_CLOSED")

receipt={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "requirements_classification":(req or {}).get("classification"),
 "requirements_count":len(requirements),"mapping_row_count":len(rows),
 "direct_mapped_target_count":len(direct_targets),"unavailable_target_count":len(unavailable_targets),
 "missing_target_count":len(missing),"extra_target_count":len(extra),
 "post_mapping_sample":{
   "mapped_discovery_cluster_count":mapped_discovery,
   "mapped_oos_cluster_count":mapped_oos,
   "excluded_unavailable_discovery_cluster_count":unmapped_discovery,
   "excluded_unavailable_oos_cluster_count":unmapped_oos,
   "discovery_required":1000,"oos_required":500,
   "pass":not sample_errors
 },
 "post_mapping_subgroups":post_mapping_subgroups,
 "sample_error_count":len(sample_errors),"sample_errors":sample_errors,
 "error_count":len(errors),"errors":errors,
 "registry_path":str(Path(args.registry)),
 "registry_sha256":sha256_file(args.registry) if Path(args.registry).exists() else None,
 "requirements_receipt_path":rp,
 "requirements_receipt_sha256":sha256_file(rp) if rp else None,
 "frozen_authorities":["MARKET_DATA_MAPPING_REGISTRY_FREEZE_V0.1.md",
                       "MARKET_DATA_MAPPING_SAMPLE_ADEQUACY_ADDENDUM_V0.2.md"],
 "firewall":{"archive_payload_downloaded":False,"candles_opened":False,"prices_opened":False,
             "returns_computed":False,"pnl_computed":False,"economic_outcomes_opened":False,
             "protected_2025_2026_opened":False,"post_outcome_tuning":False,
             "live_trading":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARKET_DATA_MAPPING_REGISTRY_PASS":raise SystemExit(2)

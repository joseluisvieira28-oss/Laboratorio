#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--requirements",required=True)
ap.add_argument("--registry",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_DATA_MAPPING_REGISTRY_VALIDATION_RECEIPT_V0.1.json")

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
mapped=0;unavailable=0;inferential_unavailable=[]

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
        mapped+=1
        required_fields=["symbol","base_asset","quote_asset","venue_metadata_authority",
                         "archive_route_template","checksum_route_template"]
        for f in required_fields:
            if not row.get(f):errors.append({"reason":"binance_field_missing","target_identity":target,"field":f})
        quote=row.get("quote_asset")
        if quote not in QUOTE_RANK:
            errors.append({"reason":"unsupported_quote","target_identity":target,"quote":quote})
        elif QUOTE_RANK[quote]>0 and not row.get("higher_priority_quote_unavailable_evidence"):
            errors.append({"reason":"lower_priority_quote_without_evidence","target_identity":target,"quote":quote})
        if row.get("listing_start_utc") is None and row.get("listing_start_status")!="SOURCE_NOT_AVAILABLE":
            errors.append({"reason":"listing_boundary_missing","target_identity":target})
    elif status=="OKX_DIRECT":
        mapped+=1
        for f in ["instrument_id","base_asset","quote_asset","venue_metadata_authority",
                  "listing_start_utc","historical_candle_route_authority","binance_unavailable_evidence"]:
            if not row.get(f):errors.append({"reason":"okx_field_missing","target_identity":target,"field":f})
    elif status=="MARKET_MAPPING_UNAVAILABLE":
        unavailable+=1
        if not row.get("reason") or not row.get("evidence"):
            errors.append({"reason":"unavailable_without_evidence","target_identity":target})
        if need.get("inferential_dependency"):
            inferential_unavailable.append(target)
    else:
        errors.append({"reason":"invalid_mapping_status","target_identity":target,"status":status})

if inferential_unavailable:
    errors.append({"reason":"inferential_targets_unavailable","targets":sorted(inferential_unavailable)})

classification="MARKET_DATA_MAPPING_REGISTRY_PASS" if not errors else "MARKET_DATA_MAPPING_REGISTRY_BLOCKED_FAIL_CLOSED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "requirements_classification":(req or {}).get("classification"),
 "requirements_count":len(requirements),"mapping_row_count":len(rows),
 "mapped_target_count":mapped,"unavailable_target_count":unavailable,
 "inferential_unavailable_count":len(inferential_unavailable),
 "missing_target_count":len(missing),"extra_target_count":len(extra),
 "error_count":len(errors),"errors":errors,
 "registry_path":str(Path(args.registry)),
 "frozen_authority":"MARKET_DATA_MAPPING_REGISTRY_FREEZE_V0.1.md",
 "firewall":{"archive_payload_downloaded":False,"candles_opened":False,"prices_opened":False,
             "returns_computed":False,"pnl_computed":False,"economic_outcomes_opened":False,
             "protected_2025_2026_opened":False,"post_outcome_tuning":False,
             "live_trading":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARKET_DATA_MAPPING_REGISTRY_PASS":raise SystemExit(2)

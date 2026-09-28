#!/usr/bin/env python3
import json,os,urllib.request,zipfile,io
from pathlib import Path
req_path=Path("mapping_requirements/MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json")
if not req_path.exists(): raise SystemExit("NO_MAPPING_REQUIREMENTS_RECEIPT")
req=json.loads(req_path.read_text())
assert req["classification"]=="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS"
artifact_id=int(os.environ.get("MAPPING_REQUIREMENTS_ARTIFACT_ID","0"))
sol="mint:So11111111111111111111111111111111111111112"
rows=[]
for need in req["requirements"]:
 t=need["target_identity"]
 if t==sol:
  rows.append({
   "target_identity":t,"status":"BINANCE_DIRECT","canonical_asset_id":"SOL",
   "identity_authority":["MARKET_DATA_SOURCE_GATE_FREEZE_V0.1.md:native SOL <-> canonical wrapped SOL equivalence",
                         "MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json:exact target identity"],
   "notes":"Conservative V0.3 sole direct mapping; all route coverage independently metadata-probed before authority.",
   "symbol":"SOLUSDT","base_asset":"SOL","quote_asset":"USDT",
   "venue_metadata_authority":"Binance public Spot exchangeInfo exact symbol/baseAsset/quoteAsset",
   "current_product_metadata_expected":True,
   "listing_start_utc":"2021-12-08T00:00:00Z",
   "archive_route_template":"https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip",
   "checksum_route_template":"https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{symbol}-1m-{date}.zip.CHECKSUM"
  })
 else:
  rows.append({
   "target_identity":t,"status":"MARKET_MAPPING_UNAVAILABLE","canonical_asset_id":t,
   "identity_authority":["MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json:exact source target identity"],
   "notes":"Conservative pre-outcome V0.3: no additional direct venue identity authority introduced.",
   "reason":"NO_ADDITIONAL_EXACT_DIRECT_MARKET_AUTHORITY_FROZEN_PRE_OUTCOME",
   "evidence":["MARKET_DATA_MAPPING_CONSERVATIVE_SELECTION_ADDENDUM_V0.3.md"]
  })
out={"schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "authority":"MARKET_DATA_MAPPING_CONSERVATIVE_SELECTION_ADDENDUM_V0.3.md",
 "source_requirements_artifact_id":artifact_id,"mapping_count":len(rows),"mappings":rows,
 "firewall":{"archive_payload_downloaded":False,"candles_opened":False,"prices_opened":False,
 "returns_computed":False,"pnl_computed":False,"economic_outcomes_opened":False,
 "protected_2025_2026_opened":False,"post_outcome_tuning":False,"live_trading":False,"merge_main":False}}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_DATA_MAPPING_REGISTRY_V0.1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\\n")
print(json.dumps({"mapping_count":len(rows),"direct_count":1,"unavailable_count":len(rows)-1},indent=2))

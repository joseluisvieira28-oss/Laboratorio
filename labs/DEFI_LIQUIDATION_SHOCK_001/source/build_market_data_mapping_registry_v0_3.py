#!/usr/bin/env python3
import json,os,urllib.request,zipfile,io
from pathlib import Path
repo=os.environ["GITHUB_REPOSITORY"]
token=os.environ["GH_TOKEN"]
headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","User-Agent":"dls-registry-builder/0.3"}
def getj(url):
 q=urllib.request.Request(url,headers=headers)
 with urllib.request.urlopen(q,timeout=60) as r:return json.load(r)
arts=getj(f"https://api.github.com/repos/{repo}/actions/artifacts?name=dls-market-mapping-requirements-v01&per_page=100").get("artifacts",[])
arts=[a for a in arts if not a.get("expired")]
if not arts: raise SystemExit("NO_MAPPING_REQUIREMENTS_ARTIFACT")
a=sorted(arts,key=lambda x:(x.get("created_at",""),x["id"]),reverse=True)[0]
q=urllib.request.Request(a["archive_download_url"],headers=headers)
with urllib.request.urlopen(q,timeout=90) as r:z=zipfile.ZipFile(io.BytesIO(r.read()))
req=json.loads(z.read("MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json"))
assert req["classification"]=="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS"
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
 "source_requirements_artifact_id":a["id"],"mapping_count":len(rows),"mappings":rows,
 "firewall":{"archive_payload_downloaded":False,"candles_opened":False,"prices_opened":False,
 "returns_computed":False,"pnl_computed":False,"economic_outcomes_opened":False,
 "protected_2025_2026_opened":False,"post_outcome_tuning":False,"live_trading":False,"merge_main":False}}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_DATA_MAPPING_REGISTRY_V0.1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\\n")
print(json.dumps({"mapping_count":len(rows),"direct_count":1,"unavailable_count":len(rows)-1},indent=2))

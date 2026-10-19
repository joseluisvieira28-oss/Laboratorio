"""V02D fixed 2025 OKX BTC/ETH/SOL USD inverse SWAP archive metadata only."""
import json
from pathlib import Path
from research.funding_hunter_v02 import okx_2025_archive_catalogue_gate as base
FAMILIES=("BTC-USD","ETH-USD","SOL-USD")
def main():
    base.FAMILIES=FAMILIES
    queries=(("2025_JUNE_USD_INVERSE_FUNDING",{"module":"3","instType":"SWAP",
       "instFamilyList":",".join(FAMILIES),"dateAggrType":"monthly",
       "begin":base.ms("2025-06-01"),"end":base.ms("2025-06-01")}),)+tuple(
       (f"2025_JUNE2_{family}_INVERSE_400L2",{"module":"4","instType":"SWAP",
       "instFamilyList":family,"dateAggrType":"daily",
       "begin":base.ms("2025-06-02"),"end":base.ms("2025-06-02")})
       for family in FAMILIES)
    rows=[base.fetch(label,query) for label,query in queries]
    result={"stage":"OKX_USDT_LINEAR_USD_INVERSE_FAMILY_DISCOVERY_ONLY",
         "usdinverse_families":FAMILIES,"results":rows,
         "market_values_read":False,"2026_holdout_opened":False,
         "status":"SIX_INVERSE_CATALOGUE_FILES_DISCOVERED_NOT_BYTES_OR_EDGE" if
         rows[0].get("file_candidates")==3 and
         all(x.get("file_candidates")==1 for x in rows[1:])
         else "THREE_ASSET_INVERSE_CATALOGUE_INCOMPLETE",
         "trading_authority":"NONE"}
    d=Path("research/funding_hunter_v02/receipts");d.mkdir(parents=True,exist_ok=True)
    (d/"V02D_USD_INVERSE_2025_METADATA_ONLY.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    for row in rows:print("V02D_USD_INVERSE_ARCHIVE",json.dumps(row,sort_keys=True))
    print("V02D_STATUS",result["status"])
if __name__=="__main__":main()

"""V02C one same-venue OKX USDC+USDT source FAMILY metadata check only."""
import json
from pathlib import Path
from research.funding_hunter_v02 import okx_2025_archive_catalogue_gate as base
FAMILIES=("BTC-USDC","ETH-USDC","SOL-USDC")
def main():
    base.FAMILIES=FAMILIES
    queries=(("2025_JUNE_USDC_FUNDING",{"module":"3","instType":"SWAP",
       "instFamilyList":",".join(FAMILIES),"dateAggrType":"monthly",
       "begin":base.ms("2025-06-01"),"end":base.ms("2025-06-01")}),)+tuple(
       (f"2025_JUNE2_{family}_USDC_400L2",{"module":"4","instType":"SWAP",
       "instFamilyList":family,"dateAggrType":"daily",
       "begin":base.ms("2025-06-02"),"end":base.ms("2025-06-02")})
       for family in FAMILIES)
    rows=[base.fetch(label,query) for label,query in queries]
    result={"stage":"OKX_USDT_USDC_SOURCE_DISCOVERY_ONLY",
         "four_official_2025_metadata_requests":True,
         "usdc_families":FAMILIES,"sources":rows,
         "raw_market_outcomes_opened":False,"2026_holdout_opened":False,
         "overall":"ALL_SIX_USDC_FILES_CATALOGUED_NOT_VERIFIED_BYTES" if
         rows[0].get("file_candidates")==3 and
         all(row.get("file_candidates")==1 for row in rows[1:]) else "USDC_SOURCE_INCOMPLETE",
         "trade_authority":"NONE"}
    p=Path("research/funding_hunter_v02/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"V02C_USDC_OFFICIAL_METADATA_ONLY.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    for row in rows:print("V02C_USDC_ARCHIVE",json.dumps(row,sort_keys=True))
    print("V02C_SOURCE_ONLY",result["overall"])
if __name__=="__main__":main()

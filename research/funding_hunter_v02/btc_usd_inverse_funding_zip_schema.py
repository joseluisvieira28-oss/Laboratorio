"""Original OKX June 2025 BTC-USD inverse funding ZIP header only, no market rows."""
import json,urllib.parse
from pathlib import Path
from urllib.parse import urlparse
from research.funding_hunter_v02 import transport_2025_only as origin
def inverse_candidates(doc):
    found=[]
    def walk(obj,fam=""):
        if isinstance(obj,list):
            for x in obj:walk(x,fam)
        elif isinstance(obj,dict):
            fam=obj.get("instFamily") or fam
            fn=obj.get("filename");url=obj.get("url")
            if isinstance(fn,str) and isinstance(url,str) and fn.endswith(".zip") and "2025-06" in fn:
                if (fam=="BTC-USD" or fn.startswith("BTC-USD-SWAP-")) and urlparse(url).hostname=="static.okx.com":
                    found.append(url)
            for k,v in obj.items():
                if k not in ("filename","url"):walk(v,fam)
    walk(doc)
    return list(dict.fromkeys(found))
def main():
    origin.url="https://www.okx.com/api/v5/public/market-data-history?"+urllib.parse.urlencode({
        "module":"3","instType":"SWAP","instFamilyList":"BTC-USD,ETH-USD,SOL-USD",
        "dateAggrType":"monthly","begin":origin.ms("2025-06-01"),"end":origin.ms("2025-06-01")})
    origin.candidates=inverse_candidates
    res={"source":"2025-06 BTC-USD inverse funding original OKX",
         "catalogued_before_request":True,
         "zip_schema_only":origin.okx(),"funding_rows_read":0,
         "2026_holdout_opened":False,"profit_calculated":False}
    p=Path("research/funding_hunter_v02/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"V02E_BTC_USD_INVERSE_FUNDING_ZIP_SCHEMA.json").write_text(json.dumps(res,sort_keys=True,indent=2)+"\n")
    print("V02E_INVERSE_FUNDING_HEADER",json.dumps(res,sort_keys=True))
if __name__=="__main__":main()

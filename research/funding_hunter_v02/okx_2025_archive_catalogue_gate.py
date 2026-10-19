"""Bounded public unsigned OKX 2025 archive CATALOGUE discovery ONLY."""
import hashlib,json,ssl,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
BASE="https://www.okx.com/api/v5/public/market-data-history"
FAMILIES=("BTC-USDT","ETH-USDT","SOL-USDT")
def ms(day):
    return str(int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000))
QUERIES=(("2025_JUNE_FUNDING_MONTHLY",{"module":"3","instType":"SWAP",
  "instFamilyList":",".join(FAMILIES),"dateAggrType":"monthly",
  "begin":ms("2025-06-01"),"end":ms("2025-06-01")}),)+tuple(
  (f"2025_JUNE2_{family}_400L2",{"module":"4","instType":"SWAP",
   "instFamilyList":family,"dateAggrType":"daily",
   "begin":ms("2025-06-02"),"end":ms("2025-06-02")})
  for family in FAMILIES)
def summarize(reply):
    if not isinstance(reply,dict):return {"status":"SOURCE_BLOCKED_BAD_SCHEMA"}
    code=str(reply.get("code",""))
    if code!="0":return {"status":"SOURCE_BLOCKED_API_CODE","api_code":code[:20]}
    data=reply.get("data")
    if not isinstance(data,list):return {"status":"SOURCE_BLOCKED_NO_DATA_LIST"}
    n={"groups":0,"file_candidates":0,"official_static_hosts":0}
    fams=set();extensions=set()
    def walk(obj,depth=0):
        if depth>8:return
        if isinstance(obj,list):
            for x in obj[:50]:walk(x,depth+1)
        if isinstance(obj,dict):
            if "groupDetails" in obj:n["groups"]+=1
            fam=obj.get("instFamily")
            if isinstance(fam,str) and fam in FAMILIES:fams.add(fam)
            link=obj.get("url");fn=obj.get("filename")
            if isinstance(link,str) and isinstance(fn,str) and link.startswith("https://"):
                n["file_candidates"]+=1
                if urlparse(link).hostname=="static.okx.com":n["official_static_hosts"]+=1
                if fn.endswith(".tar.gz"):extensions.add(".tar.gz")
                elif fn.endswith(".csv"):extensions.add(".csv")
                elif fn.endswith(".zip"):extensions.add(".zip")
                else:extensions.add("UNKNOWN")
            for k,v in obj.items():
                if k not in ("url","filename","instIdList"):walk(v,depth+1)
    walk(data)
    return {"status":"OFFICIAL_FILE_CATALOGUE_CANDIDATE_ONLY" if n["file_candidates"] else "SOURCE_BLOCKED_NO_DOWNLOADABLE_FILE",
        **n,"declared_families":sorted(fams),"filename_extension_classes":sorted(extensions),
        "underlying_market_data_bytes_downloaded":0,"actual_file_instrument_and_rate_format_verified":False}
def fetch(label,query):
    if int(query["begin"])>=int(ms("2026-01-01")) or int(query["end"])>=int(ms("2026-01-01")):raise ValueError("PROTECTED_2026")
    url=BASE+"?"+urllib.parse.urlencode(query)
    request=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Source-Metadata-Research/0.2","Accept":"application/json"},method="GET")
    try:
        with urllib.request.urlopen(request,timeout=17,context=ssl.create_default_context()) as res:
            raw=res.read(1000001)
            if len(raw)>1000000:raise ValueError("METADATA_MAX_BYTES")
            http=res.status;ctype=res.headers.get("Content-Type","")
        if http!=200 or "json" not in ctype.lower():
            return {"id":label,"status":"SOURCE_BLOCKED_HTTP_MEDIA","http_status":http,"json_media":False}
        return {"id":label,"http_status":http,"metadata_sha256":hashlib.sha256(raw).hexdigest(),**summarize(json.loads(raw))}
    except urllib.error.HTTPError as err:return {"id":label,"status":"SOURCE_BLOCKED_HTTP_ERROR","http_status":err.code}
    except Exception as exc:return {"id":label,"status":"SOURCE_BLOCKED_REQUEST_OR_SCHEMA","reason_class":type(exc).__name__}
def main():
    rows=[fetch(label,query) for label,query in QUERIES]
    summary={"mission":"FUNDING_HUNTER_V02_OKX_2025_SOURCE_METADATA","source_stage_only":True,
      "calls":len(rows),"raw_market_files_downloaded":0,"protected_2026_opened":False,
      "actual_trade_orders":0,"income_proven":False,"results":rows}
    root=Path("research/funding_hunter_v02/receipts")
    root.mkdir(parents=True,exist_ok=True)
    (root/"V02_2025_OKX_CATALOGUE_RECEIPT.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    for x in rows:print("V02_SOURCE_CATALOGUE",json.dumps(x,sort_keys=True))
    print("V02_METADATA_ONLY_NOT_MARKET_DATA_NOT_EDGE")
if __name__=="__main__":main()

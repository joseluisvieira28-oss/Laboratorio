"""V02B source-only June 2025 public ZIP header and historical Binance HEAD, no outcomes."""
import hashlib,io,json,urllib.request as ur,urllib.parse as up,urllib.error,zipfile
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
def ms(s):return str(int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000))
url="https://www.okx.com/api/v5/public/market-data-history?"+up.urlencode({
"module":"3","instType":"SWAP","instFamilyList":"BTC-USDT,ETH-USDT,SOL-USDT",
"dateAggrType":"monthly","begin":ms("2025-06-01"),"end":ms("2025-06-01")})
def candidates(data):
    found=[]
    def walk(obj,fam=""):
        if isinstance(obj,list):
            for x in obj:walk(x,fam)
        if isinstance(obj,dict):
            fam=obj.get("instFamily") or fam
            fn=obj.get("filename");ln=obj.get("url")
            if isinstance(fn,str) and isinstance(ln,str) and fn.endswith(".zip") and "2025-06" in fn:
                if fam=="BTC-USDT" or "BTC-USDT" in fn:
                    if urlparse(ln).scheme=="https" and urlparse(ln).hostname=="static.okx.com":found.append(ln)
            for k,v in obj.items():
                if k not in ("url","filename"):walk(v,fam)
    walk(data)
    return list(dict.fromkeys(found))
def okx():
    try:
        req=ur.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-Funding-V02B"})
        with ur.urlopen(req,timeout=16) as f: doc=json.load(f)
        if str(doc.get("code"))!="0":return {"status":"CATALOGUE_API_ERROR","api_code":str(doc.get("code"))}
        links=candidates(doc.get("data",[]))
        if len(links)!=1:return {"status":"BTC_ARCHIVE_LINK_NOT_UNIQUE","link_count":len(links)}
        req=ur.Request(links[0],headers={"User-Agent":"CryptoLab-Funding-V02B"})
        with ur.urlopen(req,timeout=20) as f:
            binary=f.read(40*1024*1024+1)
            if len(binary)>40*1024*1024:raise ValueError("COMPRESSED_SIZE_CAP")
        with zipfile.ZipFile(io.BytesIO(binary)) as z:
            rows=[]
            for member in z.infolist():
                if member.is_dir():continue
                if member.file_size>20*1024*1024 or member.filename.startswith("/") or ".." in Path(member.filename).parts:raise ValueError("UNSAFE_MEMBER")
                with z.open(member) as f: header=f.readline(1200).decode("utf8",errors="replace").strip()
                # Schema header only; do not export or inspect funding values in first data row.
                rows.append({"member_bytes":member.file_size,"header_if_schema":header[:220] if "time" in header.lower() or "fund" in header.lower() else "NOT_RECOGNIZED_NO_DATA_EXPORTED"})
        return {"status":"OFFICIAL_FUNDING_ZIP_BYTES_OBTAINED_HEADER_ONLY",
        "archive_bytes":len(binary),"archive_sha256_local":hashlib.sha256(binary).hexdigest(),
        "source_members":rows,"outcome_funding_rows_inspected":0}
    except urllib.error.HTTPError as e:return {"status":"OFFICIAL_FUNDING_ARCHIVE_OR_CATALOGUE_HTTP_BLOCK","http_status":e.code}
    except Exception as e:return {"status":"SOURCE_BLOCKED_ARCHIVE_OR_SCHEMA","reason_class":type(e).__name__}
def head(kind):
    link=f"https://data.binance.vision/data/futures/um/daily/{kind}/BTCUSDT/BTCUSDT-{kind}-2025-06-02.zip"
    try:
        with ur.urlopen(ur.Request(link,method="HEAD"),timeout=12) as f:
            return {"kind":kind,"status":"HEAD_200_SOURCE_EXISTS_NOT_EXECUTION" if f.status==200 else "HEAD_NON200","http_status":f.status}
    except urllib.error.HTTPError as e:return {"kind":kind,"status":"HEAD_HTTP_BLOCKED","http_status":e.code}
    except Exception as e:return {"kind":kind,"status":"HEAD_REQUEST_FAILED","reason_class":type(e).__name__}
def main():
    out={"stage":"SOURCE_ONLY","okx_2025_btc_june_funding":okx(),
         "binance_2025_june2_btc":[head("bookTicker"),head("bookDepth")],
         "funding_numbers_read":0,"pnl_calculated":False,"2026_holdout_opened":False}
    p=Path("research/funding_hunter_v02/receipts")
    p.mkdir(parents=True,exist_ok=True)
    (p/"V02B_SOURCE_TRANSPORT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("V02B_SOURCE_ONLY",json.dumps(out,sort_keys=True))
if __name__=="__main__":main()

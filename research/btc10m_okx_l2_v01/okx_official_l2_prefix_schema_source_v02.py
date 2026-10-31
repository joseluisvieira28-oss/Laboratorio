#!/usr/bin/env python3
"""Official OKX original static archived L2 400lvl first 512KiB ONLY; schema not returns."""
import datetime as dt,hashlib,json,pathlib,tarfile,urllib.request,zlib
OUT=pathlib.Path("artifacts/btc10m_okx_l2_prefix_v02")
TARGETS=[
("2024-01-01","SPOT","https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20240101/BTC-USDT-L2orderbook-400lv-2024-01-01.tar.gz"),
("2024-01-01","SWAP","https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20240101/BTC-USDT-SWAP-L2orderbook-400lv-2024-01-01.tar.gz"),
("2025-01-01","SPOT","https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20250101/BTC-USDT-L2orderbook-400lv-2025-01-01.tar.gz"),
("2025-01-01","SWAP","https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/20250101/BTC-USDT-SWAP-L2orderbook-400lv-2025-01-01.tar.gz")]
LIMIT=524288
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(x):return hashlib.sha256(x).hexdigest()
class Stop(Exception):pass
class RedirectBlock(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,h,url):
        raise Stop("REDIRECT_BLOCK")
def shape(data):
    if data[:2]!=b"\x1f\x8b":raise Stop("NO_GZIP_MAGIC")
    try:
        decomp=zlib.decompressobj(31).decompress(data,6_000_000)
    except Exception as e:raise Stop("GZIP_PREFIX_UNDECODABLE_"+type(e).__name__) from e
    if len(decomp)<512:raise Stop("TAR_HEADER_INCOMPLETE")
    try:info=tarfile.TarInfo.frombuf(decomp[:512],encoding="utf-8",errors="replace")
    except Exception as e:raise Stop("TAR_FIRST_HEADER_BAD_"+type(e).__name__) from e
    if len(decomp)<1024:raise Stop("TAR_FIRST_DATA_MISSING")
    first=decomp[512:];line=first.split(b"\n",1)[0]
    if not line or b"\n" not in first:raise Stop("NO_FIRST_COMPLETE_ROW")
    try:j=json.loads(line)
    except Exception as e:raise Stop("FIRST_TAR_ROW_NOT_NDJSON_"+type(e).__name__) from e
    if not isinstance(j,dict):raise Stop("ROW_NOT_OBJECT")
    def nested(k):
        x=j.get(k)
        return {"type":type(x).__name__,"count":len(x) if isinstance(x,(list,dict)) else None,
          "first_nesting_type":type(x[0]).__name__ if isinstance(x,list) and x else None}
    return {"gzip_and_tar_first_header_valid":True,"first_tar_member":info.name,
      "first_tar_member_size":info.size,
      "first_row_json_keys":sorted(j.keys()),"first_row_venue_action":str(j.get("action",""))[:30],
      "first_row_ts_type":type(j.get("ts")).__name__,
      "first_row_ts_decimals":len(str(j.get("ts",""))),
      "bids_schema":nested("bids"),"asks_schema":nested("asks"),
      "original_prices_parsed_for_science":False}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    out={"study":"OKX_SPOT_SWAP_HISTORICAL_L2_PREFIX_SCHEMAS_V02",
      "started_utc":utc(),"status":"SOURCE_PREFIX_GATE_FAIL",
      "market_returns_read":0,"account_calls":0,"orders":0,"money_spent":0,"files":[]}
    opener=urllib.request.build_opener(RedirectBlock)
    for date,venue,url in TARGETS:
        rec={"date":date,"venue":venue,"url":url,"requested_utc":utc()}
        try:
            req=urllib.request.Request(url,method="GET",headers={"Range":"bytes=0-524287",
                "User-Agent":"CryptoLab-OKX-L2-HeaderOnly/1.0"})
            with opener.open(req,timeout=18) as response:
                rec["http"]=response.status
                rec["reported_content_length"]=response.headers.get("Content-Length")
                rec["content_range"]=response.headers.get("Content-Range")
                raw=response.read(LIMIT+1)
            if len(raw)>LIMIT:raise Stop("RANGE_WAS_IGNORED_OR_MORE_THAN_SOURCE_CAP")
            rec["raw_partial_sha256"]=sha(raw);rec["bytes"]=len(raw)
            name=f"{date}_{venue.lower()}_prefix.bin";(OUT/name).write_bytes(raw)
            rec["file"]=name
            rec["schema"]=shape(raw);rec["status"]="ARCHIVE_PREFIX_FORMAT_PROVEN"
        except Exception as e:
            rec["status"]="ARCHIVE_PREFIX_BLOCKED"
            rec["error"]=type(e).__name__+":"+str(e)[:180]
        out["files"].append(rec)
    out["status"]="FOUR_OFFICIAL_ORIGINAL_L2_PREFIX_SCHEMAS_PROVEN" if all(x["status"]=="ARCHIVE_PREFIX_FORMAT_PROVEN" for x in out["files"]) else "SOURCE_PREFIX_GATE_FAIL"
    out["finished_utc"]=utc()
    (OUT/"receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("OFFICIAL_L2_PREFIX",json.dumps(out,indent=2,sort_keys=True),flush=True)
    if out["status"]!="FOUR_OFFICIAL_ORIGINAL_L2_PREFIX_SCHEMAS_PROVEN":raise SystemExit(2)
if __name__=="__main__":main()

#!/usr/bin/env python3
"""One-shot official OKX historical L2 orderbook ARCHIVE LINK METADATA only, no price opens."""
import datetime as dt,hashlib,json,pathlib,urllib.parse,urllib.request
OUT=pathlib.Path("artifacts/btc10m_okx_official_l2_source_v01")
BASE="https://www.okx.com/api/v5/public/market-data-history"
SCOPES=[
 ("2024-01-01","SPOT","BTC-USDT","instIdList",1704067200000,1704153599999),
 ("2024-01-01","SWAP","BTC-USDT","instFamilyList",1704067200000,1704153599999),
 ("2025-01-01","SPOT","BTC-USDT","instIdList",1735689600000,1735775999999),
 ("2025-01-01","SWAP","BTC-USDT","instFamilyList",1735689600000,1735775999999)]
def utc():return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def h(x):return hashlib.sha256(x).hexdigest()
class NoOutsideRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,url):
        raise ValueError("NO_REDIRECT_ALLOWED")
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r={"study":"BTC10M_OKX_SPOT_SWAP_OFFICIAL_L2_ARCHIVE_METADATA_V01",
      "started_utc":utc(),"status":"SOURCE_BLOCKED_OR_INCOMPLETE",
      "requests":[],"verified_listed_scopes":0,
      "downloaded_market_archive_bytes":0,"market_outcomes_read":0,
      "orders":0,"wallet":0,"account_calls":0,"paid_requests":0,"economic_edge_certified":False}
    opener=urllib.request.build_opener(NoOutsideRedirect)
    for day,market,sym,instkey,begin,end in SCOPES:
        query=urllib.parse.urlencode([
            ("module","4"),("instType",market),(instkey,sym),
            ("dateAggrType","daily"),("begin",str(begin)),("end",str(end))])
        url=BASE+"?"+query
        rec={"date":day,"market":market,"instkey":instkey,"uri":url,"request_utc":utc()}
        try:
            req=urllib.request.Request(url,method="GET",headers={"Accept":"application/json",
                "User-Agent":"CryptoLab-OKX-L2Archive-MetadataOnly/1.0"})
            with opener.open(req,timeout=12) as res:
                raw=res.read(1_000_001)
                rec["http"]=res.status
            if len(raw)>1_000_000:raise ValueError("BODY_TOO_LARGE")
            name=f"{day}_{market.lower()}.json"
            (OUT/name).write_bytes(raw)
            rec["raw_file"]=name;rec["bytes"]=len(raw);rec["raw_sha256"]=h(raw)
            obj=json.loads(raw)
            rec["response_code"]=str(obj.get("code"))
            rec["response_message"]=str(obj.get("msg",""))[:160]
            data=obj.get("data")
            rec["data_type"]=type(data).__name__
            rec["data_count"]=len(data) if isinstance(data,list) else None
            rec["first_metadata_keys"]=sorted(data[0].keys())[:35] if isinstance(data,list) and data and isinstance(data[0],dict) else None
            rec["first_metadata_safe"]=(
                {k:v for k,v in data[0].items() if k in
                  ("instId","instType","instFamily","begin","end","ts","date","fileName","fileUrl","url","link","downloadUrl")}
                if isinstance(data,list) and data and isinstance(data[0],dict) else None)
            if str(obj.get("code"))=="0" and isinstance(data,list) and len(data)>0:
                r["verified_listed_scopes"]+=1
                rec["metadata_present"]=True
            else:rec["metadata_present"]=False
        except Exception as e:
            rec["error"]=type(e).__name__+":"+str(e)[:200]
        r["requests"].append(rec)
    r["status"]="FOUR_OFFICIAL_L2_ARCHIVE_SCOPES_LISTED_FILE_UNPROVEN" if r["verified_listed_scopes"]==4 else "SOURCE_BLOCKED_OR_INCOMPLETE"
    r["finished_utc"]=utc()
    (OUT/"receipt.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("FINAL_OFFICIAL_SOURCE",json.dumps(r,indent=2,sort_keys=True))
    if r["status"]!="FOUR_OFFICIAL_L2_ARCHIVE_SCOPES_LISTED_FILE_UNPROVEN":raise SystemExit(2)
if __name__=="__main__":main()

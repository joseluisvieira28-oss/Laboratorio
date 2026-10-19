"""Two frozen official OKX public historical-L2-catalogue metadata GETs only.

No archive download, market prices, credentials, private endpoints, trading.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.parse,urllib.request,urllib.error
from collections import Counter
from pathlib import Path

ENDPOINT="https://www.okx.com/api/v5/public/market-data-history"
CASES=(
    ("SOL-USDT","SOL-USDT-SWAP","2023-05-29",1685318400000),
    ("BNB-USDT","BNB-USDT-SWAP","2023-11-01",1698796800000),
)
MAX_RESPONSE=1_000_000
MAX_FIELDS=80

class SameOriginRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=urllib.parse.urlsplit(newurl)
        if parsed.scheme!="https" or parsed.hostname!="www.okx.com":
            raise ValueError("UNAPPROVED_CATALOGUE_REDIRECT")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def structure(value,depth=0):
    """Return types and field shapes only, *never string values*."""
    if depth>7:return {"type":"DEPTH_LIMIT"}
    if isinstance(value,dict):
        k=sorted(value.keys())[:MAX_FIELDS]
        return {"type":"dict","keys":k,
                "values":{name:structure(value[name],depth+1) for name in k}}
    if isinstance(value,list):
        return {"type":"array","len":len(value),
                "first":structure(value[0],depth+1) if value else None}
    if isinstance(value,str):return {"type":"string","chars":len(value)}
    if value is None:return {"type":"null"}
    if isinstance(value,bool):return {"type":"boolean"}
    return {"type":"number"}

def file_link_hosts(value,max_depth=12):
    """Only explicitly url/download/href/uri-labelled HTTPS strings count."""
    matches=[]
    def recurse(v,prefix,depth):
        if depth>max_depth:return
        if isinstance(v,list):
            for i,x in enumerate(v[:50]):recurse(x,prefix+f"[{i}]",depth+1)
        elif isinstance(v,dict):
            for key,x in list(v.items())[:MAX_FIELDS]:
                path=prefix+"."+key
                if isinstance(x,str) and any(tok in key.lower() for tok in ("url","href","download","uri")):
                    parsed=urllib.parse.urlsplit(x)
                    if parsed.scheme=="https" and parsed.hostname and parsed.username is None:
                        matches.append({
                            "field_path":path,"host":parsed.hostname.lower(),
                            "sanitized_path_sha256":hashlib.sha256(parsed.path.encode()).hexdigest(),
                            "has_query":bool(parsed.query),
                        })
                else:recurse(x,path,depth+1)
    recurse(value,"data",0)
    return matches

def classify(case,status,raw=b"",error=""):
    family,inst,day,epoch_ms=case
    out={"family":family,"instrument":inst,"day_utc":day,
        "http_status":status,"response_bytes":len(raw),
        "raw_sha256":hashlib.sha256(raw).hexdigest() if raw else None,
        "api_code":None,"top_keys":[],"data_count":0,
        "nested_shape":None,"public_candidate_link_descriptors":[],
        "status":"SOURCE_BLOCKED","reason":error[:130],
        "files_downloaded":0,"prices_observed":False,"trading_authority":"NONE"}
    if status!=200 or not raw:return out
    try:
        doc=json.loads(raw.decode("utf-8"))
        if not isinstance(doc,dict):raise ValueError("NOT_OBJECT")
        out["top_keys"]=sorted(doc)[:MAX_FIELDS]
        out["api_code"]=str(doc.get("code","MISSING"))
        values=doc.get("data")
        if not isinstance(values,list):raise ValueError("DATA_NOT_LIST")
        out["data_count"]=len(values)
        out["nested_shape"]=structure(values)
        out["public_candidate_link_descriptors"]=file_link_hosts(values)
        if out["api_code"]!="0":out["reason"]="NONZERO_API_CODE"
        elif not values:out["reason"]="EMPTY_CATALOGUE"
        elif out["public_candidate_link_descriptors"]:
            out["status"]="CATALOGUE_LINK_CANDIDATE_NOT_L2_VERIFIED"
            out["reason"]="DOWNLOADABLE_FILE_NOT_CHECKED"
        else:
            out["status"]="CATALOGUE_SCHEMA_ONLY_NO_FILE_URL"
            out["reason"]="NOT_YET_AN_AUTHENTICATED_HISTORICAL_L2_ARCHIVE"
    except Exception as exc:
        out["reason"]=type(exc).__name__+":"+str(exc)[:90]
    return out

def one_get(case):
    family,_,_,stamp=case
    query=urllib.parse.urlencode({
        "module":"4","instType":"SWAP","instFamilyList":family,
        "dateAggrType":"daily","begin":str(stamp),"end":str(stamp)
    })
    req=urllib.request.Request(ENDPOINT+"?"+query,headers={
        "Accept":"application/json","User-Agent":"CryptoLab-Science-ReadOnly-HistoricalSource/0.5",
    })
    opener=urllib.request.build_opener(SameOriginRedirects)
    code=0;raw=b"";error=""
    try:
        with opener.open(req,timeout=10) as response:
            code=int(response.status)
            raw=response.read(MAX_RESPONSE+1)
            if len(raw)>MAX_RESPONSE:
                raise ValueError("SOURCE_RESPONSE_EXCEEDS_1MB")
    except urllib.error.HTTPError as exc:
        code=exc.code;error="HTTP_"+str(exc.code)
    except Exception as exc:
        error=type(exc).__name__+":"+str(exc)[:90]
    return classify(case,code,raw,error)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    rows=[]
    for case in CASES:
        rec=one_get(case)
        rows.append(rec)
        print("V05_OKX_SOURCE",json.dumps(rec,sort_keys=True),flush=True)
    if len(rows)!=2:raise ValueError("FROZEN_CASE_COUNT")
    summary={"status":"PUBLIC_CATALOGUE_ONLY_NO_EXECUTION","pre_registered_cases":2,
        "categories":dict(Counter(x["status"] for x in rows)),
        "probes":rows,"full_400_l2_file_verified":False,
        "historical_ctVal_verified":False,"cross_venue_fill_proven":False,
        "independent_OOS":False,"real_orders":False,
        "trading_authority":"NONE"}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"OKX_V05_TWO_ORIGINAL_ENTRY_DATES_SOURCE_METADATA.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("V05_OKX_SOURCE_VERDICT",json.dumps({k:v for k,v in summary.items() if k!="probes"},sort_keys=True))
if __name__=="__main__":
    main()

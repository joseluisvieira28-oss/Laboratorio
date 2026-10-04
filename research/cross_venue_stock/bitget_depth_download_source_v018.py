#!/usr/bin/env python3
"""Source-only probe of Bitget official historical futures-depth download API."""
from __future__ import annotations
import csv,gzip,hashlib,io,json,zipfile
from pathlib import Path
import requests

DATE="2026-09-16"
SYMBOLS=["HOODUSDT","COINUSDT","ARMUSDT","AAPLUSDT"]
BASE="https://www.bitget.com"
API=BASE+"/v1/statistics/public/download/getPublicDataV2"
SYMBOL_API=BASE+"/v1/statistics/public/download/getSymbolList"
OUT=Path("artifacts/cross_venue_stock/bitget_depth_download_v018")
UA="Mozilla/5.0 CryptoLab-BitgetDepthSource/0.1.8"
HEADERS={
 "User-Agent":UA,
 "Content-Type":"application/json;charset=UTF-8",
 "Accept":"application/json, text/plain, */*",
 "Origin":"https://www.bitget.com",
 "Referer":"https://www.bitget.com/data-download",
 "terminalType":"1",
 "locale":"en_US",
 "language":"en_US",
 "securityNew":"true"
}

def sha(b):return hashlib.sha256(b).hexdigest()

def post(url,payload):
    r=requests.post(url,json=payload,headers=HEADERS,timeout=60)
    rec={"http":r.status_code,"sha256":sha(r.content),"bytes":len(r.content)}
    try:
        j=r.json()
        rec["json"]=j
        rec["code"]=j.get("code") if isinstance(j,dict) else None
        rec["msg"]=j.get("msg") if isinstance(j,dict) else None
    except Exception:
        rec["text_prefix"]=r.text[:500]
    return r,rec

def file_schema(url):
    r=requests.get(url,headers={"User-Agent":UA,"Referer":"https://www.bitget.com/data-download"},timeout=120)
    b=r.content
    out={"http":r.status_code,"bytes":len(b),"sha256":sha(b),"content_type":r.headers.get("content-type"),
         "final_url":r.url,"archive_type":"unknown","member_count":None,"row_count":None,"header":None}
    if r.status_code!=200:return out
    payload=b
    name=""
    try:
        if zipfile.is_zipfile(io.BytesIO(b)):
            out["archive_type"]="zip"
            z=zipfile.ZipFile(io.BytesIO(b)); names=z.namelist(); out["member_count"]=len(names)
            if names:
                name=names[0]; payload=z.read(name)
        elif b[:2]==b"\x1f\x8b":
            out["archive_type"]="gzip";payload=gzip.decompress(b)
        else:
            out["archive_type"]="plain"
        text=payload.decode("utf-8-sig",errors="replace")
        lines=[x for x in text.splitlines() if x.strip()]
        out["row_count"]=max(0,len(lines)-1)
        if lines:
            # Header only: source/schema validation; do not persist market-depth values.
            try:
                out["header"]=next(csv.reader([lines[0]]))
            except Exception:
                out["header_raw"]=lines[0][:500]
        out["member_name"]=name
    except Exception as e:
        out["parse_error"]=str(e)
    return out

def extract_files(j):
    if not isinstance(j,dict):return []
    data=j.get("data")
    if isinstance(data,list):return [x for x in data if isinstance(x,dict)]
    if isinstance(data,dict):
        for k in ("list","files","rows","data"):
            v=data.get(k)
            if isinstance(v,list):return [x for x in v if isinstance(x,dict)]
    return []

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"gate_id":"BITGET_DEPTH_DOWNLOAD_SOURCE_V0_1_8","source_only":True,"burned_date":DATE,
            "endpoint":API,"symbols":{},"market_depth_values_persisted":False}
    for sym in SYMBOLS:
        sr_payload={"displaySymbol":sym,"businessLine":2,"businessType":3,"languageType":1}
        _,sr=post(SYMBOL_API,sr_payload)
        item={"symbol_lookup":{"payload":sr_payload,"response":sr},"depth":{}}
        for dept in (1,2):
            payload={"displaySymbol":[sym],"businessLine":2,"businessType":3,"dateType":1,
                     "beginTimeStr":DATE,"endTimeStr":DATE,"deptType":dept}
            rr,rec=post(API,payload)
            files=extract_files(rec.get("json"))
            file_meta=[]
            for f in files[:5]:
                clean={k:f.get(k) for k in ("fileName","fileUrl","dateTime","dateTimeStr") if k in f}
                if f.get("fileUrl"):
                    clean["schema_probe"]=file_schema(str(f["fileUrl"]))
                file_meta.append(clean)
            item["depth"][str(dept)]={"payload":payload,
               "response_meta":{k:v for k,v in rec.items() if k!="json"},
               "response_data_type":type((rec.get("json") or {}).get("data")).__name__ if isinstance(rec.get("json"),dict) else None,
               "file_count":len(files),"files":file_meta}
            print(sym,"dept",dept,"http",rec["http"],"code",rec.get("code"),"msg",rec.get("msg"),"files",len(files))
            for fm in file_meta:
                print(" FILE",fm.get("fileName"),"schema",fm.get("schema_probe"))
        report["symbols"][sym]=item
    passes={}
    for sym,item in report["symbols"].items():
        l1=item["depth"]["1"]; l2=item["depth"]["2"]
        def ok(x):
            return x["file_count"]>0 and any((f.get("schema_probe") or {}).get("http")==200 and
                (f.get("schema_probe") or {}).get("row_count") not in (None,0) for f in x["files"])
        passes[sym]={"level1":ok(l1),"level500":ok(l2)}
    report["passes"]=passes
    report["all_level1_pass"]=all(x["level1"] for x in passes.values())
    report["all_level500_pass"]=all(x["level500"] for x in passes.values())
    report["verdict"]=("BITGET_HISTORICAL_DEPTH_SOURCE_PASS" if report["all_level1_pass"]
                       else "BITGET_HISTORICAL_DEPTH_SOURCE_BLOCKED")
    report.update({"microstructure_outcomes_opened":0,"private_endpoints_used":False,"account_reads":False,
                   "orders":False,"exchange_mutation":False,"live_trading_authorized":False})
    (OUT/"BITGET_DEPTH_DOWNLOAD_SOURCE_V018.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({"verdict":report["verdict"],"passes":passes},indent=2))

if __name__=="__main__":main()

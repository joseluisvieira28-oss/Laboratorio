#!/usr/bin/env python3
"""Free-source schema audit BEFORE LIQMAP004 economic event calculation. Never stores wallets."""
import datetime as dt,hashlib,io,json,pathlib,urllib.parse,urllib.request
import pyarrow.parquet as pq
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"results"
SOURCES={"events":"ironflow/hyperliquid-liquidations","candles":"ironflow/hyperliquid-candles-1h"}
MONTHS=("2026-07","2026-08","2026-09","2026-10")
def get(url,limit=40000000):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQMAP004-ReadOnly-Scientific/1.0"})
    begin=dt.datetime.now(dt.timezone.utc).isoformat()
    with urllib.request.urlopen(req,timeout=65) as f:raw=f.read(limit+1)
    end=dt.datetime.now(dt.timezone.utc).isoformat()
    if len(raw)>limit:raise ValueError("SOURCE_BLOCKED file over max bytes")
    return raw,{"url":url,"start_utc":begin,"end_utc":end,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={"study":"LIQMAP004 inventory","no_trades":True,"months":MONTHS,"datasets":{},
            "samples":[],"status":"SOURCE_BLOCKED","receipts":[]}
    for kind,ds in SOURCES.items():
        part="data/events" if kind=="events" else "data"
        url="https://huggingface.co/api/datasets/"+ds+"/tree/main/"+part+"?recursive=true&limit=1000"
        try:
            raw,receipt=get(url,3000000);result["receipts"].append(receipt)
            listing=json.loads(raw)
            candidates={}
            for x in listing:
                if x.get("type")!="file":continue
                for m in MONTHS:
                    if x.get("path")==part+"/"+m+".parquet":
                        candidates[m]={"path":x["path"],"bytes":x.get("size"),
                            "oid":x.get("lfs",{}).get("oid")}
            result["datasets"][kind]={"status":"SOURCE_PASS" if len(candidates)==4 else "SOURCE_BLOCKED",
               "files":candidates,"listing_total":len(listing)}
            if candidates:
                m="2026-07";f=candidates[m]
                url="https://huggingface.co/datasets/"+ds+"/resolve/main/"+f["path"]+"?download=true"
                try:
                    raw,receipt=get(url,45000000);result["receipts"].append(receipt)
                    if receipt["bytes"]!=f["bytes"] or (f["oid"] and receipt["sha256"]!=f["oid"]):
                        raise ValueError("SOURCE_BLOCKED LFS size/sha mismatch")
                    t=pq.read_table(io.BytesIO(raw))
                    fields=[{"name":x.name,"type":str(x.type)} for x in t.schema]
                    result["samples"].append({"kind":kind,"month":m,"rows":t.num_rows,
                        "schema":fields,"status":"SCHEMA_PASS",
                        "examples_of_symbol_only":{s:{col:str(t[col][0].as_py()) for col in ("market","coin")
                            if col in t.schema.names} for s in ("first",) if t.num_rows}})
                except Exception as e:result["samples"].append({"kind":kind,"status":"SCHEMA_SOURCE_BLOCKED","error":str(e)[:450]})
        except Exception as e:result["datasets"][kind]={"status":"SOURCE_BLOCKED","error":type(e).__name__+": "+str(e)}
        (OUT/"SOURCE_INVENTORY.json").write_text(json.dumps(result,indent=2)+"\n")
    result["status"]="SCHEMA_PASS" if len(result["samples"])==2 and all(x.get("status")=="SCHEMA_PASS" for x in result["samples"]) and all(x.get("status")=="SOURCE_PASS" for x in result["datasets"].values()) else "SOURCE_OR_SCHEMA_BLOCKED"
    (OUT/"SOURCE_INVENTORY.json").write_text(json.dumps(result,indent=2)+"\n")
    for x in result["samples"]:print("LIQMAP004_SCHEMA",x["kind"],x["status"],x.get("rows"),x.get("schema"),flush=True)
    print("LIQMAP004_SOURCE",result["status"],flush=True)
    if result["status"]!="SCHEMA_PASS":raise RuntimeError(result["status"])
if __name__=="__main__":main()

#!/usr/bin/env python3
import hashlib,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/btc_options_vrp_mark_history_diag_v011");OUT.mkdir(parents=True,exist_ok=True)
inst="BTC-29JAN21-28000-C"
start=datetime(2021,1,1,tzinfo=timezone.utc);end=start+timedelta(days=7)
params={"instrument_name":inst,"start_timestamp":int(start.timestamp()*1000),"end_timestamp":int(end.timestamp()*1000)}
hosts=[
 "https://www.deribit.com/api/v2/public/get_mark_price_history",
 "https://history.deribit.com/api/v2/public/get_mark_price_history"
]
rows=[]
for url in hosts:
    try:
        r=requests.get(url,params=params,timeout=(20,60),headers={"User-Agent":"SRC-Crypto-Lab-MarkDiag/0.1.1"})
        raw=r.content
        rec={"url":url,"status":r.status_code,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
        try:
            obj=r.json()
            if isinstance(obj,dict) and obj.get("error") is not None:
                err=obj["error"]
                rec["error_code"]=err.get("code") if isinstance(err,dict) else None
                rec["error_message"]=err.get("message") if isinstance(err,dict) else str(err)
                data=err.get("data") if isinstance(err,dict) else None
                if isinstance(data,dict):
                    rec["error_data_keys"]=sorted(data.keys())
                    rec["error_data_reason"]=data.get("reason")
                    rec["error_data_param"]=data.get("param")
            else:
                res=obj.get("result") if isinstance(obj,dict) else None
                if isinstance(res,list): rec["result_rows"]=len(res)
                elif isinstance(res,dict):
                    for k in ("data","prices","records","history"):
                        if isinstance(res.get(k),list): rec["result_rows"]=len(res[k]);break
        except Exception as e:
            rec["json_parse_error"]=type(e).__name__
        rows.append(rec)
    except Exception as e:
        rows.append({"url":url,"exception":repr(e)})
out={"instrument":inst,"start":params["start_timestamp"],"end":params["end_timestamp"],"probes":rows,
     "safety":{"prices_retained":False,"returns":False,"pnl":False,"access_2025":False,"access_2026":False,"auth":False}}
(OUT/"MARK_HISTORY_SOURCE_DIAGNOSTIC_V0.1.1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))

from __future__ import annotations
import datetime as dt
import json
import urllib.parse
import urllib.request

UTC=dt.timezone.utc
HOST="history.deribit.com"
PATH="/api/v2/public/get_last_trades_by_currency_and_time"
COUNT=1000
START=dt.datetime(2024,3,12,tzinfo=UTC)
END=dt.datetime(2024,3,13,tzinfo=UTC)
PREFIX="XRP_USDC-"

def request(a:int,b:int):
    q=urllib.parse.urlencode({
        "currency":"USDC","kind":"option","include_old":"true",
        "start_timestamp":a,"end_timestamp":b,"count":COUNT,"sorting":"asc",
    })
    url=f"https://{HOST}{PATH}?{q}"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-XRP-Format-Diagnostic/0.1"})
    with urllib.request.urlopen(req,timeout=90) as resp:
        obj=json.loads(resp.read().decode("utf-8"))
    if obj.get("error"):
        raise RuntimeError(obj["error"])
    result=obj["result"]; rows=result["trades"]
    if result.get("has_more"):
        if b-a<=1000: raise RuntimeError("unsplittable")
        m=a+(b-a)//2
        return request(a,m)+request(m+1,b)
    return rows

def main():
    a=int(START.timestamp()*1000); b=int(END.timestamp()*1000)-1
    rows=request(a,b)
    names=sorted({str(x.get("instrument_name") or "") for x in rows if str(x.get("instrument_name") or "").startswith(PREFIX)})
    out={
        "status":"SOURCE_FORMAT_DIAGNOSTIC_ONLY",
        "window_start":START.isoformat(),"window_end_exclusive":END.isoformat(),
        "source_rows":len(rows),"target_rows":sum(1 for x in rows if str(x.get("instrument_name") or "").startswith(PREFIX)),
        "unique_target_instruments":len(names),
        "sample_instrument_names":names[:80],
        "sample_split_tokens":[{"name":n,"parts":n.split("-"),"part_count":len(n.split("-"))} for n in names[:80]],
        "skew_computed":False,"signal_computed":False,"forward_return_computed":False,
        "pnl_computed":False,"outcome_source_contacted":False,"year_2025_accessed":False,
    }
    print(json.dumps(out,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

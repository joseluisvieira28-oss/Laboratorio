#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.error,urllib.parse,urllib.request
from pathlib import Path

PROGRAMS={
 "kamino_lend":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
 "marginfi_v2":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
 "drift_v2":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
 "save_solend":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
}
UTC_FROM=1734220800
UTC_TO=1734307199
BASE="https://api.solana.fm/v0/accounts/{program}/transactions"

def main():
    out=Path("dls_solanafm_probe"); out.mkdir(exist_ok=True)
    results=[]
    for name,program in PROGRAMS.items():
        q=urllib.parse.urlencode({"utcFrom":UTC_FROM,"utcTo":UTC_TO,"limit":5,"page":1})
        url=BASE.format(program=program)+"?"+q
        rec={"protocol":name,"program_id":program,"url":url}
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"DLS-SOURCE-RECON/0.1","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=30) as r:
                body=r.read(); rec["http_status"]=r.status
            rec["body_sha256"]=hashlib.sha256(body).hexdigest()
            data=json.loads(body)
            rec["json_type"]=type(data).__name__
            if isinstance(data,list):
                rec["row_count"]=len(data)
            elif isinstance(data,dict):
                rec["top_level_keys"]=sorted(data.keys())
                for k in ("result","data","transactions"):
                    if isinstance(data.get(k),list):
                        rec["row_count"]=len(data[k]); rec["row_container"]=k; break
            rec["parseable_json"]=True
            (out/f"{name}.json").write_bytes(body)
        except urllib.error.HTTPError as e:
            rec["http_status"]=e.code
            rec["error"]="HTTPError"
            try:
                b=e.read(); rec["error_body_sha256"]=hashlib.sha256(b).hexdigest()
                rec["error_body_prefix"]=b[:200].decode("utf-8",errors="replace")
            except Exception:
                pass
        except Exception as e:
            rec["error"]=f"{type(e).__name__}:{e}"
        results.append(rec)
    accessible=[x["protocol"] for x in results if x.get("http_status")==200 and x.get("parseable_json")]
    receipt={
      "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"TIME_BOUNDED_INDEXED_ROUTE_ACCESSIBLE" if len(accessible)==4 else ("PARTIAL_INDEXED_ROUTE_ACCESS" if accessible else "INDEXED_ROUTE_ACCESS_BLOCKED"),
      "accessible_protocols":accessible,
      "results":results,
      "source_data_pass":False,
      "prices":False,"returns":False,"pnl":False,"direction":False,"market_response":False,
      "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False
    }
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["fingerprint"]=hashlib.sha256(raw).hexdigest()
    (out/"SOLANAFM_INDEXED_SOURCE_PROBE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()

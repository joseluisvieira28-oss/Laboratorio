#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,urllib.error,urllib.parse,urllib.request
from pathlib import Path

BASE="https://pro-api.solscan.io/playground/account/transactions/enhanced"
FROM_TIME=1734220800
TO_TIME=1734307199

CLASSES=[
 ("save_solend_0x11","So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","11"),
 ("marginfi_liquidate","MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","d6a997d5fba756db"),
 ("kamino_liquidate","KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","b1479abce2854a37"),
 ("drift_liquidate_perp","dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","4b2377f7bf128b02"),
 ("drift_liquidate_spot","dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","6b00802923e5fb12"),
 ("drift_borrow_for_perp_pnl","dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","a911205acf94d11b"),
 ("drift_perp_pnl_for_deposit","dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","ed4bc6ebe9ba4b23"),
]

def _write_receipt(out:Path,receipt:dict):
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["fingerprint"]=hashlib.sha256(raw).hexdigest()
    (out/"SOLSCAN_ENHANCED_SOURCE_PROBE_RECEIPT_V0.1.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print(json.dumps({
      "classification":receipt["classification"],
      "executed":receipt["executed"],
      "class_count":len(receipt.get("results",[])),
      "fingerprint":receipt["fingerprint"],
    },sort_keys=True))

def main():
    out=Path("dls_solscan_enhanced_probe")
    out.mkdir(exist_ok=True)
    token=os.environ.get("SOLSCAN_API_KEY","").strip()
    firewall={
      "source_data_pass":False,"prices":False,"returns":False,"pnl":False,
      "direction":False,"market_response":False,
      "first_success_boundary_adjudicated":False,
      "live_trading":False,"orders":False,"wallets":False,
      "exchange_mutation":False,"merge_main":False
    }
    if not token:
        _write_receipt(out,{
          "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
          "classification":"AUTH_REQUIRED_NOT_EXECUTED",
          "executed":False,
          "credential_source":"SOLSCAN_API_KEY environment variable",
          "results":[],
          "firewall":firewall,
        })
        return

    results=[]
    for name,program,disc in CLASSES:
        params=[
          ("address",program),
          ("from_time",str(FROM_TIME)),
          ("to_time",str(TO_TIME)),
          ("limit","10"),
          ("status","true"),
          ("program[]",program),
          ("instruction[]",program+disc),
          ("encoding","jsonParsed"),
        ]
        url=BASE+"?"+urllib.parse.urlencode(params)
        rec={"class":name,"program_id":program,"discriminator":disc}
        try:
            req=urllib.request.Request(
              url,
              headers={
                "accept":"application/json",
                "token":token,
                "User-Agent":"DLS-SOLSCAN-SOURCE-PROBE/0.1",
              },
            )
            with urllib.request.urlopen(req,timeout=45) as r:
                body=r.read()
                rec["http_status"]=r.status
            rec["body_sha256"]=hashlib.sha256(body).hexdigest()
            data=json.loads(body)
            rec["json_object"]=isinstance(data,dict)
            rec["success"]=data.get("success") if isinstance(data,dict) else None
            payload=data.get("data") if isinstance(data,dict) else None
            txs=payload.get("transactions") if isinstance(payload,dict) else None
            rec["transactions_array"]=isinstance(txs,list)
            rec["transaction_count"]=len(txs) if isinstance(txs,list) else None
            rec["cursor_present"]=bool(payload.get("cursor")) if isinstance(payload,dict) else False
            ok=(r.status==200 and isinstance(data,dict) and data.get("success") is True and isinstance(txs,list))
            rec["schema_pass"]=bool(ok)
            if ok:
                safe={
                  "success":data.get("success"),
                  "data":{
                    "cursor":payload.get("cursor"),
                    "transaction_count":len(txs),
                  },
                }
                (out/f"{name}_summary.json").write_text(
                    json.dumps(safe,indent=2,sort_keys=True)+"\n",encoding="utf-8"
                )
        except urllib.error.HTTPError as e:
            rec["http_status"]=e.code
            rec["error"]="HTTPError"
            try:
                b=e.read()
                rec["error_body_sha256"]=hashlib.sha256(b).hexdigest()
            except Exception:
                pass
        except Exception as e:
            rec["error"]=f"{type(e).__name__}:{e}"
        results.append(rec)

    passed=sum(bool(x.get("schema_pass")) for x in results)
    classification=(
      "SOLSCAN_ENHANCED_SCHEMA_PASS_ALL_CLASSES" if passed==len(results)
      else "SOLSCAN_ENHANCED_PARTIAL_SCHEMA_PASS" if passed
      else "SOLSCAN_ENHANCED_SOURCE_BLOCKED"
    )
    _write_receipt(out,{
      "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":classification,
      "executed":True,
      "credential_source":"SOLSCAN_API_KEY environment variable",
      "schema_pass_classes":passed,
      "results":results,
      "firewall":firewall,
    })

if __name__=="__main__":
    main()

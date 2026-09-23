#!/usr/bin/env python3
import json, urllib.request, urllib.error
from pathlib import Path

BASE="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_TIMESTAMP_SLOT_PROBE_RECEIPT_V0.4.1.json")
controls=[
  {"name":"kamino_first_success","ts":1700232504,"expected_slot":230572965},
  {"name":"save11_first_success","ts":1721417452,"expected_slot":278496102},
  {"name":"window_end","ts":1735689600,"expected_slot":None},
]

rows=[]
for c in controls:
    url=f"{BASE}/{c['ts']}/block"
    rec={"name":c["name"],"timestamp":c["ts"],"url":url,"expected_slot":c["expected_slot"]}
    try:
        req=urllib.request.Request(url,headers={"Accept":"application/json,text/plain,*/*","User-Agent":"crypto-lab-dls-sqd-ts-probe/0.4.1"})
        with urllib.request.urlopen(req,timeout=30) as resp:
            raw=resp.read()
            rec["http_status"]=int(resp.status)
            rec["content_type"]=resp.headers.get("content-type")
            rec["raw_prefix"]=raw[:1000].decode("utf-8","replace")
            parsed=None
            txt=raw.decode("utf-8","replace").strip()
            try: parsed=json.loads(txt)
            except Exception:
                try: parsed=int(txt)
                except Exception: parsed=txt
            rec["parsed"]=parsed
    except urllib.error.HTTPError as e:
        rec["http_status"]=int(e.code)
        rec["error_body"]=e.read(1000).decode("utf-8","replace")
    except Exception as e:
        rec["http_status"]=None
        rec["error"]=type(e).__name__
        rec["detail"]=str(e)[:500]
    rows.append(rec)

def extract_slot(v):
    if isinstance(v,int): return v
    if isinstance(v,dict):
        for k in ("block","slot","number","height"):
            if isinstance(v.get(k),int): return v[k]
    return None

known=[]
for r in rows[:2]:
    r["resolved_slot"]=extract_slot(r.get("parsed"))
    r["exact_expected_match"]=r["resolved_slot"]==r["expected_slot"]
    known.append(r["exact_expected_match"])

end_slot=extract_slot(rows[2].get("parsed"))
rows[2]["resolved_slot"]=end_slot
classification="SQD_TIMESTAMP_SLOT_RESOLVER_PASS" if all(known) and isinstance(end_slot,int) else "SQD_TIMESTAMP_SLOT_RESOLVER_FAIL_CLOSED"

receipt={
  "schema_version":"0.4.1",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "rows":rows,
  "firewall":{
    "prices":False,"balances":False,"token_balances":False,"amounts":False,
    "returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
    "protected_market_outcomes_2025_2026":False,"live_trading":False,
    "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
    "account_creation":False,"merge_main":False
  }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="SQD_TIMESTAMP_SLOT_RESOLVER_PASS":
    raise SystemExit(2)

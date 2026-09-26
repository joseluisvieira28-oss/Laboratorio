#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
SLOT=110526981
TARGETS=[
 "GsXfKKyK2pDm4Tn8WdYBzfGUrSBDFh4ZGh7y2SV7sTtc",
 "9c9JC96jg7nSovijiTpxWQAXvLMf6sbMuT9jR6RFRqb3",
]
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_HISTORICAL_TOKEN_IDENTITY_RECEIPT_V0.2.json")

def req(body,retries=10):
    data=json.dumps(body,separators=(",",":")).encode()
    request=urllib.request.Request(
        STREAM,data=data,
        headers={"Accept":"application/x-ndjson,application/json",
                 "Content-Type":"application/json",
                 "User-Agent":"crypto-lab-save0c-token-identity/0.2"},
        method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as r:
                return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code}; time.sleep(min(45,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

body={
 "type":"solana",
 "fromBlock":SLOT,
 "toBlock":SLOT,
 "fields":{
   "block":{"number":True},
   "tokenBalance":{"account":True,"preMint":True,"postMint":True}
 },
 "tokenBalances":[{"account":TARGETS}]
}
st,h,raw=req(body)
receipt={
 "schema_version":"0.2",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "slot":SLOT,
 "http_status":st,
 "classification":"SAVE0C_HISTORICAL_TOKEN_IDENTITY_FAIL_CLOSED",
 "targets":[],
 "requested_fields":["account","preMint","postMint"],
 "forbidden_fields_requested":False,
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"balances":False,"token_amounts":False,
             "token_decimals":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}
}
found={a:[] for a in TARGETS}
if st==200:
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip(): continue
        b=json.loads(line)
        for tb in b.get("tokenBalances") or []:
            a=tb.get("account")
            if a in found:
                found[a].append({
                  "account":a,
                  "preMint":tb.get("preMint"),
                  "postMint":tb.get("postMint")
                })

passes=[]
for a in TARGETS:
    recs=found[a]
    ok=any(bool(r.get("preMint") or r.get("postMint")) for r in recs)
    passes.append(ok)
    receipt["targets"].append({
      "account":a,
      "record_count":len(recs),
      "mint_identity_present":ok,
      "records":recs
    })

if st==200 and len(passes)==2 and all(passes):
    receipt["classification"]="SAVE0C_HISTORICAL_TOKEN_IDENTITY_2_OF_2_PASS"

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"]!="SAVE0C_HISTORICAL_TOKEN_IDENTITY_2_OF_2_PASS":
    raise SystemExit(2)

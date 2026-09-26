#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/INSTRUCTION_TOKEN_BALANCE_RELATION_DIAGNOSTIC_RECEIPT_V0.2.json")
REFS=[
 {"name":"save0c","slot":110526981,"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","filter":"d1","disc":"0x0c",
  "signature":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V",
  "targets":{"GsXfKKyK2pDm4Tn8WdYBzfGUrSBDFh4ZGh7y2SV7sTtc":["SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",6]}},
 {"name":"save11","slot":278496102,"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","filter":"d1","disc":"0x11",
  "signature":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
  "targets":{"A7srL2Wek9hmkinB7zX5Zx88wf3BTFuquVDUwHMwvKoq":["jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",9]}},
 {"name":"kamino","slot":230572965,"program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","filter":"d8","disc":"0xb1479abce2854a37",
  "signature":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
  "targets":{"Bgq7trRgVMeq33yt235zM2onQ4bRDBsY5EWiTetF4qw6":["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",6]}}
]

def req(body,retries=8):
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json","Content-Type":"application/json",
      "User-Agent":"crypto-lab-dls-token-balance-relation-diag/0.2"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":raw[:500].decode("utf-8","replace")};time.sleep(min(45,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

results=[]
for ref in REFS:
    filt={"programId":[ref["program"]],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}
    filt[ref["filter"]]=[ref["disc"]]
    body={"type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True},
            "tokenBalance":{"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True}
          },
          "instructions":[filt]}
    st,h,raw=req(body)
    rr={"name":ref["name"],"http_status":st,"block_count":0,"block_keys":[],"token_balance_total":0,
        "token_balance_tx_indices":[],"instruction_matches":[],"target_results":[],"pass":False}
    if st!=200:
        rr["error_body"]=raw[:1000].decode("utf-8","replace");results.append(rr);continue
    found={}
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip():continue
        b=json.loads(line);rr["block_count"]+=1;rr["block_keys"].append(sorted(b.keys()))
        tbs=b.get("tokenBalances") or []
        rr["token_balance_total"]+=len(tbs)
        rr["token_balance_tx_indices"]+=sorted({tb.get("transactionIndex") for tb in tbs if tb.get("transactionIndex") is not None})
        for tb in tbs:
            a=tb.get("account"); pairs=set()
            if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
                pairs.add((tb["preMint"],tb["preDecimals"]))
            if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
                pairs.add((tb["postMint"],tb["postDecimals"]))
            if a:found.setdefault(a,set()).update(pairs)
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            tx=tx_by.get(ix.get("transactionIndex"))
            sigs=(tx or {}).get("signatures") or []
            sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            if ix.get("programId")==ref["program"] and sig==ref["signature"]:
                rr["instruction_matches"].append({
                  "transactionIndex":ix.get("transactionIndex"),
                  "instructionAddress":ix.get("instructionAddress"),
                  "isCommitted":ix.get("isCommitted"),
                  "transactionErr":(tx or {}).get("err")
                })
    all_ok=bool(rr["instruction_matches"])
    for account,exp in ref["targets"].items():
        observed=sorted(found.get(account,set()))
        ok=(observed==[(exp[0],exp[1])])
        rr["target_results"].append({"account":account,"expected":{"mint":exp[0],"decimals":exp[1]},
                                     "observed":[{"mint":m,"decimals":d} for m,d in observed],"pass":ok})
        all_ok=all_ok and ok
    rr["pass"]=all_ok;results.append(rr)

passed=sum(1 for r in results if r["pass"])
any_tb=any(r["token_balance_total"]>0 for r in results)
if passed==3:
    classification="INSTRUCTION_TOKEN_BALANCE_RELATION_3_OF_3_REFERENCE_PASS"
elif not any_tb and all(r["http_status"]==200 and r["instruction_matches"] for r in results):
    classification="INSTRUCTION_TOKEN_BALANCE_RELATION_RAW_PORTAL_NOT_MATERIALIZED"
else:
    classification="INSTRUCTION_TOKEN_BALANCE_RELATION_DIAGNOSTIC_FAIL_CLOSED"

receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
         "reference_count":3,"pass_count":passed,"results":results,"amount_fields_requested":False,
         "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
                     "economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
                     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"paid_source":False,"account_creation":False,
                     "post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="INSTRUCTION_TOKEN_BALANCE_RELATION_DIAGNOSTIC_FAIL_CLOSED":raise SystemExit(2)

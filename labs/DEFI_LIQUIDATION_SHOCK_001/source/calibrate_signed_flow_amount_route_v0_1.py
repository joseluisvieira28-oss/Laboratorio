#!/usr/bin/env python3
import json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SIGNED_FLOW_AMOUNT_ROUTE_CALIBRATION_RECEIPT_V0.1.json")
REFS=[
 {"name":"save0c","slot":110526981,"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","filter":"d1","disc":"0x0c",
  "signature":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V",
  "targets":["GsXfKKyK2pDm4Tn8WdYBzfGUrSBDFh4ZGh7y2SV7sTtc","9c9JC96jg7nSovijiTpxWQAXvLMf6sbMuT9jR6RFRqb3","4JHVBtmMPFyRpidxHtM8gVjGuLBXhaXCF4jNFFKBdGpb","6uEjo58ecepRyYnKRLdAMRn8ic3oJJxnwMBH96ufMSXN"]},
 {"name":"save11","slot":278496102,"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","filter":"d1","disc":"0x11",
  "signature":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
  "targets":["A7srL2Wek9hmkinB7zX5Zx88wf3BTFuquVDUwHMwvKoq","4AfbHQzPc1rLEYSjwtDHtCqm6m2g56BG9qAKRiJKsn5c","9nbeqZZnL21hqHKQRsqFK4A7hGHLrkNpiuanHK7c7KPD","8UviNr47S8eL6J3WfDxMRa3hvLta1VDJwNWqsDgtN3Cv"]},
 {"name":"kamino","slot":230572965,"program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","filter":"d8","disc":"0xb1479abce2854a37",
  "signature":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
  "targets":["Bgq7trRgVMeq33yt235zM2onQ4bRDBsY5EWiTetF4qw6","GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U","2mwjbrnNgYTBN8PedkWXdvDd8JdZr1uMdX6iu4vs9tZs","BRTfi2ahsyzQU5Mmg9rbKjxHxx2MVmtVWsZ51CZfTREQ"]}
]

def req(body,retries=8):
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json","Content-Type":"application/json",
      "User-Agent":"crypto-lab-dls-signed-flow-amount/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":raw[:500].decode("utf-8","replace")};time.sleep(min(45,2**i));continue
            return int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def as_int(v):
    if v is None:return None
    try:return int(v)
    except Exception:return None

results=[]
for ref in REFS:
    filt={"programId":[ref["program"]],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}
    filt[ref["filter"]]=[ref["disc"]]
    body={"type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
          "fields":{
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True},
            "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True,
                            "preOwner":True,"postOwner":True,"preAmount":True,"postAmount":True}
          },"instructions":[filt]}
    st,raw=req(body)
    rr={"name":ref["name"],"http_status":st,"instruction_match":False,"token_balance_total":0,"token_balance_tx_indices":[],"raw_token_balance_sample":[],"target_rows":[],"parseable_target_count":0,"nonzero_delta_target_count":0,"pass":False}
    if st!=200:
        rr["error_body"]=raw[:1000].decode("utf-8","replace");results.append(rr);continue
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip():continue
        b=json.loads(line)
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        tbs_all=b.get("tokenBalances") or []
        rr["token_balance_total"]+=len(tbs_all)
        rr["token_balance_tx_indices"]+=sorted({tb.get("transactionIndex") for tb in tbs_all if tb.get("transactionIndex") is not None})
        for tb in tbs_all[:20]:
            rr["raw_token_balance_sample"].append({
              "transactionIndex":tb.get("transactionIndex"),"account":tb.get("account"),
              "preMint":tb.get("preMint"),"postMint":tb.get("postMint"),
              "preAmount":str(tb.get("preAmount")) if tb.get("preAmount") is not None else None,
              "postAmount":str(tb.get("postAmount")) if tb.get("postAmount") is not None else None,
              "preOwner":tb.get("preOwner"),"postOwner":tb.get("postOwner")
            })
        wanted_ti=None
        for ix in b.get("instructions") or []:
            tx=tx_by.get(ix.get("transactionIndex")) or {}
            sigs=tx.get("signatures") or []
            sig=sigs[0] if sigs else None
            if ix.get("programId")==ref["program"] and sig==ref["signature"] and tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None:
                rr["instruction_match"]=True;wanted_ti=ix.get("transactionIndex");break
        if wanted_ti is None:continue
        exact_matches=[]
        for ix in b.get("instructions") or []:
            tx=tx_by.get(ix.get("transactionIndex")) or {}
            sigs=tx.get("signatures") or []
            sig=sigs[0] if sigs else None
            if ix.get("programId")==ref["program"] and sig==ref["signature"] and tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None:
                exact_matches.append(ix)
        if len(exact_matches)!=1:
            rr["binding_error"]="exact_reference_instruction_match_count_"+str(len(exact_matches))
            continue
        wanted_ti=exact_matches[0].get("transactionIndex")
        merged={}
        for tb in b.get("tokenBalances") or []:
            if tb.get("account") not in ref["targets"]:continue
            tb_ti=tb.get("transactionIndex")
            if tb_ti is not None and tb_ti!=wanted_ti:continue
            a=tb.get("account")
            m=merged.setdefault(a,{"account":a})
            for k in ("preMint","postMint","preDecimals","postDecimals","preOwner","postOwner","preAmount","postAmount"):
                if tb.get(k) is not None:m[k]=tb.get(k)
        for a,m in sorted(merged.items()):
            pre=as_int(m.get("preAmount"));post=as_int(m.get("postAmount"))
            rr["target_rows"].append({
                "account":a,
                "preMint":m.get("preMint"),"postMint":m.get("postMint"),
                "preDecimals":m.get("preDecimals"),"postDecimals":m.get("postDecimals"),
                "preOwner":m.get("preOwner"),"postOwner":m.get("postOwner"),
                "preAmount":str(m.get("preAmount")) if m.get("preAmount") is not None else None,
                "postAmount":str(m.get("postAmount")) if m.get("postAmount") is not None else None,
                "delta_raw":(post-pre) if pre is not None and post is not None else None
            })
    rr["parseable_target_count"]=sum(1 for x in rr["target_rows"] if x["delta_raw"] is not None)
    rr["nonzero_delta_target_count"]=sum(1 for x in rr["target_rows"] if x["delta_raw"] not in (None,0))
    rr["pass"]=rr["instruction_match"] and rr["parseable_target_count"]>=2 and rr["nonzero_delta_target_count"]>=1
    results.append(rr)

passed=sum(1 for r in results if r["pass"])
classification="SIGNED_FLOW_AMOUNT_ROUTE_3_OF_3_PASS" if passed==3 else "SIGNED_FLOW_AMOUNT_ROUTE_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "reference_count":3,"pass_count":passed,"results":results,
 "direction_assigned":False,
 "firewall":{"prices":False,"returns":False,"usd_notional":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"pass_count":passed,"results":results},indent=2))
if classification!="SIGNED_FLOW_AMOUNT_ROUTE_3_OF_3_PASS":raise SystemExit(2)

#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/INSTRUCTION_TOKEN_BALANCE_RELATION_CALIBRATION_RECEIPT_V0.1.json")
REFS=[
 {"name":"save0c","slot":110526981,"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"0c",
  "signature":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V",
  "targets":{
    "GsXfKKyK2pDm4Tn8WdYBzfGUrSBDFh4ZGh7y2SV7sTtc":("SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",6),
    "9c9JC96jg7nSovijiTpxWQAXvLMf6sbMuT9jR6RFRqb3":("2d95ZC8L5XP6xCnaKx8D5U5eX6rKbboBBAwuBLxaFmmJ",6),
    "4JHVBtmMPFyRpidxHtM8gVjGuLBXhaXCF4jNFFKBdGpb":("SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",6),
    "6uEjo58ecepRyYnKRLdAMRn8ic3oJJxnwMBH96ufMSXN":("2d95ZC8L5XP6xCnaKx8D5U5eX6rKbboBBAwuBLxaFmmJ",6)
  }},
 {"name":"save11","slot":278496102,"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"11",
  "signature":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
  "targets":{
    "A7srL2Wek9hmkinB7zX5Zx88wf3BTFuquVDUwHMwvKoq":("jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",9),
    "4AfbHQzPc1rLEYSjwtDHtCqm6m2g56BG9qAKRiJKsn5c":("5h6ssFpeDeRbzsEHDbTQNH7nVGgsKrZydxdSTnLm6QdV",9),
    "9nbeqZZnL21hqHKQRsqFK4A7hGHLrkNpiuanHK7c7KPD":("jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",9),
    "8UviNr47S8eL6J3WfDxMRa3hvLta1VDJwNWqsDgtN3Cv":("So11111111111111111111111111111111111111112",9)
  }},
 {"name":"kamino","slot":230572965,"program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix":"b1479abce2854a37",
  "signature":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
  "targets":{
    "Bgq7trRgVMeq33yt235zM2onQ4bRDBsY5EWiTetF4qw6":("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",6),
    "GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U":("So11111111111111111111111111111111111111112",9),
    "2mwjbrnNgYTBN8PedkWXdvDd8JdZr1uMdX6iu4vs9tZs":("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",6),
    "BRTfi2ahsyzQU5Mmg9rbKjxHxx2MVmtVWsZ51CZfTREQ":("So11111111111111111111111111111111111111112",9)
  }}
]

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def req(body,retries=8):
    data=json.dumps(body,separators=(",",":")).encode()
    request=urllib.request.Request(STREAM,data=data,headers={"Accept":"application/x-ndjson,application/json","Content-Type":"application/json","User-Agent":"crypto-lab-dls-instruction-token-balance-relation/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
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
    body={"type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
          "fields":{
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True},
            "tokenBalance":{"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True}
          },
          "instructions":[{
            "programId":[ref["program"]],
            "transaction":True,
            "transactionTokenBalances":True
          }]}
    st,h,raw=req(body)
    rr={"name":ref["name"],"http_status":st,"instruction_match":False,"token_balance_count":0,
        "target_results":[],"pass":False}
    if st==200:
        found={}
        for line in raw.decode("utf-8","replace").splitlines():
            if not line.strip():continue
            b=json.loads(line);tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            wanted_ti=None
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=ref["program"]:continue
                tx=tx_by.get(ix.get("transactionIndex"))
                if not isinstance(tx,dict):continue
                sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                if sig!=ref["signature"]:continue
                try:dec=b58decode(ix.get("data",""))
                except Exception:continue
                if not dec.startswith(bytes.fromhex(ref["prefix"])):continue
                if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
                rr["instruction_match"]=True;wanted_ti=ix.get("transactionIndex");break
            if wanted_ti is None:continue
            tbs=[tb for tb in (b.get("tokenBalances") or []) if tb.get("transactionIndex")==wanted_ti]
            rr["token_balance_count"]+=len(tbs)
            for tb in tbs:
                a=tb.get("account")
                pairs=[]
                if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
                    pairs.append((tb["preMint"],tb["preDecimals"]))
                if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
                    pairs.append((tb["postMint"],tb["postDecimals"]))
                if a:
                    found.setdefault(a,set()).update(pairs)
        all_ok=rr["instruction_match"]
        for account,(mint,decimals) in ref["targets"].items():
            pairs=sorted(found.get(account,set()))
            ok=(pairs==[(mint,decimals)])
            rr["target_results"].append({"account":account,"expected_mint":mint,"expected_decimals":decimals,
                                         "observed":[{"mint":m,"decimals":d} for m,d in pairs],"pass":ok})
            all_ok=all_ok and ok
        rr["pass"]=all_ok
    else:
        rr["error_body"]=raw[:1000].decode("utf-8","replace")
    results.append(rr)

passed=sum(1 for r in results if r["pass"])
classification="INSTRUCTION_TOKEN_BALANCE_RELATION_3_OF_3_REFERENCE_PASS" if passed==3 else "INSTRUCTION_TOKEN_BALANCE_RELATION_CALIBRATION_FAIL_CLOSED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
         "reference_count":3,"pass_count":passed,"results":results,
         "amount_fields_requested":False,
         "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
                     "economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
                     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="INSTRUCTION_TOKEN_BALANCE_RELATION_3_OF_3_REFERENCE_PASS":raise SystemExit(2)

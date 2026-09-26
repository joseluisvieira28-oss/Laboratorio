#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/FIELD_DECODER_IMPLEMENTATION_VALIDATION_RECEIPT_V0.1.json")
REFS=[
 {"name":"save0c","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"0c","slot":110526981,"sig":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V","accounts":12,"kind":"save_u64"},
 {"name":"save11","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"11","slot":278496102,"sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L","accounts":15,"kind":"save_u64"},
 {"name":"marginfi","program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","prefix":"d6a997d5fba756db","slot":177590210,"sig":"2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK","min_accounts":10,"kind":"anchor_u64"},
 {"name":"kamino","program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix":"b1479abce2854a37","slot":230572965,"sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv","accounts":16,"kind":"anchor_3u64"},
 {"name":"drift_liquidate_perp","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"4b2377f7bf128b02","slot":159692675,"sig":"4r37rDVwUvdxJjJsx5fa5kXm8obE6TAn9czVMnMABDXa6L6QnQQnoRTmF9Kct5Cx5HUD8a3GB9P9cebSUQqDERad","min_accounts":6,"kind":"drift_perp"},
 {"name":"drift_liquidate_spot","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"6b00802923e5fb12","slot":159863566,"sig":"6Nna7TV5aSH2uczPrT3mHGMjsVKtLf49TF6C823tLY9ZdSpbdQYbB4tMtNUXKEoQ3VEC4cbzRS49KMcZEakjYVm","min_accounts":6,"kind":"drift_u16_u16_u128_opt"},
 {"name":"drift_liquidate_borrow_for_perp_pnl","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"a911205acf94d11b","slot":195239739,"sig":"5kYZPtPTFhvdBZfaFMPXtWh2A9tQYHt8bbzKJazopc7pWWmpwdcn1DeT4yLjxaidn387VMK6g6rYX4KMMh7NPka6","min_accounts":6,"kind":"drift_u16_u16_u128_opt"},
 {"name":"drift_liquidate_perp_pnl_for_deposit","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"ed4bc6ebe9ba4b23","slot":159694878,"sig":"3sRvzJkuuqMPhftGKSqiPJVJ72u6fyiyUYfWB4pqA3o6y9HcNvWsydVFe9iNtvZzkMXBoCDvgaontLzAnYArzxBi","min_accounts":6,"kind":"drift_u16_u16_u128_opt"}
]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";MAP={c:i for i,c in enumerate(ALPH)}
def b58(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def req(body):
    data=json.dumps(body,separators=(",",":")).encode()
    rq=urllib.request.Request(STREAM,data=data,headers={"Content-Type":"application/json","Accept":"application/x-ndjson","User-Agent":"crypto-lab-field-decoder-validation/0.1"})
    for i in range(10):
        try:
            with urllib.request.urlopen(rq,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if e.code==429 or 500<=e.code<600: time.sleep(min(45,2**i));continue
            return e.code,e.read()
        except Exception: time.sleep(min(45,2**i))
    raise RuntimeError("transport_exhausted")
def validate_layout(kind,d):
    if kind=="save_u64": return len(d)==9
    if kind=="anchor_u64": return len(d)==16
    if kind=="anchor_3u64": return len(d)==32
    if kind=="drift_perp":
        if len(d)<19:return False
        opt=d[18]
        return (opt==0 and len(d)==19) or (opt==1 and len(d)==27)
    if kind=="drift_u16_u16_u128_opt":
        if len(d)<29:return False
        opt=d[28]
        return (opt==0 and len(d)==29) or (opt==1 and len(d)==37)
    return False

results=[]
for ref in REFS:
    body={"type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
          "fields":{"transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True}},
          "instructions":[{"programId":[ref["program"]],"transaction":True}]}
    st,raw=req(body);matches=[]
    if st==200:
        for line in raw.decode("utf-8","replace").splitlines():
            if not line.strip():continue
            block=json.loads(line);txs={}
            for pos,tx in enumerate(block.get("transactions") or []):
                txs[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in block.get("instructions") or []:
                if ix.get("programId")!=ref["program"]:continue
                tx=txs.get(ix.get("transactionIndex"))
                if not isinstance(tx,dict):continue
                sigs=tx.get("signatures") or []
                if not sigs or sigs[0]!=ref["sig"]:continue
                try:d=b58(ix.get("data") or "")
                except Exception:continue
                if not d.startswith(bytes.fromhex(ref["prefix"])):continue
                ac=len(ix.get("accounts") or [])
                count_ok=(ac==ref["accounts"]) if "accounts" in ref else (ac>=ref["min_accounts"])
                matches.append({"account_count":ac,"account_count_pass":count_ok,
                                "data_length":len(d),"layout_pass":validate_layout(ref["kind"],d),
                                "execution_pass":tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None})
    ok=bool(matches) and all(x["account_count_pass"] and x["layout_pass"] and x["execution_pass"] for x in matches)
    results.append({"name":ref["name"],"http_status":st,"match_count":len(matches),"matches":matches,"pass":ok})
passed=sum(1 for x in results if x["pass"])
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"FIELD_DECODER_IMPLEMENTATION_8_OF_8_PASS" if passed==8 else "FIELD_DECODER_IMPLEMENTATION_VALIDATION_FAIL_CLOSED",
 "reference_count":8,"pass_count":passed,"results":results,
 "numeric_argument_values_emitted":False,
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "balances":False,"token_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if passed!=8:raise SystemExit(2)

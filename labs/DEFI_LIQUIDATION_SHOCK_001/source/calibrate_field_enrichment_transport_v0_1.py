#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/FIELD_ENRICHMENT_TRANSPORT_CALIBRATION_RECEIPT_V0.1.json")

REFS=[
 {"name":"save0c","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"0c","slot":110526981,
  "signature":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V","addr":[3]},
 {"name":"save11","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"11","slot":278496102,
  "signature":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L","addr":None},
 {"name":"marginfi","program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","prefix":"d6a997d5fba756db","slot":177590210,
  "signature":"2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK","addr":[0]},
 {"name":"kamino","program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix":"b1479abce2854a37","slot":230572965,
  "signature":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv","addr":None},
 {"name":"drift_liquidate_perp","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"4b2377f7bf128b02","slot":159692675,
  "signature":"4r37rDVwUvdxJjJsx5fa5kXm8obE6TAn9czVMnMABDXa6L6QnQQnoRTmF9Kct5Cx5HUD8a3GB9P9cebSUQqDERad","addr":[1]},
 {"name":"drift_liquidate_perp_pnl_for_deposit","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"ed4bc6ebe9ba4b23","slot":159694878,
  "signature":"3sRvzJkuuqMPhftGKSqiPJVJ72u6fyiyUYfWB4pqA3o6y9HcNvWsydVFe9iNtvZzkMXBoCDvgaontLzAnYArzxBi","addr":[1]},
 {"name":"drift_liquidate_spot","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"6b00802923e5fb12","slot":159863566,
  "signature":"6Nna7TV5aSH2uczPrT3mHGMjsVKtLf49TF6C823tLY9ZdSpbdQYbB4tMtNUXKEoQ3VEC4cbzRS49KMcZEakjYVm","addr":[1]},
 {"name":"drift_liquidate_borrow_for_perp_pnl","program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH","prefix":"a911205acf94d11b","slot":195239739,
  "signature":"5kYZPtPTFhvdBZfaFMPXtWh2A9tQYHt8bbzKJazopc7pWWmpwdcn1DeT4yLjxaidn387VMK6g6rYX4KMMh7NPka6","addr":[1]}
]

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def req(body,retries=10):
    data=json.dumps(body,separators=(",",":")).encode()
    request=urllib.request.Request(STREAM,data=data,headers={
        "Accept":"application/x-ndjson,application/json",
        "Content-Type":"application/json",
        "User-Agent":"crypto-lab-dls-field-enrichment-cal/0.1"
    },method="POST")
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

results=[]
for ref in REFS:
    body={
      "type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
      "fields":{
        "block":{"number":True,"timestamp":True},
        "transaction":{"transactionIndex":True,"signatures":True,"err":True,"accountKeys":True},
        "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                       "instructionAddress":True,"isCommitted":True,"error":True}
      },
      "instructions":[{"programId":[ref["program"]],"transaction":True}]
    }
    st,h,raw=req(body)
    out={"name":ref["name"],"slot":ref["slot"],"signature":ref["signature"],"program":ref["program"],
         "prefix":ref["prefix"],"http_status":st,"pass":False}
    if st!=200:
        out["reason"]=f"http_{st}"
        results.append(out); continue
    lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    matches=[]
    for line in lines:
        b=json.loads(line)
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            idx=tx.get("transactionIndex",tx.get("index",pos)); tx_by[idx]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=ref["program"]: continue
            ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
            if not isinstance(tx,dict): continue
            sigs=tx.get("signatures") or []
            sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            if sig!=ref["signature"]: continue
            data=ix.get("data")
            try: dec=b58decode(data or "")
            except Exception: continue
            if not dec.startswith(bytes.fromhex(ref["prefix"])): continue
            matches.append({
              "instructionAddress":ix.get("instructionAddress"),
              "accounts":ix.get("accounts"),
              "account_count":len(ix.get("accounts") or []),
              "transaction_account_key_count":len(tx.get("accountKeys") or []),
              "data_base58_length":len(data or ""),
              "decoded_data_byte_length":len(dec),
              "decoded_prefix_hex":dec[:len(bytes.fromhex(ref["prefix"]))].hex(),
              "transactionErr":tx.get("err"),
              "isCommitted":ix.get("isCommitted"),
              "instructionError":ix.get("error")
            })
    out["matches"]=matches
    good=[]
    for m in matches:
        addr_ok=(ref["addr"] is None or m.get("instructionAddress")==ref["addr"])
        good.append(addr_ok and m.get("account_count",0)>0 and m.get("decoded_data_byte_length",0)>0
                    and m.get("transactionErr") is None and m.get("isCommitted") is True
                    and m.get("instructionError") is None)
    out["pass"]=any(good)
    if not out["pass"]:
        out["reason"]="identity_or_accounts_or_execution_mismatch"
    results.append(out)

passed=sum(1 for x in results if x["pass"])
receipt={
  "schema_version":"0.1",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":"FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS" if passed==len(REFS) else "FIELD_ENRICHMENT_TRANSPORT_CALIBRATION_FAIL_CLOSED",
  "reference_count":len(REFS),"pass_count":passed,"results":results,
  "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
              "balances":False,"token_amounts":False,"protected_market_outcomes_2025_2026":False,
              "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
              "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"]!="FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS":
    raise SystemExit(2)

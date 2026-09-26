#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/LENDING_TOKEN_UNIT_METADATA_CALIBRATION_RECEIPT_V0.1.json")

REFS=[
 {"name":"save0c","slot":110526981,"signature":"3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V",
  "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"0c",
  "positions":{"source_liquidity_token_account":0,"destination_collateral_token_account":1,
               "repay_reserve_liquidity_supply":3,"withdraw_reserve_collateral_supply":5}},
 {"name":"save11","slot":278496102,"signature":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
  "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"11",
  "positions":{"source_liquidity":0,"destination_collateral":1,
               "repay_reserve_liquidity_supply":4,"withdraw_reserve_liquidity_supply":8}},
 {"name":"kamino","slot":230572965,"signature":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
  "program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix":"b1479abce2854a37",
  "positions":{"repay_reserve_liquidity_supply":5,"withdraw_reserve_liquidity_supply":9,
               "user_source_liquidity":11,"user_destination_liquidity":13}}
]

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def req(body,retries=10):
    data=json.dumps(body,separators=(",",":")).encode()
    request=urllib.request.Request(STREAM,data=data,headers={"Accept":"application/x-ndjson,application/json","Content-Type":"application/json","User-Agent":"crypto-lab-dls-unit-metadata/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(45,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

results=[]; total_pass=0; total_targets=0
for ref in REFS:
    ibody={"type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
           "fields":{"transaction":{"transactionIndex":True,"signatures":True,"err":True},
                     "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                    "instructionAddress":True,"isCommitted":True,"error":True}},
           "instructions":[{"programId":[ref["program"]],"transaction":True}]}
    st,h,raw=req(ibody)
    rr={"name":ref["name"],"slot":ref["slot"],"signature":ref["signature"],"instruction_match":False,"targets":[]}
    accounts=None
    if st==200:
        for line in raw.decode("utf-8","replace").splitlines():
            if not line.strip():continue
            b=json.loads(line); tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=ref["program"]:continue
                tx=tx_by.get(ix.get("transactionIndex"))
                if not isinstance(tx,dict):continue
                sigs=tx.get("signatures") or []
                sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                if sig!=ref["signature"]:continue
                try:dec=b58decode(ix.get("data",""))
                except Exception:continue
                if not dec.startswith(bytes.fromhex(ref["prefix"])):continue
                if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
                accounts=ix.get("accounts") or []; rr["instruction_match"]=True
                break
            if accounts is not None:break
    if accounts is None:
        rr["classification"]="REFERENCE_INSTRUCTION_NOT_RECOVERED"
        results.append(rr);continue

    target_map={}
    for role,pos in ref["positions"].items():
        total_targets+=1
        target_map[role]=accounts[pos] if pos<len(accounts) else None
    valid_accounts=[a for a in target_map.values() if isinstance(a,str) and a]

    tbody={"type":"solana","fromBlock":ref["slot"],"toBlock":ref["slot"],
           "fields":{"tokenBalance":{"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True}},
           "tokenBalances":[{"account":valid_accounts}]}
    tst,th,traw=req(tbody)
    found={a:[] for a in valid_accounts}
    if tst==200:
        for line in traw.decode("utf-8","replace").splitlines():
            if not line.strip():continue
            b=json.loads(line)
            for tb in b.get("tokenBalances") or []:
                a=tb.get("account")
                if a in found:
                    found[a].append({"preMint":tb.get("preMint"),"postMint":tb.get("postMint"),
                                     "preDecimals":tb.get("preDecimals"),"postDecimals":tb.get("postDecimals")})

    ref_pass=True
    for role,pos in ref["positions"].items():
        account=target_map.get(role); recs=found.get(account,[]) if account else []
        pairs=[]
        for x in recs:
            if isinstance(x.get("preMint"),str) and isinstance(x.get("preDecimals"),int):
                pairs.append((x["preMint"],x["preDecimals"]))
            if isinstance(x.get("postMint"),str) and isinstance(x.get("postDecimals"),int):
                pairs.append((x["postMint"],x["postDecimals"]))
        uniq=sorted(set(pairs))
        ok=(account is not None and len(uniq)==1)
        if ok: total_pass+=1
        else: ref_pass=False
        rr["targets"].append({"role":role,"position":pos,"account":account,"record_count":len(recs),
                              "metadata_pairs":[{"mint":m,"decimals":d} for m,d in uniq],"pass":ok})
    rr["classification"]="REFERENCE_TOKEN_UNIT_METADATA_PASS" if ref_pass else "REFERENCE_TOKEN_UNIT_METADATA_FAIL_CLOSED"
    results.append(rr)

classification="LENDING_TOKEN_UNIT_METADATA_12_OF_12_ACCOUNT_PASS" if total_targets==12 and total_pass==12 else "LENDING_TOKEN_UNIT_METADATA_CALIBRATION_FAIL_CLOSED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
         "reference_count":len(REFS),"target_account_count":total_targets,"pass_count":total_pass,"results":results,
         "requested_token_balance_fields":["account","preMint","postMint","preDecimals","postDecimals"],
         "amount_fields_requested":False,
         "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
                     "economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
                     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="LENDING_TOKEN_UNIT_METADATA_12_OF_12_ACCOUNT_PASS":raise SystemExit(2)

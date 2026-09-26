#!/usr/bin/env python3
import base64, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_INDEPENDENT_ABI_RECONCILIATION_RECEIPT_V0.1.json")
SOLEND="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
TOKEN="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
CLOCK="SysvarC1ock11111111111111111111111111111111"
SIG="3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V"
SLOT=110526981
ADDR=[3]
ACCOUNTS=[
 "GsXfKKyK2pDm4Tn8WdYBzfGUrSBDFh4ZGh7y2SV7sTtc",
 "9c9JC96jg7nSovijiTpxWQAXvLMf6sbMuT9jR6RFRqb3",
 "5suXmvdbKQ98VonxGCXqViuWRu8k4zgZRxndYKsH2fJg",
 "4JHVBtmMPFyRpidxHtM8gVjGuLBXhaXCF4jNFFKBdGpb",
 "9n2exoMQwMTzfw6NFoFFujxYPndWVLtKREJePssrKb36",
 "6uEjo58ecepRyYnKRLdAMRn8ic3oJJxnwMBH96ufMSXN",
 "dcHivNNFDPuQKCuojVN5Da1dAc7gAPHaojJWrKN5C6T",
 "4UpD2fh7xH3VP9QQaXtsS1YY3bxzWhtfpks7FatyKvdY",
 "DdZR6zRFiUt4S5mg7AV1uKB2z1f1WzcNYCaTEEWPAuby",
 "F4q2bm6k4AW2rgQMBfvoNnfn1xFkoD98We6uJd6tV7tq",
 CLOCK,
 TOKEN
]
EXPECTED_OWNERS={0:TOKEN,1:TOKEN,2:SOLEND,3:TOKEN,4:SOLEND,5:TOKEN,6:SOLEND,7:SOLEND}

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def rpc(method,params,retries=10):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-save0c-abi/0.1"})
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=60) as r:
                obj=json.loads(r.read())
            if obj.get("error"):
                code=(obj.get("error") or {}).get("code")
                if code in (-32005,429):
                    last=obj["error"]; time.sleep(min(45,2*(i+1))); continue
            return obj
        except urllib.error.HTTPError as e:
            last={"http":e.code}
            if e.code in (429,500,502,503,504):
                time.sleep(min(45,2*(i+1))); continue
            raise
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(45,2*(i+1)))
    raise RuntimeError(f"rpc_exhausted:{last}")

tx_obj=rpc("getTransaction",[SIG,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}])
res=tx_obj.get("result")
checks=[]; instruction_data=None; observed_accounts=None; tx_ok=False
if isinstance(res,dict):
    tx_ok=(res.get("slot")==SLOT and (res.get("meta") or {}).get("err") is None)
    msg=((res.get("transaction") or {}).get("message") or {})
    for i,ix in enumerate(msg.get("instructions") or []):
        if [i]==ADDR and ix.get("programId")==SOLEND:
            instruction_data=ix.get("data"); observed_accounts=ix.get("accounts")
    if instruction_data is None:
        for group in (res.get("meta") or {}).get("innerInstructions") or []:
            outer=group.get("index")
            for j,ix in enumerate(group.get("instructions") or []):
                if [outer,j]==ADDR and ix.get("programId")==SOLEND:
                    instruction_data=ix.get("data"); observed_accounts=ix.get("accounts")

dec=b58decode(instruction_data or "") if instruction_data else b""
layout_ok=(len(dec)==9 and dec[:1]==bytes([12]))
liquidity_amount=int.from_bytes(dec[1:9],"little") if layout_ok else None
account_identity_ok=(observed_accounts==ACCOUNTS)
tail_ok=(len(ACCOUNTS)==12 and ACCOUNTS[10]==CLOCK and ACCOUNTS[11]==TOKEN)

acc_obj=rpc("getMultipleAccounts",[ACCOUNTS,{"encoding":"base64","commitment":"finalized"}])
vals=(acc_obj.get("result") or {}).get("value") or []
owners=[]
owner_checks=[]
for i,a in enumerate(ACCOUNTS):
    v=vals[i] if i<len(vals) else None
    owner=v.get("owner") if isinstance(v,dict) else None
    owners.append({"index":i,"account":a,"owner":owner,"exists":v is not None})
    if i in EXPECTED_OWNERS:
        owner_checks.append({"index":i,"expected":EXPECTED_OWNERS[i],"observed":owner,"pass":owner==EXPECTED_OWNERS[i]})

passed=(tx_ok and layout_ok and account_identity_ok and tail_ok and len(owner_checks)==8 and all(x["pass"] for x in owner_checks))
receipt={
 "schema_version":"0.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"SAVE0C_INDEPENDENT_ABI_RECONCILIATION_PASS" if passed else "SAVE0C_INDEPENDENT_ABI_RECONCILIATION_FAIL_CLOSED",
 "signature":SIG,"slot":SLOT,"instruction_address":ADDR,
 "transaction_success_and_slot_pass":tx_ok,
 "instruction_data_length":len(dec),
 "tag_hex":dec[:1].hex() if dec else None,
 "requested_liquidity_amount_u64":liquidity_amount,
 "account_count":len(observed_accounts or []),
 "account_identity_exact_match":account_identity_ok,
 "clock_token_tail_pass":tail_ok,
 "owner_checks":owner_checks,
 "account_owners":owners,
 "authority_basis":{
   "direct_solend_tag_commit":"c93fbc81fcc68610ad64fbce4a170a38335b7d7f",
   "independent_historical_spl_abi_commit":"fd662e5f878d58ad06d3cb6365171ebaec41b39d",
   "note":"SPL ABI semantics accepted only through exact on-chain structural/ownership reconciliation with direct Solend tag authority."
 },
 "semantic_limits":{
   "requested_liquidity_amount_is_not_realized_transfer":True,
   "prices_opened":False,
   "returns_computed":False,
   "pnl_computed":False
 },
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "balances":False,"token_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if not passed: raise SystemExit(2)

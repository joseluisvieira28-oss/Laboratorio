#!/usr/bin/env python3
import base64,json,time,urllib.request,urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
PROGRAM="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
SLOT=177590210
SIG="2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK"
PREFIX="d6a997d5fba756db"
ADDR=[0]
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_RECEIPT_V0.1.json")
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

def b58d(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))
def request(url,body,retries=8):
    data=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json",
        "Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-marginfi-bank-slice/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(30,2**i));continue
            return int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(30,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def account_slice(keys):
    body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
          "params":[keys,{"encoding":"base64","commitment":"finalized","dataSlice":{"offset":8,"length":33}}]}
    st,raw=request(RPC,body)
    if st!=200:raise RuntimeError(f"rpc_http_{st}")
    o=json.loads(raw)
    if o.get("error"):raise RuntimeError(str(o["error"]))
    return o["result"]["value"]

body={
 "type":"solana","fromBlock":SLOT,"toBlock":SLOT,
 "fields":{
   "block":{"number":True,"timestamp":True},
   "transaction":{"transactionIndex":True,"signatures":True,"err":True},
   "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                  "instructionAddress":True,"isCommitted":True,"error":True},
   "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,
                   "preDecimals":True,"postDecimals":True}},
 "instructions":[{"programId":[PROGRAM],"transaction":True,"transactionTokenBalances":True}]
}
st,raw=request(STREAM,body)
if st!=200:raise RuntimeError(f"sqd_http_{st}")
matches=[]
for line in raw.decode("utf-8","replace").splitlines():
    if not line.strip():continue
    b=json.loads(line);tx_by={}
    for pos,tx in enumerate(b.get("transactions") or []):
        tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
    tb_by={}
    for tb in b.get("tokenBalances") or []:
        ti=tb.get("transactionIndex");acct=tb.get("account")
        if ti is None or not acct:continue
        pairs=tb_by.setdefault(ti,{}).setdefault(acct,set())
        if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
            pairs.add((tb["preMint"],int(tb["preDecimals"])))
        if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
            pairs.add((tb["postMint"],int(tb["postDecimals"])))
    for ix in b.get("instructions") or []:
        if ix.get("programId")!=PROGRAM:continue
        tx=tx_by.get(ix.get("transactionIndex"))
        if not isinstance(tx,dict):continue
        sigs=tx.get("signatures") or [];sig=sigs[0] if sigs else None
        if sig!=SIG:continue
        try:dec=b58d(ix.get("data",""))
        except Exception:continue
        if not dec.startswith(bytes.fromhex(PREFIX)):continue
        if ix.get("instructionAddress")!=ADDR:continue
        if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
        accounts=ix.get("accounts") or []
        if len(accounts)<10:continue
        vault=accounts[7];pairs=sorted(tb_by.get(ix.get("transactionIndex"),{}).get(vault,set()))
        matches.append({"accounts":accounts,"vault":vault,
                        "vault_pairs":[{"mint":m,"decimals":d} for m,d in pairs]})
if len(matches)!=1:raise RuntimeError(f"expected_one_reference_match_got_{len(matches)}")
m=matches[0];accounts=m["accounts"]
asset_bank=accounts[1];liab_bank=accounts[2]
vals=account_slice([asset_bank,liab_bank])

results=[]
for role,key,val in [("asset_bank",asset_bank,vals[0] if len(vals)>0 else None),
                     ("liab_bank",liab_bank,vals[1] if len(vals)>1 else None)]:
    rr={"role":role,"bank":key,"pass":False}
    if val is None:
        rr["reason"]="account_missing";results.append(rr);continue
    owner=val.get("owner")
    try:data=base64.b64decode((val.get("data") or [""])[0])
    except Exception:
        rr["reason"]="base64_decode_failed";results.append(rr);continue
    rr["owner"]=owner;rr["slice_length"]=len(data)
    if len(data)!=33:
        rr["reason"]="slice_length_mismatch";results.append(rr);continue
    rr["mint"]=b58e(data[:32]);rr["decimals"]=int(data[32])
    rr["owner_pass"]=(owner==PROGRAM)
    rr["pass"]=rr["owner_pass"] and bool(rr["mint"])
    results.append(rr)

liab=next(x for x in results if x["role"]=="liab_bank")
asset=next(x for x in results if x["role"]=="asset_bank")
vp=m["vault_pairs"]
vault_ok=(len(vp)==1 and vp[0]["mint"]==liab.get("mint") and vp[0]["decimals"]==liab.get("decimals"))
passed=asset["pass"] and liab["pass"] and vault_ok
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_PASS" if passed else "MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_FAIL_CLOSED",
 "reference":{"slot":SLOT,"signature":SIG,"instructionAddress":ADDR,"asset_bank":asset_bank,"liab_bank":liab_bank,
              "bank_liquidity_vault":m["vault"],"vault_token_metadata_pairs":vp},
 "requested_slice":{"offset":8,"length":33,"meaning":"bank_mint_plus_mint_decimals"},
 "bank_results":results,"liability_vault_reconciliation_pass":vault_ok,
 "bank_economic_fields_requested":False,
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"bank_balances":False,"share_values":False,"token_amounts":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if not passed:raise SystemExit(2)

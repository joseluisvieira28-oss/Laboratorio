#!/usr/bin/env python3
import base64,json,urllib.request,time
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
REG=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_2021_PRODUCTION_RESERVE_REGISTRY_V0.1.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE_RESERVE_METADATA_DATASLICE_CALIBRATION_RECEIPT_V0.1.json")
TARGETS=[
 "8PbodeaosQP19SjYFx855UMqWxH2HynZLdBXmsrbac36",
 "BgxfHJDzm44T7XG68MYKx7YisTjZu73tVovyZSjJMpmw",
 "9n2exoMQwMTzfw6NFoFFujxYPndWVLtKREJePssrKb36"
]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58e(b):
    n=int.from_bytes(b,"big")
    s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

def rpc_slice(offset,length,retries=8):
    body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
          "params":[TARGETS,{"encoding":"base64","commitment":"finalized",
                            "dataSlice":{"offset":offset,"length":length}}]}
    raw=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-save-reserve-metadata/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                o=json.loads(r.read())
                if o.get("error"):raise RuntimeError(f"rpc_error:{o['error']}")
                return o["result"]["value"]
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:500]}
            time.sleep(min(30,2**i))
    raise RuntimeError(f"rpc_exhausted:{last}")

registry={x["reserve"]:x for x in json.loads(REG.read_text())["reserves"]}
a=rpc_slice(42,33)
b=rpc_slice(227,32)
results=[];passes=0

for i,address in enumerate(TARGETS):
    exp=registry[address]
    ra=a[i] if i<len(a) else None
    rb=b[i] if i<len(b) else None
    rr={"reserve":address,"pass":False}
    if ra is None or rb is None:
        rr["reason"]="account_missing"
        results.append(rr);continue
    owner_a=ra.get("owner");owner_b=rb.get("owner")
    try:
        da=base64.b64decode((ra.get("data") or [""])[0])
        db=base64.b64decode((rb.get("data") or [""])[0])
    except Exception as e:
        rr["reason"]="base64_decode_failed";results.append(rr);continue
    if len(da)!=33 or len(db)!=32:
        rr["reason"]="slice_length_mismatch";rr["slice_lengths"]=[len(da),len(db)];results.append(rr);continue
    observed={
      "owner":owner_a,
      "liquidity_mint":b58e(da[:32]),
      "liquidity_decimals":int(da[32]),
      "collateral_mint":b58e(db)
    }
    expected={
      "owner":PROGRAM,
      "liquidity_mint":exp["underlying_mint"],
      "liquidity_decimals":int(exp["underlying_decimals"]),
      "collateral_mint":exp["collateral_mint"]
    }
    ok=(owner_a==PROGRAM and owner_b==PROGRAM and observed==expected)
    rr.update({"observed":observed,"expected":expected,"pass":ok})
    if ok:passes+=1
    results.append(rr)

classification="SAVE_RESERVE_METADATA_DATASLICE_3_OF_3_PASS" if passes==3 else "SAVE_RESERVE_METADATA_DATASLICE_CALIBRATION_FAIL_CLOSED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "rpc_authority":RPC,"reference_count":3,"pass_count":passes,"results":results,
 "requested_slices":[{"offset":42,"length":33,"meaning":"liquidity_mint_plus_decimals"},
                     {"offset":227,"length":32,"meaning":"collateral_mint"}],
 "full_reserve_state_requested":False,"economic_amount_fields_decoded":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"full_reserve_state":False,"reserve_available_amount":False,
             "reserve_borrowed_amount":False,"token_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="SAVE_RESERVE_METADATA_DATASLICE_3_OF_3_PASS":raise SystemExit(2)

#!/usr/bin/env python3
import argparse,base64,json,time,urllib.request
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json")
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

def find(root,name):
    hits=sorted(Path(root).rglob(name))
    return json.loads(hits[0].read_text()) if hits else None

def rpc_slice(keys,retries=8):
    body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
          "params":[keys,{"encoding":"base64","commitment":"finalized","dataSlice":{"offset":8,"length":33}}]}
    raw=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json",
      "User-Agent":"crypto-lab-dls-marginfi-bank-completion/0.2"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                o=json.loads(r.read())
                if o.get("error"):raise RuntimeError(str(o["error"]))
                return o["result"]["value"]
        except Exception as e:
            last=str(e)[:300];time.sleep(min(30,2**i))
    raise RuntimeError(f"rpc_exhausted:{last}")

ap=argparse.ArgumentParser()
ap.add_argument("--aggregate",required=True)
ap.add_argument("--calibration",required=True)
args=ap.parse_args()

agg=find(args.aggregate,"MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.1.json")
cal=find(args.calibration,"MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_RECEIPT_V0.1.json")
errors=[];conflicts=[];pending=[]
if not agg:
    errors.append({"reason":"missing_v0_1_registry_receipt"})
elif agg.get("classification")!="MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE":
    errors.append({"reason":"invalid_trigger_classification","classification":agg.get("classification")})
if not cal:
    errors.append({"reason":"missing_dataslice_calibration_receipt"})
elif cal.get("classification")!="MARGINFI_BANK_METADATA_DATASLICE_CALIBRATION_PASS":
    errors.append({"reason":"dataslice_calibration_not_pass","classification":cal.get("classification")})

registry={}
for x in (agg or {}).get("bank_registry") or []:
    b=x.get("bank");mint=x.get("mint");dec=x.get("decimals")
    if b and mint and isinstance(dec,int):registry[b]=(mint,dec)

targets=sorted(set((agg or {}).get("unmapped_asset_banks") or []))
recovered={}
if not errors:
    for i in range(0,len(targets),100):
        chunk=targets[i:i+100]
        vals=rpc_slice(chunk)
        for j,bank in enumerate(chunk):
            val=vals[j] if j<len(vals) else None
            if val is None:
                pending.append({"bank":bank,"reason":"account_missing"});continue
            if val.get("owner")!=PROGRAM:
                conflicts.append({"bank":bank,"reason":"owner_mismatch","owner":val.get("owner")});continue
            try:data=base64.b64decode((val.get("data") or [""])[0])
            except Exception:
                conflicts.append({"bank":bank,"reason":"base64_decode_failed"});continue
            if len(data)!=33:
                conflicts.append({"bank":bank,"reason":"slice_length_mismatch","observed":len(data)});continue
            mint=b58e(data[:32]);dec=int(data[32])
            if not mint:
                conflicts.append({"bank":bank,"reason":"empty_mint"});continue
            recovered[bank]=(mint,dec)

for b,pair in recovered.items():
    if b in registry and registry[b]!=pair:
        conflicts.append({"bank":b,"reason":"registry_pair_conflict",
                          "existing":{"mint":registry[b][0],"decimals":registry[b][1]},
                          "recovered":{"mint":pair[0],"decimals":pair[1]}})
    registry[b]=pair

still=sorted(set(targets)-set(recovered))
if conflicts or errors:
    classification="MARGINFI_BANK_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED"
elif pending or still:
    classification="MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE"
else:
    classification="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS"

receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "trigger_classification":(agg or {}).get("classification"),
 "calibration_classification":(cal or {}).get("classification"),
 "target_unmapped_bank_count":len(targets),"recovered_bank_count":len(recovered),
 "still_unmapped_bank_count":len(still),"still_unmapped_banks":still,
 "pending_account_count":len(pending),"pending_accounts":pending,
 "conflict_count":len(conflicts),"conflicts":conflicts,
 "registry_bank_count":len(registry),
 "bank_registry":[{"bank":b,"mint":p[0],"decimals":p[1]} for b,p in sorted(registry.items())],
 "error_count":len(errors),"errors":errors,
 "bank_economic_fields_requested":False,
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"bank_balances":False,"share_values":False,
             "token_amounts":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="MARGINFI_BANK_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS":raise SystemExit(3)

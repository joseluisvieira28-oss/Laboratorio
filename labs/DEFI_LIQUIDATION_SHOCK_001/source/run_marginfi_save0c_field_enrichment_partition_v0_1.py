#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

CFG={
 "marginfi":{
   "program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
   "prefix":"d6a997d5fba756db",
   "instruction_class":"lending_account_liquidate",
   "lower":"2023-02-07T15:47:04Z","upper":"2025-01-01T00:00:00Z",
   "min_accounts":10,
   "argument_schema":"asset_quantity:u64",
   "roles":{
     "marginfi_group":0,"asset_bank":1,"liab_bank":2,"liquidator_marginfi_account":3,
     "signer":4,"liquidated_marginfi_account":5,"bank_liquidity_vault_authority":6,
     "bank_liquidity_vault":7,"bank_insurance_vault":8,"token_program":9
   }
 },
 "save0c":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix":"0c",
   "instruction_class":"LiquidateObligation",
   "lower":"2021-12-08T00:00:00Z","upper":"2025-01-01T00:00:00Z",
   "min_accounts":12,
   "exact_accounts":12,
   "argument_schema":"liquidity_amount:u64 little-endian",
   "roles":{
     "source_liquidity_token_account":0,"destination_collateral_token_account":1,
     "repay_reserve":2,"repay_reserve_liquidity_supply":3,"withdraw_reserve":4,
     "withdraw_reserve_collateral_supply":5,"obligation":6,"lending_market":7,
     "derived_lending_market_authority":8,"user_transfer_authority":9,
     "clock_sysvar":10,"token_program":11
   }
 }
}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def iso_dt(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm_ts(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)):
        return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def canonical_key(protocol,cls,sig,addr): return (protocol,cls,sig,addr_key(addr))
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-field-enrichment/0.1"}
    if data is not None: headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as r:
                return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":raw[:300].decode("utf-8","replace")}
                time.sleep(min(60,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    unix=int(iso_dt(s).timestamp())
    st,h,raw=req(f"{TSROOT}/{unix}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}")
    obj=json.loads(raw)
    if isinstance(obj,int): return obj
    if isinstance(obj,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(obj.get(k),int): return obj[k]
    raise RuntimeError("timestamp_resolver_schema")

def load_baseline(root,protocol,cls,start,end):
    lo=iso_dt(start); hi=iso_dt(end)
    keys={}; source_files=[]; anomalies=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:
            with p.open("r",encoding="utf-8") as fh: obj=json.load(fh)
        except Exception:
            continue
        rows=obj.get("rows")
        if not isinstance(rows,list): continue
        source_files.append(str(p))
        for r in rows:
            if r.get("protocol")!=protocol: continue
            if r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": continue
            try: t=iso_dt(r.get("timestamp"))
            except Exception:
                anomalies.append({"reason":"baseline_bad_timestamp","file":str(p),"signature":r.get("signature")}); continue
            if not (lo<=t<hi): continue
            sig=r.get("signature"); addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anomalies.append({"reason":"baseline_bad_identity","file":str(p),"signature":sig}); continue
            k=canonical_key(protocol,cls,sig,addr)
            if k in keys and keys[k]!=r:
                anomalies.append({"reason":"baseline_duplicate_conflict","signature":sig,"instructionAddress":addr})
            keys[k]=r
    return keys,source_files,anomalies

def enrich(protocol,start,end):
    c=CFG[protocol]; lo=iso_dt(start); hi=iso_dt(end)
    from_slot=ts_slot(start); to_slot=ts_slot(end)+16; current=from_slot
    lo_ts=int(lo.timestamp()); hi_ts=int(hi.timestamp())
    rows=[]; termination=[]; requests=0
    while current<=to_slot:
        body={
          "type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}
          },
          "instructions":[{"programId":[c["program"]],"transaction":True}]
        }
        st,h,raw=req(STREAM,body); requests+=1
        if st==204:
            termination.append({"http_status":204,"from_slot":current,"reason":"NO_CONTENT_DOCUMENTED_STREAM_TERMINATION"}); break
        if st!=200: raise RuntimeError(f"stream_http_{st}")
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines:
            termination.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION"}); break
        batch=[json.loads(x) for x in lines]; last=None
        for b in batch:
            hdr=b.get("header") or {}; slot=hdr.get("number"); ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            if ts is None: continue
            try: bt=int(iso_dt(ts).timestamp())
            except Exception: continue
            if not (lo_ts<=bt<hi_ts): continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=c["program"]: continue
                try: dec=b58decode(ix.get("data",""))
                except Exception: continue
                pref=bytes.fromhex(c["prefix"])
                if not dec.startswith(pref): continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict): continue
                sigs=tx.get("signatures") or []; sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                if not sig: continue
                terr=tx.get("err"); committed=ix.get("isCommitted"); ierr=ix.get("error")
                if not (terr is None and committed is True and ierr is None): continue
                addr=ix.get("instructionAddress"); accounts=ix.get("accounts") or []; data=ix.get("data") or ""
                semantic={name:(accounts[idx] if idx<len(accounts) else None) for name,idx in c["roles"].items()}
                rows.append({
                  "protocol":protocol,"instruction_class":c["instruction_class"],"signature":sig,
                  "slot":slot,"timestamp":ts,"transactionIndex":ti,"instructionAddress":addr,
                  "programId":c["program"],"decoded_prefix_hex":dec[:len(pref)].hex(),
                  "instruction_data_base58":data,"instruction_data_byte_length":len(dec),
                  "accounts":accounts,"account_count":len(accounts),"semantic_accounts":semantic,
                  "argument_schema":c["argument_schema"],
                  "argument_numeric_value_emitted":False,
                  "field_status":{
                    "identity":"FIELD_PRESENT_DIRECT",
                    "instruction_data":"FIELD_PRESENT_DIRECT",
                    "semantic_accounts":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY",
                    "argument_schema":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY"
                  }
                })
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1
    return rows,requests,termination

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=sorted(CFG),required=True)
ap.add_argument("--start",required=True); ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True); ap.add_argument("--out",required=True); ap.add_argument("--partition-id",required=True)
args=ap.parse_args()

c=CFG[args.protocol]
start=max(iso_dt(args.start),iso_dt(c["lower"])).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(c["upper"])).isoformat().replace("+00:00","Z")
if iso_dt(start)>=iso_dt(end): raise SystemExit("empty_effective_range")

baseline,source_files,baseline_anom=load_baseline(args.baseline,args.protocol,c["instruction_class"],start,end)
enriched,requests,termination=enrich(args.protocol,start,end)

enriched_map={}; duplicate_keys=[]; semantic_conflicts=[]
for r in enriched:
    k=canonical_key(args.protocol,c["instruction_class"],r.get("signature"),r.get("instructionAddress"))
    if k in enriched_map:
        duplicate_keys.append({"signature":r.get("signature"),"instructionAddress":r.get("instructionAddress")})
    enriched_map[k]=r
    n=r["account_count"]
    if n<c["min_accounts"] or ("exact_accounts" in c and n!=c["exact_accounts"]):
        semantic_conflicts.append({"signature":r["signature"],"instructionAddress":r["instructionAddress"],
                                   "reason":"account_count_mismatch","observed":n})
    if any(v is None for v in r["semantic_accounts"].values()):
        semantic_conflicts.append({"signature":r["signature"],"instructionAddress":r["instructionAddress"],
                                   "reason":"required_semantic_account_missing"})

missing=sorted(set(baseline)-set(enriched_map))
extra=sorted(set(enriched_map)-set(baseline))
passed=(not baseline_anom and not duplicate_keys and not semantic_conflicts and not missing and not extra)

receipt={
  "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "protocol":args.protocol,"instruction_class":c["instruction_class"],"partition_id":args.partition_id,
  "effective_start":start,"effective_end":end,
  "classification":"FIELD_ENRICHMENT_PARTITION_PASS" if passed else "FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED",
  "baseline_source_files":source_files,
  "baseline_success_count":len(baseline),"enriched_success_count":len(enriched_map),
  "missing_count":len(missing),"extra_count":len(extra),"duplicate_count":len(duplicate_keys),
  "semantic_conflict_count":len(semantic_conflicts),"baseline_anomaly_count":len(baseline_anom),
  "nonempty_accounts_count":sum(1 for r in enriched_map.values() if r.get("account_count",0)>0),
  "full_instruction_data_count":sum(1 for r in enriched_map.values() if r.get("instruction_data_byte_length",0)>0),
  "request_count":requests,"termination_evidence":termination,
  "missing_keys":[list(x) for x in missing[:100]],"extra_keys":[list(x) for x in extra[:100]],
  "duplicate_keys":duplicate_keys[:100],"semantic_conflicts":semantic_conflicts[:100],
  "enriched_rows":sorted(enriched_map.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],addr_key(r["instructionAddress"]))),
  "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
              "economic_outcomes":False,"token_balances":False,"token_amounts":False,"token_decimals":False,
              "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
              "exchange_mutation":False,"paid_source":False,"account_creation":False,
              "post_outcome_tuning":False,"merge_main":False}
}
p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["protocol","effective_start","effective_end","classification",
 "baseline_success_count","enriched_success_count","missing_count","extra_count","duplicate_count",
 "semantic_conflict_count","baseline_anomaly_count"]},indent=2))
if not passed: raise SystemExit(2)

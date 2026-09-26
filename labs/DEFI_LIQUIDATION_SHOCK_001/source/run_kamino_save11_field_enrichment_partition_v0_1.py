#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

CFG={
 "kamino":{
   "program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
   "prefix":"b1479abce2854a37",
   "instruction_class":"liquidate_obligation_and_redeem_reserve_collateral",
   "lower":"2023-11-17T14:48:24Z","upper":"2025-01-01T00:00:00Z",
   "exact_accounts":16,"exact_data_bytes":32,
   "argument_schema":["liquidity_amount:u64","min_acceptable_received_collateral_amount:u64","max_allowed_ltv_override_percent:u64"],
   "roles":{
     "liquidator":0,"obligation":1,"lending_market":2,"lending_market_authority":3,
     "repay_reserve":4,"repay_reserve_liquidity_supply":5,"withdraw_reserve":6,
     "withdraw_reserve_collateral_mint":7,"withdraw_reserve_collateral_supply":8,
     "withdraw_reserve_liquidity_supply":9,"withdraw_reserve_liquidity_fee_receiver":10,
     "user_source_liquidity":11,"user_destination_collateral":12,"user_destination_liquidity":13,
     "token_program":14,"instruction_sysvar_account":15
   }
 },
 "save11":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix":"11",
   "instruction_class":"LiquidateObligationAndRedeemReserveCollateral",
   "lower":"2024-07-19T19:30:52Z","upper":"2025-01-01T00:00:00Z",
   "exact_accounts":15,"exact_data_bytes":9,
   "argument_schema":["liquidityAmount:u64"],
   "roles":{
     "source_liquidity":0,"destination_collateral":1,"destination_reward_liquidity":2,
     "repay_reserve":3,"repay_reserve_liquidity_supply":4,"withdraw_reserve":5,
     "withdraw_reserve_collateral_mint":6,"withdraw_reserve_collateral_supply":7,
     "withdraw_reserve_liquidity_supply":8,"withdraw_reserve_fee_receiver":9,
     "obligation":10,"lending_market":11,"lending_market_authority":12,
     "transfer_authority":13,"token_program":14
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
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def canonical_key(protocol,cls,sig,addr): return (protocol,cls,sig,addr_key(addr))
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-field-enrichment-k-s11/0.1"}
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
                last={"http":e.code}; time.sleep(min(60,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}; time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def ts_slot(s):
    unix=int(iso_dt(s).timestamp()); st,h,raw=req(f"{TSROOT}/{unix}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}")
    obj=json.loads(raw)
    if isinstance(obj,int): return obj
    if isinstance(obj,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(obj.get(k),int): return obj[k]
    raise RuntimeError("timestamp_resolver_schema")

def load_baseline(root,protocol,cls,start,end):
    lo=iso_dt(start); hi=iso_dt(end); keys={}; files=[]; anomalies=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:
            with p.open("r",encoding="utf-8") as fh: obj=json.load(fh)
        except Exception: continue
        rows=obj.get("rows")
        if not isinstance(rows,list): continue
        files.append(str(p))
        for r in rows:
            if r.get("protocol")!=protocol: continue
            if r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": continue
            try:t=iso_dt(r.get("timestamp"))
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
    return keys,files,anomalies

def enrich(protocol,start,end):
    c=CFG[protocol]; lo=iso_dt(start); hi=iso_dt(end)
    from_slot=ts_slot(start); to_slot=ts_slot(end)+16; current=from_slot
    lo_ts=int(lo.timestamp()); hi_ts=int(hi.timestamp())
    rows=[]; terms=[]; reqs=0
    while current<=to_slot:
        body={"type":"solana","fromBlock":current,"toBlock":to_slot,
              "fields":{"block":{"number":True,"timestamp":True},
                        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                        "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                       "instructionAddress":True,"isCommitted":True,"error":True}},
              "instructions":[{"programId":[c["program"]],"transaction":True}]}
        st,h,raw=req(STREAM,body); reqs+=1
        if st==204:
            terms.append({"http_status":204,"from_slot":current,"reason":"NO_CONTENT_DOCUMENTED_STREAM_TERMINATION"}); break
        if st!=200: raise RuntimeError(f"stream_http_{st}")
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines:
            terms.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION"}); break
        batch=[json.loads(x) for x in lines]; last=None
        for b in batch:
            hdr=b.get("header") or {}; slot=hdr.get("number"); ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            if ts is None: continue
            try:bt=int(iso_dt(ts).timestamp())
            except Exception:continue
            if not (lo_ts<=bt<hi_ts): continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=c["program"]: continue
                try:dec=b58decode(ix.get("data",""))
                except Exception:continue
                pref=bytes.fromhex(c["prefix"])
                if not dec.startswith(pref): continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict): continue
                sigs=tx.get("signatures") or []; sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                if not sig: continue
                if not (tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None): continue
                addr=ix.get("instructionAddress"); accounts=ix.get("accounts") or []; data=ix.get("data") or ""
                semantic={name:(accounts[idx] if idx<len(accounts) else None) for name,idx in c["roles"].items()}
                rows.append({
                  "protocol":protocol,"instruction_class":c["instruction_class"],"signature":sig,
                  "slot":slot,"timestamp":ts,"transactionIndex":ti,"instructionAddress":addr,
                  "programId":c["program"],"decoded_prefix_hex":dec[:len(pref)].hex(),
                  "instruction_data_base58":data,"instruction_data_byte_length":len(dec),
                  "accounts":accounts,"account_count":len(accounts),"semantic_accounts":semantic,
                  "argument_schema":c["argument_schema"],"argument_numeric_value_emitted":False,
                  "field_status":{"identity":"FIELD_PRESENT_DIRECT","instruction_data":"FIELD_PRESENT_DIRECT",
                                  "semantic_accounts":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY",
                                  "argument_schema":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY"}
                })
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1
    return rows,reqs,terms

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=sorted(CFG),required=True)
ap.add_argument("--start",required=True); ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True); ap.add_argument("--out",required=True); ap.add_argument("--partition-id",required=True)
args=ap.parse_args()

c=CFG[args.protocol]
start=max(iso_dt(args.start),iso_dt(c["lower"])).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(c["upper"])).isoformat().replace("+00:00","Z")
baseline,files,banom=load_baseline(args.baseline,args.protocol,c["instruction_class"],start,end)
enriched,reqs,terms=enrich(args.protocol,start,end)

emap={}; duplicates=[]; conflicts=[]
for r in enriched:
    k=canonical_key(args.protocol,c["instruction_class"],r.get("signature"),r.get("instructionAddress"))
    if k in emap: duplicates.append({"signature":r.get("signature"),"instructionAddress":r.get("instructionAddress")})
    emap[k]=r
    if r["account_count"]!=c["exact_accounts"]:
        conflicts.append({"signature":r["signature"],"reason":"account_count_mismatch","observed":r["account_count"],"expected":c["exact_accounts"]})
    if r["instruction_data_byte_length"]!=c["exact_data_bytes"]:
        conflicts.append({"signature":r["signature"],"reason":"instruction_data_length_mismatch","observed":r["instruction_data_byte_length"],"expected":c["exact_data_bytes"]})
    if any(v is None for v in r["semantic_accounts"].values()):
        conflicts.append({"signature":r["signature"],"reason":"required_semantic_account_missing"})

missing=sorted(set(baseline)-set(emap)); extra=sorted(set(emap)-set(baseline))
passed=not banom and not duplicates and not conflicts and not missing and not extra

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":args.protocol,
 "instruction_class":c["instruction_class"],"partition_id":args.partition_id,"effective_start":start,"effective_end":end,
 "classification":"FIELD_ENRICHMENT_PARTITION_PASS" if passed else "FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED",
 "baseline_source_files":files,"baseline_success_count":len(baseline),"enriched_success_count":len(emap),
 "missing_count":len(missing),"extra_count":len(extra),"duplicate_count":len(duplicates),
 "semantic_conflict_count":len(conflicts),"baseline_anomaly_count":len(banom),
 "nonempty_accounts_count":sum(1 for r in emap.values() if r["account_count"]>0),
 "full_instruction_data_count":sum(1 for r in emap.values() if r["instruction_data_byte_length"]>0),
 "exact_abi_shape_count":sum(1 for r in emap.values() if r["account_count"]==c["exact_accounts"] and r["instruction_data_byte_length"]==c["exact_data_bytes"]),
 "request_count":reqs,"termination_evidence":terms,
 "missing_keys":[list(x) for x in missing[:100]],"extra_keys":[list(x) for x in extra[:100]],
 "duplicate_keys":duplicates[:100],"semantic_conflicts":conflicts[:100],
 "enriched_rows":sorted(emap.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],addr_key(r["instructionAddress"]))),
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_balances":False,"token_amounts":False,"token_decimals":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["protocol","partition_id","classification","baseline_success_count","enriched_success_count","missing_count","extra_count","semantic_conflict_count"]},indent=2))
if not passed: raise SystemExit(2)

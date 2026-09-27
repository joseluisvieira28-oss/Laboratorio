#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from collections import Counter
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
CLS="LiquidateObligationAndRedeemReserveCollateral"
LOWER="2024-07-19T19:30:52Z"
UPPER="2025-01-01T00:00:00Z"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}
ROLES={
 "source_liquidity":0,"destination_collateral":1,"destination_reward_liquidity":2,
 "repay_reserve":3,"repay_reserve_liquidity_supply":4,"withdraw_reserve":5,
 "withdraw_reserve_collateral_mint":6,"withdraw_reserve_collateral_supply":7,
 "withdraw_reserve_liquidity_supply":8,"withdraw_reserve_fee_receiver":9,
 "obligation":10,"lending_market":11,"lending_market_authority":12,
 "transfer_authority":13,"token_program":14
}
UNIT_ROLES={
 "debt_underlying":(4,0),
 "collateral_token":(7,1),
 "collateral_underlying":(8,2)
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
def key(sig,addr): return ("save11",CLS,sig,addr_key(addr))

def req(url,body=None,retries=12):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-save11-authority/0.4"}
    if data is not None: headers["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:
                return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":raw.decode("utf-8","replace")[:300]}
                time.sleep(min(90,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(90,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    st,h,raw=req(f"{TSROOT}/{int(iso_dt(s).timestamp())}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int): return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int): return o[k]
    raise RuntimeError("timestamp_resolver_schema")

def load_baseline(root,start,end):
    lo=iso_dt(start);hi=iso_dt(end);out={};anom=[];files=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:o=json.loads(p.read_text())
        except Exception:continue
        rows=o.get("rows")
        if not isinstance(rows,list):continue
        files.append(str(p))
        for r in rows:
            if r.get("protocol")!="save11" or r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":continue
            try:t=iso_dt(r.get("timestamp"))
            except Exception:
                anom.append({"reason":"bad_timestamp","signature":r.get("signature")});continue
            if not (lo<=t<hi):continue
            sig=r.get("signature");addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anom.append({"reason":"bad_identity","signature":sig});continue
            k=key(sig,addr)
            if k in out and out[k]!=r:
                anom.append({"reason":"duplicate_baseline_conflict","signature":sig,"instructionAddress":addr})
            out[k]=r
    return out,files,anom

def pairs_for(tb):
    s=set()
    if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
        s.add((tb["preMint"],int(tb["preDecimals"])))
    if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
        s.add((tb["postMint"],int(tb["postDecimals"])))
    return s

def primary_optional(accounts,tbmap,primary_pos,optional_pos):
    if primary_pos>=len(accounts) or optional_pos>=len(accounts):
        return None,{"reason":"account_position_missing","primary_pos":primary_pos,"optional_pos":optional_pos}
    primary_account=accounts[primary_pos]; optional_account=accounts[optional_pos]
    pp=sorted(tbmap.get(primary_account,set()))
    op=sorted(tbmap.get(optional_account,set()))
    observed={
      "primary":{"position":primary_pos,"account":primary_account,
                 "pairs":[{"mint":m,"decimals":d} for m,d in pp]},
      "optional":{"position":optional_pos,"account":optional_account,
                  "pairs":[{"mint":m,"decimals":d} for m,d in op]}
    }
    if len(pp)!=1:
        return None,{"reason":"primary_reserve_vault_unit_not_exactly_one_pair","observed":observed}
    if len(op)>1:
        return None,{"reason":"optional_user_unit_multiple_pairs","observed":observed}
    if len(op)==1 and op[0]!=pp[0]:
        return None,{"reason":"optional_user_unit_mismatch","observed":observed}
    mint,dec=pp[0]
    return {
      "mint":mint,"decimals":dec,
      "primary_source_account":primary_account,
      "optional_crosscheck_account":optional_account,
      "resolution":"PRIMARY_RESERVE_VAULT_PLUS_USER_CROSSCHECK" if len(op)==1 else "PRIMARY_RESERVE_VAULT_DIRECT_OPTIONAL_USER_MISSING"
    },None

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True)
ap.add_argument("--field-out",required=True);ap.add_argument("--unit-out",required=True)
args=ap.parse_args()

start=max(iso_dt(args.start),iso_dt(LOWER)).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(UPPER)).isoformat().replace("+00:00","Z")
baseline,baseline_files,banom=load_baseline(args.baseline,start,end)
lo=iso_dt(start);hi=iso_dt(end);lo_ts=int(lo.timestamp());hi_ts=int(hi.timestamp())
current=ts_slot(start);to_slot=ts_slot(end)+16

seen={};field_rows={};unit_rows=[];field_conflicts=[];unit_conflicts=[];query_anom=[];duplicates=[]
reqs=0;terms=[];length_counts=Counter();unit_resolution_counts=Counter()

while current<=to_slot:
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True},
                    "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,
                                    "preDecimals":True,"postDecimals":True}},
          "instructions":[{"programId":[PROGRAM],"d1":["0x11"],"isCommitted":True,
                           "transaction":True,"transactionTokenBalances":True}]}
    st,h,raw=req(STREAM,body);reqs+=1
    if st==204:
        terms.append({"http_status":204,"from_slot":current,"reason":"NO_CONTENT"});break
    if st!=200: raise RuntimeError(f"stream_http_{st}")
    lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    if not lines:
        terms.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON"});break
    batch=[json.loads(x) for x in lines];last=None
    for b in batch:
        hdr=b.get("header") or {};slot=hdr.get("number");ts=norm_ts(hdr.get("timestamp"))
        if isinstance(slot,int):last=slot if last is None else max(last,slot)
        if ts is None:continue
        try:bt=int(iso_dt(ts).timestamp())
        except Exception:continue
        if not (lo_ts<=bt<hi_ts):continue

        tb_by_tx={}
        for tb in b.get("tokenBalances") or []:
            ti=tb.get("transactionIndex");acct=tb.get("account")
            if ti is None or not acct:continue
            tb_by_tx.setdefault(ti,{}).setdefault(acct,set()).update(pairs_for(tb))
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx

        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(b"\x11"):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict):
                query_anom.append({"reason":"missing_parent_transaction","slot":slot});continue
            if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list):
                query_anom.append({"reason":"bad_identity","signature":sig});continue

            k=key(sig,addr)
            if k in seen:
                duplicates.append({"signature":sig,"instructionAddress":addr});continue
            seen[k]=True
            length_counts[len(dec)]+=1

            ferr=[]
            if len(accounts)!=15:
                ferr.append({"reason":"save11_account_count_mismatch","observed":len(accounts),"expected":15})
            if len(dec) not in (9,10):
                ferr.append({"reason":"save11_data_length_not_frozen_allowed","observed":len(dec),"allowed":[9,10]})
            if ferr:
                field_conflicts.append({"signature":sig,"instructionAddress":addr,"errors":ferr})
                continue

            sem={name:accounts[pos] for name,pos in ROLES.items()}
            field_rows[k]={
              "protocol":"save11","instruction_class":CLS,"signature":sig,"slot":slot,"timestamp":ts,
              "transactionIndex":ti,"instructionAddress":addr,"programId":PROGRAM,
              "decoded_prefix_hex":"11","instruction_data_base58":ix.get("data") or "",
              "instruction_data_byte_length":len(dec),"account_count":15,"accounts":accounts,
              "historical_account_layout":"SAVE11_15_TRAILING_TOLERANT",
              "semantic_accounts":sem,"dynamic_remaining_accounts":[],
              "argument_schema":["liquidityAmount:u64"],
              "decoder_ignored_trailing_byte_count":len(dec)-9,
              "argument_numeric_value_emitted":False,"trailing_byte_value_emitted":False,
              "field_status":{"identity":"FIELD_PRESENT_DIRECT","instruction_data":"FIELD_PRESENT_DIRECT",
                              "semantic_accounts":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY",
                              "argument_schema":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY"}
            }

            units={};errs=[];tbmap=tb_by_tx.get(ti,{})
            for role,(primary_pos,optional_pos) in UNIT_ROLES.items():
                pair,err=primary_optional(accounts,tbmap,primary_pos,optional_pos)
                if err:errs.append({"role":role,**err})
                else:
                    units[role]=pair
                    unit_resolution_counts[pair["resolution"]]+=1
            if errs:
                unit_conflicts.append({"signature":sig,"instructionAddress":addr,"unit_errors":errs})
            else:
                unit_rows.append({"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,
                                  "historical_account_layout":"SAVE11_15_TRAILING_TOLERANT",**units})

    if last is None: raise RuntimeError("no_block_number")
    if last<current: raise RuntimeError("non_advancing_stream")
    current=last+1

missing=sorted(set(baseline)-set(seen));extra=sorted(set(seen)-set(baseline))
field_pass=not banom and not query_anom and not duplicates and not field_conflicts and not missing and not extra and len(field_rows)==len(baseline)
unit_pass=field_pass and not unit_conflicts and len(unit_rows)==len(baseline)

field_receipt={
 "schema_version":"0.4","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"save11",
 "instruction_class":CLS,"partition_id":args.partition_id,"effective_start":start,"effective_end":end,
 "classification":"FIELD_ENRICHMENT_PARTITION_PASS" if field_pass else "FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED",
 "authority_addendum":"SAVE11_TRAILING_DATA_AND_UNIT_AUTHORITY_ADDENDUM_V0.4.md",
 "baseline_source_files":baseline_files,"baseline_success_count":len(baseline),"enriched_success_count":len(seen),
 "missing_count":len(missing),"extra_count":len(extra),"duplicate_count":len(duplicates),
 "semantic_conflict_count":len(field_conflicts),"baseline_anomaly_count":len(banom),
 "nonempty_accounts_count":sum(1 for r in field_rows.values() if r["account_count"]>0),
 "full_instruction_data_count":len(field_rows),"exact_abi_shape_count":len(field_rows),
 "instruction_data_length_counts":{str(k):v for k,v in sorted(length_counts.items())},
 "ignored_trailing_byte_event_count":sum(v for k,v in length_counts.items() if k==10),
 "trailing_byte_value_emitted":False,"request_count":reqs,"termination_evidence":terms,
 "missing_keys":[list(x) for x in missing[:100]],"extra_keys":[list(x) for x in extra[:100]],
 "duplicate_keys":duplicates[:100],"semantic_conflicts":field_conflicts[:100],
 "enriched_rows":sorted(field_rows.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],addr_key(r["instructionAddress"]))),
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"token_amounts":False,"requested_amount_values":False,
             "trailing_byte_value_emitted":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}

unit_receipt={
 "schema_version":"0.4","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"save11",
 "partition_id":args.partition_id,"effective_start":start,"effective_end":end,
 "classification":"KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS" if unit_pass else "KAMINO_SAVE11_UNIT_METADATA_PARTITION_FAIL_CLOSED",
 "authority_addendum":"SAVE11_TRAILING_DATA_AND_UNIT_AUTHORITY_ADDENDUM_V0.4.md",
 "baseline_success_count":len(baseline),"enriched_success_count":len(seen),
 "unit_complete_event_count":len(unit_rows),"missing_count":len(missing),"extra_count":len(extra),
 "baseline_anomaly_count":len(banom),"query_anomaly_count":len(query_anom),
 "unit_conflict_count":len(unit_conflicts),
 "primary_plus_crosscheck_role_count":unit_resolution_counts["PRIMARY_RESERVE_VAULT_PLUS_USER_CROSSCHECK"],
 "primary_optional_missing_role_count":unit_resolution_counts["PRIMARY_RESERVE_VAULT_DIRECT_OPTIONAL_USER_MISSING"],
 "event_units":unit_rows,"conflict_examples":unit_conflicts[:100],"query_anomaly_examples":query_anom[:100],
 "request_count":reqs,"termination_evidence":terms,"amount_fields_requested":False,
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
             "requested_amount_values":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}

for out,obj in [(args.field_out,field_receipt),(args.unit_out,unit_receipt)]:
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

print(json.dumps({
 "partition_id":args.partition_id,
 "field_classification":field_receipt["classification"],
 "unit_classification":unit_receipt["classification"],
 "baseline_success_count":len(baseline),"enriched_success_count":len(seen),
 "instruction_data_length_counts":field_receipt["instruction_data_length_counts"],
 "field_conflict_count":len(field_conflicts),"unit_conflict_count":len(unit_conflicts),
 "unit_complete_event_count":len(unit_rows),"missing_count":len(missing),"extra_count":len(extra)
},indent=2,sort_keys=True))

if not field_pass or not unit_pass: raise SystemExit(2)

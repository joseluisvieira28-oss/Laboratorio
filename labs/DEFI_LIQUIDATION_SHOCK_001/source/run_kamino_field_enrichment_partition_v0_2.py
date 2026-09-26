#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
PREFIX="b1479abce2854a37"
CLS="liquidate_obligation_and_redeem_reserve_collateral"
LOWER="2023-11-17T14:48:24Z"; UPPER="2025-01-01T00:00:00Z"
V2_BOUNDARY="2024-06-19T19:15:17Z"
V2_SOURCE_COMMIT_TIME="2024-06-19T15:31:40Z"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}

LEGACY_ROLES={
 "liquidator":0,"obligation":1,"lending_market":2,"lending_market_authority":3,
 "repay_reserve":4,"repay_reserve_liquidity_supply":5,"withdraw_reserve":6,
 "withdraw_reserve_collateral_mint":7,"withdraw_reserve_collateral_supply":8,
 "withdraw_reserve_liquidity_supply":9,"withdraw_reserve_liquidity_fee_receiver":10,
 "user_source_liquidity":11,"user_destination_collateral":12,"user_destination_liquidity":13,
 "token_program":14,"instruction_sysvar_account":15
}
V2_ROLES={
 "liquidator":0,"obligation":1,"lending_market":2,"lending_market_authority":3,
 "repay_reserve":4,"repay_reserve_liquidity_mint":5,"repay_reserve_liquidity_supply":6,
 "withdraw_reserve":7,"withdraw_reserve_liquidity_mint":8,"withdraw_reserve_collateral_mint":9,
 "withdraw_reserve_collateral_supply":10,"withdraw_reserve_liquidity_supply":11,
 "withdraw_reserve_liquidity_fee_receiver":12,"user_source_liquidity":13,
 "user_destination_collateral":14,"user_destination_liquidity":15,"collateral_token_program":16,
 "repay_liquidity_token_program":17,"withdraw_liquidity_token_program":18,"instruction_sysvar_account":19
}
ARG_SCHEMA=["liquidity_amount:u64","min_acceptable_received_liquidity_or_collateral_amount:u64","max_allowed_ltv_override_percent:u64"]

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw
def iso(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
def ak(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def key(sig,addr): return ("kamino",CLS,sig,ak(addr))
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-kamino-temporal-field/0.2"}
    if data is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:last=e.code;time.sleep(min(60,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:last=str(e)[:300];time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def ts_slot(s):
    st,h,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    for k in ("block","block_number","number","slot"):
        if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")
def load_baseline(root,start,end):
    lo,hi=iso(start),iso(end);out={};anom=[];files=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:o=json.loads(p.read_text())
        except Exception:continue
        rows=o.get("rows")
        if not isinstance(rows,list):continue
        files.append(str(p))
        for r in rows:
            if r.get("protocol")!="kamino" or r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":continue
            try:t=iso(r.get("timestamp"))
            except Exception:anom.append({"reason":"bad_timestamp","signature":r.get("signature")});continue
            if not(lo<=t<hi):continue
            sig=r.get("signature");addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anom.append({"reason":"bad_identity","signature":sig});continue
            k=key(sig,addr)
            if k in out and out[k]!=r:anom.append({"reason":"duplicate_conflict","signature":sig,"instructionAddress":addr})
            out[k]=r
    return out,files,anom
def layout(ts,accounts):
    when=iso(ts); boundary=iso(V2_BOUNDARY); source=iso(V2_SOURCE_COMMIT_TIME); n=len(accounts)
    if when<boundary:
        if n!=16:return None,{"reason":"legacy_shape_mismatch","timestamp":ts,"observed":n,"expected":16}
        return ("kamino_v1_legacy",LEGACY_ROLES,[]),None
    if when<source:
        return None,{"reason":"v2_before_source_support","timestamp":ts,"observed":n}
    if n<20:return None,{"reason":"v2_fixed_prefix_missing","timestamp":ts,"observed":n,"minimum":20}
    return ("kamino_v1_6_plus",V2_ROLES,accounts[20:]),None

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args()
start=max(iso(args.start),iso(LOWER)).isoformat().replace("+00:00","Z"); end=min(iso(args.end),iso(UPPER)).isoformat().replace("+00:00","Z")
baseline,files,banom=load_baseline(args.baseline,start,end)
lo,hi=iso(start),iso(end);current=ts_slot(start);to_slot=ts_slot(end)+16
emap={};conf=[];dup=[];terms=[];reqs=0
while current<=to_slot:
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
      "fields":{"block":{"number":True,"timestamp":True},"transaction":{"transactionIndex":True,"signatures":True,"err":True},
      "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True}},
      "instructions":[{"programId":[PROGRAM],"transaction":True}]}
    st,h,raw=req(STREAM,body);reqs+=1
    if st==204:terms.append({"http_status":204,"from_slot":current});break
    if st!=200:raise RuntimeError(f"stream_http_{st}")
    lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    if not lines:terms.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON"});break
    batch=[json.loads(x) for x in lines];last=None
    for b in batch:
        hdr=b.get("header") or {};slot=hdr.get("number");ts=norm(hdr.get("timestamp"))
        if isinstance(slot,int):last=slot if last is None else max(last,slot)
        if not ts:continue
        try:t=iso(ts)
        except Exception:continue
        if not(lo<=t<hi):continue
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(bytes.fromhex(PREFIX)):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict) or tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list):continue
            k=key(sig,addr)
            if k in emap:dup.append({"signature":sig,"instructionAddress":addr});continue
            lay,err=layout(ts,accounts)
            semantic={};remaining=[]
            if err:conf.append({"signature":sig,"instructionAddress":addr,**err})
            else:
                ver,roles,remaining=lay
                semantic={name:accounts[idx] for name,idx in roles.items()}
                if len(dec)!=32:conf.append({"signature":sig,"reason":"instruction_data_length_mismatch","observed":len(dec),"expected":32})
                if any(v is None for v in semantic.values()):conf.append({"signature":sig,"reason":"required_semantic_account_missing"})
            emap[k]={"protocol":"kamino","instruction_class":CLS,"signature":sig,"slot":slot,"timestamp":ts,
              "transactionIndex":ti,"instructionAddress":addr,"programId":PROGRAM,"decoded_prefix_hex":PREFIX,
              "instruction_data_base58":ix.get("data") or "","instruction_data_byte_length":len(dec),
              "accounts":accounts,"account_count":len(accounts),"decoder_version":(lay[0] if lay else None),
              "semantic_accounts":semantic,"remaining_accounts":remaining,"argument_schema":ARG_SCHEMA,
              "argument_numeric_value_emitted":False}
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1
missing=sorted(set(baseline)-set(emap));extra=sorted(set(emap)-set(baseline))
passed=not banom and not dup and not conf and not missing and not extra
receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"kamino","partition_id":args.partition_id,
 "classification":"FIELD_ENRICHMENT_PARTITION_PASS" if passed else "FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED",
 "effective_start":start,"effective_end":end,"baseline_source_files":files,
 "baseline_success_count":len(baseline),"enriched_success_count":len(emap),"missing_count":len(missing),"extra_count":len(extra),
 "duplicate_count":len(dup),"semantic_conflict_count":len(conf),"baseline_anomaly_count":len(banom),
 "nonempty_accounts_count":sum(1 for r in emap.values() if r["account_count"]>0),
 "full_instruction_data_count":sum(1 for r in emap.values() if r["instruction_data_byte_length"]>0),
 "temporal_abi_shape_valid_count":sum(1 for r in emap.values() if (r["decoder_version"]=="kamino_v1_legacy" and r["account_count"]==16) or (r["decoder_version"]=="kamino_v1_6_plus" and r["account_count"]>=20)),
 "decoder_version_counts":{v:sum(1 for r in emap.values() if r["decoder_version"]==v) for v in ("kamino_v1_legacy","kamino_v1_6_plus")},
 "request_count":reqs,"termination_evidence":terms,"semantic_conflicts":conf[:100],"duplicate_keys":dup[:100],
 "missing_keys":[list(x) for x in missing[:100]],"extra_keys":[list(x) for x in extra[:100]],
 "enriched_rows":sorted(emap.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],ak(r["instructionAddress"]))),
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
 "token_amounts":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
 "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["partition_id","classification","baseline_success_count","enriched_success_count","missing_count","extra_count","semantic_conflict_count","decoder_version_counts"]},indent=2))
if not passed:raise SystemExit(2)

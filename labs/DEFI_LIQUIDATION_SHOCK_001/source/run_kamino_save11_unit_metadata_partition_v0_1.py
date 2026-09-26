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
   "filter":"d8","disc":"0xb1479abce2854a37","prefix":"b1479abce2854a37",
   "cls":"liquidate_obligation_and_redeem_reserve_collateral",
   "lower":"2023-11-17T14:48:24Z","upper":"2025-01-01T00:00:00Z","exact_accounts":16,
   "unit_roles":{
      "debt_underlying":[5,11],
      "collateral_token":[8,12],
      "collateral_underlying":[9,13]
   }
 },
 "save11":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "filter":"d1","disc":"0x11","prefix":"11",
   "cls":"LiquidateObligationAndRedeemReserveCollateral",
   "lower":"2024-07-19T19:30:52Z","upper":"2025-01-01T00:00:00Z","exact_accounts":15,
   "unit_roles":{
      "debt_underlying":[0,4],
      "collateral_token":[1,7],
      "collateral_underlying":[2,8]
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
def key(protocol,cls,sig,addr): return (protocol,cls,sig,addr_key(addr))

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-ks-unit/0.1"}
    if data is not None: headers["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(60,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(60,2**i))
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

def load_baseline(root,protocol,cls,start,end):
    lo=iso_dt(start);hi=iso_dt(end);out={};anom=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:o=json.loads(p.read_text())
        except Exception:continue
        rows=o.get("rows")
        if not isinstance(rows,list):continue
        for r in rows:
            if r.get("protocol")!=protocol or r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":continue
            try:t=iso_dt(r.get("timestamp"))
            except Exception:
                anom.append({"reason":"bad_timestamp","signature":r.get("signature")});continue
            if not (lo<=t<hi):continue
            sig=r.get("signature");addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anom.append({"reason":"bad_identity","signature":sig});continue
            k=key(protocol,cls,sig,addr)
            if k in out and out[k]!=r:anom.append({"reason":"duplicate_conflict","signature":sig,"instructionAddress":addr})
            out[k]=r
    return out,anom

def pairs_for(tb):
    s=set()
    if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
        s.add((tb["preMint"],int(tb["preDecimals"])))
    if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
        s.add((tb["postMint"],int(tb["postDecimals"])))
    return s

def role_pair(accounts,tbmap,positions):
    observed=[]
    for pos in positions:
        if pos>=len(accounts): return None,{"reason":"account_position_missing","position":pos}
        a=accounts[pos];pairs=sorted(tbmap.get(a,set()))
        observed.append({"position":pos,"account":a,"pairs":[{"mint":m,"decimals":d} for m,d in pairs]})
        if len(pairs)!=1:return None,{"reason":"token_metadata_not_exactly_one_pair","observed":observed}
    if observed[0]["pairs"]!=observed[1]["pairs"]:
        return None,{"reason":"paired_accounts_unit_mismatch","observed":observed}
    p=observed[0]["pairs"][0]
    return {"mint":p["mint"],"decimals":p["decimals"],"source_accounts":[observed[0]["account"],observed[1]["account"]]},None

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=sorted(CFG),required=True)
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args();c=CFG[args.protocol]
start=max(iso_dt(args.start),iso_dt(c["lower"])).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(c["upper"])).isoformat().replace("+00:00","Z")
baseline,banom=load_baseline(args.baseline,args.protocol,c["cls"],start,end)

lo=iso_dt(start);hi=iso_dt(end);lo_ts=int(lo.timestamp());hi_ts=int(hi.timestamp())
current=ts_slot(start);to_slot=ts_slot(end)+16
seen={};event_units=[];conflicts=[];qanom=[];reqs=0;terms=[]
while current<=to_slot:
    filt={"programId":[c["program"]],c["filter"]:[c["disc"]],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True},
                    "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,
                                    "preDecimals":True,"postDecimals":True}},
          "instructions":[filt]}
    st,h,raw=req(STREAM,body);reqs+=1
    if st==204:
        terms.append({"http_status":204,"from_slot":current});break
    if st!=200:raise RuntimeError(f"stream_http_{st}")
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
            ti=tb.get("transactionIndex");a=tb.get("account")
            if ti is None or not a:continue
            tb_by_tx.setdefault(ti,{}).setdefault(a,set()).update(pairs_for(tb))
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=c["program"]:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(bytes.fromhex(c["prefix"])):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict):
                qanom.append({"reason":"missing_parent_transaction","slot":slot});continue
            if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list) or len(accounts)!=c["exact_accounts"]:
                qanom.append({"reason":"bad_identity_or_account_shape","signature":sig,"account_count":len(accounts)});continue
            k=key(args.protocol,c["cls"],sig,addr)
            if k in seen:
                conflicts.append({"reason":"duplicate_enriched_key","signature":sig,"instructionAddress":addr});continue
            units={};errs=[]
            tbmap=tb_by_tx.get(ti,{})
            for role,positions in c["unit_roles"].items():
                pair,err=role_pair(accounts,tbmap,positions)
                if err:errs.append({"role":role,**err})
                else:units[role]=pair
            seen[k]={"signature":sig,"instructionAddress":addr}
            if errs:
                conflicts.append({"signature":sig,"instructionAddress":addr,"unit_errors":errs})
            else:
                event_units.append({"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,**units})
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1

missing=sorted(set(baseline)-set(seen));extra=sorted(set(seen)-set(baseline))
passed=not banom and not qanom and not conflicts and not missing and not extra and len(event_units)==len(baseline)
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":args.protocol,
 "partition_id":args.partition_id,"effective_start":start,"effective_end":end,
 "classification":"KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS" if passed else "KAMINO_SAVE11_UNIT_METADATA_PARTITION_FAIL_CLOSED",
 "baseline_success_count":len(baseline),"enriched_success_count":len(seen),"unit_complete_event_count":len(event_units),
 "missing_count":len(missing),"extra_count":len(extra),"baseline_anomaly_count":len(banom),
 "query_anomaly_count":len(qanom),"unit_conflict_count":len(conflicts),
 "event_units":event_units,"conflict_examples":conflicts[:100],"query_anomaly_examples":qanom[:100],
 "request_count":reqs,"termination_evidence":terms,"amount_fields_requested":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["protocol","partition_id","classification","baseline_success_count","enriched_success_count",
 "unit_complete_event_count","missing_count","extra_count","query_anomaly_count","unit_conflict_count"]},indent=2))
if not passed:raise SystemExit(2)

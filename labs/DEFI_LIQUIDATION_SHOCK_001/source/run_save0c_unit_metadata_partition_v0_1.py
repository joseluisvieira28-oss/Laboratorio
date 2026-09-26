#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
LOWER="2021-12-08T00:00:00Z";UPPER="2025-01-01T00:00:00Z"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP:raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def iso_dt(s):return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm_ts(v):
    if isinstance(v,str):return v
    if isinstance(v,(int,float)):return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def addr_key(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def key(sig,addr):return ("save0c","LiquidateObligation",sig,addr_key(addr))

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-save0c-unit/0.1"}
    if data is not None:headers["Content-Type"]="application/json"
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
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

def load_baseline(root,start,end):
    lo=iso_dt(start);hi=iso_dt(end);out={};anom=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:o=json.loads(p.read_text())
        except Exception:continue
        rows=o.get("rows")
        if not isinstance(rows,list):continue
        for r in rows:
            if r.get("protocol")!="save0c" or r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":continue
            try:t=iso_dt(r.get("timestamp"))
            except Exception:
                anom.append({"reason":"bad_timestamp","signature":r.get("signature")});continue
            if not (lo<=t<hi):continue
            sig=r.get("signature");addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anom.append({"reason":"bad_identity","signature":sig});continue
            k=key(sig,addr)
            if k in out and out[k]!=r:anom.append({"reason":"duplicate_conflict","signature":sig,"instructionAddress":addr})
            out[k]=r
    return out,anom

def tb_pairs(tb):
    s=set()
    if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
        s.add((tb["preMint"],int(tb["preDecimals"])))
    if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
        s.add((tb["postMint"],int(tb["postDecimals"])))
    return s

def exact_pair(accounts,tbmap,positions):
    vals=[]
    for pos in positions:
        if pos>=len(accounts):return None,{"reason":"account_position_missing","position":pos}
        a=accounts[pos];pairs=sorted(tbmap.get(a,set()))
        vals.append({"position":pos,"account":a,"pairs":[{"mint":m,"decimals":d} for m,d in pairs]})
        if len(pairs)!=1:return None,{"reason":"token_metadata_not_exactly_one_pair","observed":vals}
    if vals[0]["pairs"]!=vals[1]["pairs"]:
        return None,{"reason":"paired_accounts_unit_mismatch","observed":vals}
    p=vals[0]["pairs"][0]
    return {"mint":p["mint"],"decimals":p["decimals"],"source_accounts":[vals[0]["account"],vals[1]["account"]]},None

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True)
ap.add_argument("--registry",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args()
start=max(iso_dt(args.start),iso_dt(LOWER)).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(UPPER)).isoformat().replace("+00:00","Z")
baseline,banom=load_baseline(args.baseline,start,end)
reg_obj=json.loads(Path(args.registry).read_text())
registry={x["reserve"]:x for x in reg_obj["reserves"]}

lo=iso_dt(start);hi=iso_dt(end);lo_ts=int(lo.timestamp());hi_ts=int(hi.timestamp())
current=ts_slot(start);to_slot=ts_slot(end)+16
seen={};event_units=[];conflicts=[];qanom=[];reqs=0;terms=[];unmapped={}
while current<=to_slot:
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True},
                    "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,
                                    "preDecimals":True,"postDecimals":True}},
          "instructions":[{"programId":[PROGRAM],"d1":["0x0c"],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}]}
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
            tb_by_tx.setdefault(ti,{}).setdefault(a,set()).update(tb_pairs(tb))
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(b"\x0c"):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict):
                qanom.append({"reason":"missing_parent_transaction","slot":slot});continue
            if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list) or len(accounts)!=12:
                qanom.append({"reason":"bad_identity_or_account_shape","signature":sig,"account_count":len(accounts)});continue
            k=key(sig,addr)
            if k in seen:
                conflicts.append({"reason":"duplicate_enriched_key","signature":sig,"instructionAddress":addr});continue
            seen[k]=True;tbmap=tb_by_tx.get(ti,{})
            debt,de=exact_pair(accounts,tbmap,[0,3]);ctok,ce=exact_pair(accounts,tbmap,[1,5])
            if de or ce:
                conflicts.append({"signature":sig,"instructionAddress":addr,"debt_error":de,"collateral_token_error":ce});continue
            reserve=accounts[4];mapped=registry.get(reserve)
            collateral_underlying=None
            if mapped is None:
                unmapped[reserve]=unmapped.get(reserve,0)+1
            else:
                if ctok["mint"]!=mapped["collateral_mint"]:
                    conflicts.append({"signature":sig,"instructionAddress":addr,"reason":"pinned_registry_collateral_mint_conflict",
                                      "reserve":reserve,"observed_collateral_mint":ctok["mint"],
                                      "expected_collateral_mint":mapped["collateral_mint"]});continue
                collateral_underlying={"mint":mapped["underlying_mint"],"decimals":int(mapped["underlying_decimals"]),
                                       "reserve":reserve,"source":"SAVE0C_2021_PRODUCTION_RESERVE_REGISTRY_V0.1"}
            event_units.append({"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,
                                "withdraw_reserve":reserve,"debt_underlying":debt,
                                "collateral_token":ctok,"collateral_underlying":collateral_underlying,
                                "reserve_registry_mapped":mapped is not None})
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1

missing=sorted(set(baseline)-set(seen));extra=sorted(set(seen)-set(baseline))
direct_complete=sum(1 for e in event_units if e.get("debt_underlying") and e.get("collateral_token"))
mapped_count=sum(1 for e in event_units if e.get("reserve_registry_mapped"))
blocked=bool(banom or qanom or conflicts or missing or extra or direct_complete!=len(baseline))
if blocked:classification="SAVE0C_UNIT_METADATA_PARTITION_BLOCKED_FAIL_CLOSED"
elif mapped_count==len(baseline):classification="SAVE0C_UNIT_METADATA_PARTITION_PASS"
else:classification="SAVE0C_UNIT_METADATA_PARTITION_PARTIAL_SOURCE_COVERAGE"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"save0c",
 "partition_id":args.partition_id,"effective_start":start,"effective_end":end,"classification":classification,
 "baseline_success_count":len(baseline),"enriched_success_count":len(seen),"direct_unit_complete_event_count":direct_complete,
 "collateral_underlying_mapped_event_count":mapped_count,
 "collateral_underlying_unmapped_event_count":len(baseline)-mapped_count,
 "missing_count":len(missing),"extra_count":len(extra),"baseline_anomaly_count":len(banom),
 "query_anomaly_count":len(qanom),"conflict_count":len(conflicts),
 "unmapped_reserves":[{"reserve":r,"event_count":n} for r,n in sorted(unmapped.items())],
 "event_units":event_units,"conflict_examples":conflicts[:100],"query_anomaly_examples":qanom[:100],
 "request_count":reqs,"termination_evidence":terms,"amount_fields_requested":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "token_amounts":False,"token_balance_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["partition_id","classification","baseline_success_count","enriched_success_count",
 "direct_unit_complete_event_count","collateral_underlying_mapped_event_count","collateral_underlying_unmapped_event_count",
 "missing_count","extra_count","query_anomaly_count","conflict_count"]},indent=2))
if blocked:raise SystemExit(2)

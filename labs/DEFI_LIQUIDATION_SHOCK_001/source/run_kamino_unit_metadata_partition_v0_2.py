#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream";TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD";PREFIX="b1479abce2854a37";DISC="0xb1479abce2854a37"
CLS="liquidate_obligation_and_redeem_reserve_collateral";LOWER="2023-11-17T14:48:24Z";UPPER="2025-01-01T00:00:00Z"
BOUNDARY="2024-06-19T19:15:17Z";SOURCE_V2="2024-06-19T15:31:40Z"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP:raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b"";return b"\x00"*(len(s)-len(s.lstrip("1")))+raw
def iso(s):return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm(v):
    if isinstance(v,str):return v
    if isinstance(v,(int,float)):return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
def ak(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def key(sig,addr):return ("kamino",CLS,sig,ak(addr))
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-kamino-unit/0.2"}
    if data is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST");last=None
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
def pairs(tb):
    s=set()
    if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):s.add((tb["preMint"],int(tb["preDecimals"])))
    if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):s.add((tb["postMint"],int(tb["postDecimals"])))
    return s
def load_baseline(root,start,end):
    lo,hi=iso(start),iso(end);out={};anom=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:o=json.loads(p.read_text())
        except Exception:continue
        for r in o.get("rows") or []:
            if r.get("protocol")!="kamino" or r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":continue
            try:t=iso(r.get("timestamp"))
            except Exception:anom.append({"reason":"bad_timestamp","signature":r.get("signature")});continue
            if not(lo<=t<hi):continue
            sig=r.get("signature");addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):anom.append({"reason":"bad_identity","signature":sig});continue
            k=key(sig,addr)
            if k in out and out[k]!=r:anom.append({"reason":"duplicate_conflict","signature":sig})
            out[k]=r
    return out,anom
def layout(ts,accounts):
    if iso(ts)<iso(BOUNDARY):
        if len(accounts)!=16:return None,{"reason":"legacy_shape_mismatch","observed":len(accounts)}
        return ("kamino_v1_legacy",{"debt_underlying":(5,11),"collateral_token":(8,12),"collateral_underlying":(9,13)}),None
    if iso(ts)<iso(SOURCE_V2):return None,{"reason":"v2_before_source_support"}
    if len(accounts)<20:return None,{"reason":"v2_fixed_prefix_missing","observed":len(accounts)}
    return ("kamino_v1_6_plus",{"debt_underlying":(6,13),"collateral_token":(10,14),"collateral_underlying":(11,15)}),None
def resolve_role(accounts,tbmap,primary_pos,optional_pos):
    if primary_pos>=len(accounts):return None,{"reason":"primary_account_position_missing","position":primary_pos}
    pa=accounts[primary_pos];pp=sorted(tbmap.get(pa,set()))
    if len(pp)!=1:return None,{"reason":"primary_token_metadata_not_exactly_one_pair","position":primary_pos,"account":pa,"pairs":[{"mint":m,"decimals":d} for m,d in pp]}
    mint,dec=pp[0];oa=accounts[optional_pos] if optional_pos<len(accounts) else None;op=sorted(tbmap.get(oa,set())) if oa else []
    if len(op)>1:return None,{"reason":"optional_crosscheck_ambiguous","position":optional_pos,"account":oa,"pairs":[{"mint":m,"decimals":d} for m,d in op]}
    if len(op)==1 and op[0]!=(mint,dec):return None,{"reason":"optional_crosscheck_unit_mismatch","primary":{"account":pa,"mint":mint,"decimals":dec},"optional":{"account":oa,"mint":op[0][0],"decimals":op[0][1]}}
    return {"mint":mint,"decimals":dec,"primary_source_account":pa,"optional_crosscheck_account":oa,
            "optional_crosscheck_status":"MATCH" if len(op)==1 else "UNAVAILABLE"},None

ap=argparse.ArgumentParser();ap.add_argument("--start",required=True);ap.add_argument("--end",required=True);ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args();start=max(iso(args.start),iso(LOWER)).isoformat().replace("+00:00","Z");end=min(iso(args.end),iso(UPPER)).isoformat().replace("+00:00","Z")
baseline,banom=load_baseline(args.baseline,start,end);lo,hi=iso(start),iso(end);current=ts_slot(start);to_slot=ts_slot(end)+16
seen={};event_units=[];conf=[];qanom=[];terms=[];reqs=0;version_counts={"kamino_v1_legacy":0,"kamino_v1_6_plus":0}
while current<=to_slot:
    filt={"programId":[PROGRAM],"d8":[DISC],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
      "fields":{"block":{"number":True,"timestamp":True},"transaction":{"transactionIndex":True,"signatures":True,"err":True},
      "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True},
      "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True}},
      "instructions":[filt]}
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
        tb_by={}
        for tb in b.get("tokenBalances") or []:
            ti=tb.get("transactionIndex");a=tb.get("account")
            if ti is None or not a:continue
            tb_by.setdefault(ti,{}).setdefault(a,set()).update(pairs(tb))
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(bytes.fromhex(PREFIX)):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict) or tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None;addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list):qanom.append({"reason":"bad_identity","slot":slot});continue
            k=key(sig,addr)
            if k in seen:conf.append({"reason":"duplicate_enriched_key","signature":sig});continue
            lay,err=layout(ts,accounts);seen[k]={"signature":sig}
            if err:conf.append({"signature":sig,"instructionAddress":addr,**err});continue
            ver,roles=lay;version_counts[ver]+=1;units={};errs=[];tbmap=tb_by.get(ti,{})
            for role,(primary,optional) in roles.items():
                u,e=resolve_role(accounts,tbmap,primary,optional)
                if e:errs.append({"role":role,**e})
                else:units[role]=u
            if errs:conf.append({"signature":sig,"instructionAddress":addr,"decoder_version":ver,"unit_errors":errs})
            else:event_units.append({"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,"decoder_version":ver,**units})
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1
missing=sorted(set(baseline)-set(seen));extra=sorted(set(seen)-set(baseline))
passed=not banom and not qanom and not conf and not missing and not extra and len(event_units)==len(baseline)
receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"kamino","partition_id":args.partition_id,
 "classification":"KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS" if passed else "KAMINO_SAVE11_UNIT_METADATA_PARTITION_FAIL_CLOSED",
 "effective_start":start,"effective_end":end,"baseline_success_count":len(baseline),"enriched_success_count":len(seen),
 "unit_complete_event_count":len(event_units),"missing_count":len(missing),"extra_count":len(extra),
 "baseline_anomaly_count":len(banom),"query_anomaly_count":len(qanom),"unit_conflict_count":len(conf),
 "decoder_version_counts":version_counts,"event_units":event_units,"conflict_examples":conf[:100],"query_anomaly_examples":qanom[:100],
 "request_count":reqs,"termination_evidence":terms,"amount_fields_requested":False,
 "unit_authority":"protocol_reserve_vault_primary; user_token_optional_crosscheck",
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
 "token_amounts":False,"token_balance_amounts":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
 "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["partition_id","classification","baseline_success_count","enriched_success_count","unit_complete_event_count","missing_count","extra_count","unit_conflict_count","decoder_version_counts"]},indent=2))
if not passed:raise SystemExit(2)

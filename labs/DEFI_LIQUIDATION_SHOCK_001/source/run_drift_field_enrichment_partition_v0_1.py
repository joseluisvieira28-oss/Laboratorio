#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
LOWER="2022-11-04T15:17:54Z"; UPPER="2025-01-01T00:00:00Z"

CLASSES={
 "liquidate_perp":{"prefix":"4b2377f7bf128b02","allowed_lengths":[19,27],"index_kind":"perp_only"},
 "liquidate_spot":{"prefix":"6b00802923e5fb12","allowed_lengths":[29,37],"index_kind":"spot_pair"},
 "liquidate_borrow_for_perp_pnl":{"prefix":"a911205acf94d11b","allowed_lengths":[29,37],"index_kind":"perp_spot"},
 "liquidate_perp_pnl_for_deposit":{"prefix":"ed4bc6ebe9ba4b23","allowed_lengths":[29,37],"index_kind":"perp_spot"},
}
ROLES={"state":0,"authority":1,"liquidator":2,"liquidatorStats":3,"liquidated_user":4,"userStats":5}

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

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
def key(cls,sig,addr): return ("drift",cls,sig,addr_key(addr))
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-drift-field-enrichment/0.1"}
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

def class_from_data(dec):
    for cls,c in CLASSES.items():
        if dec.startswith(bytes.fromhex(c["prefix"])): return cls
    return None

def market_identity(cls,dec):
    if len(dec)<10: return None
    k=CLASSES[cls]["index_kind"]
    if k=="perp_only":
        return {"perp_market_index":int.from_bytes(dec[8:10],"little")}
    if len(dec)<12: return None
    a=int.from_bytes(dec[8:10],"little"); b=int.from_bytes(dec[10:12],"little")
    if k=="spot_pair":
        return {"asset_spot_market_index":a,"liability_spot_market_index":b}
    return {"perp_market_index":a,"spot_market_index":b}

def load_baseline(root,start,end):
    lo=iso_dt(start); hi=iso_dt(end); keys={}; files=[]; anomalies=[]; manifests=[]
    for p in sorted(Path(root).rglob("MANIFEST.json")):
        try:
            with p.open("r",encoding="utf-8") as fh:m=json.load(fh)
        except Exception:
            anomalies.append({"reason":"baseline_manifest_unreadable","file":str(p)}); continue
        manifests.append({"file":str(p),"classification":m.get("classification")})
        if m.get("classification")!="PARTITION_COMPLETE":
            anomalies.append({"reason":"baseline_manifest_not_complete","file":str(p),"classification":m.get("classification")})
    if not manifests:
        anomalies.append({"reason":"baseline_manifest_missing"})
    for p in sorted(Path(root).rglob("*.json")):
        if p.name=="MANIFEST.json": continue
        try:
            with p.open("r",encoding="utf-8") as fh:o=json.load(fh)
        except Exception: continue
        rows=o.get("rows")
        if not isinstance(rows,list): continue
        files.append(str(p))
        for r in rows:
            if r.get("protocol")!="drift": continue
            if r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": continue
            cls=r.get("class")
            if cls not in CLASSES:
                anomalies.append({"reason":"baseline_unknown_class","class":cls,"signature":r.get("signature")}); continue
            try:t=iso_dt(r.get("timestamp"))
            except Exception:
                anomalies.append({"reason":"baseline_bad_timestamp","signature":r.get("signature")}); continue
            if not (lo<=t<hi): continue
            sig=r.get("signature"); addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anomalies.append({"reason":"baseline_bad_identity","signature":sig}); continue
            k=key(cls,sig,addr)
            if k in keys and keys[k]!=r:
                anomalies.append({"reason":"baseline_duplicate_conflict","class":cls,"signature":sig,"instructionAddress":addr})
            keys[k]=r
    return keys,files,manifests,anomalies

def enrich(start,end):
    lo=iso_dt(start); hi=iso_dt(end); lo_ts=int(lo.timestamp()); hi_ts=int(hi.timestamp())
    current=ts_slot(start); to_slot=ts_slot(end)+16
    rows=[]; terms=[]; reqs=0; anomalies=[]
    while current<=to_slot:
        body={"type":"solana","fromBlock":current,"toBlock":to_slot,
              "fields":{"block":{"number":True,"timestamp":True},
                        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                        "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                       "instructionAddress":True,"isCommitted":True,"error":True}},
              "instructions":[{"programId":[PROGRAM],"transaction":True}]}
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
                if ix.get("programId")!=PROGRAM: continue
                try:dec=b58decode(ix.get("data",""))
                except Exception:continue
                cls=class_from_data(dec)
                if cls is None: continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict):
                    anomalies.append({"reason":"missing_parent_transaction","class":cls,"slot":slot,"instructionAddress":ix.get("instructionAddress")}); continue
                sigs=tx.get("signatures") or []; sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                addr=ix.get("instructionAddress")
                if not sig or not isinstance(addr,list):
                    anomalies.append({"reason":"bad_identity","class":cls,"slot":slot}); continue
                if not (tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None):
                    continue
                accounts=ix.get("accounts") or []; data=ix.get("data") or ""
                semantic={name:(accounts[idx] if idx<len(accounts) else None) for name,idx in ROLES.items()}
                market=market_identity(cls,dec)
                rows.append({"protocol":"drift","class":cls,"instruction_class":cls,"signature":sig,
                             "slot":slot,"timestamp":ts,"transactionIndex":ti,"instructionAddress":addr,
                             "programId":PROGRAM,"decoded_prefix_hex":CLASSES[cls]["prefix"],
                             "instruction_data_base58":data,"instruction_data_byte_length":len(dec),
                             "accounts":accounts,"account_count":len(accounts),"semantic_accounts":semantic,
                             "dynamic_remaining_accounts":accounts[6:] if len(accounts)>=6 else [],
                             "market_identity":market,
                             "economic_argument_values_emitted":False,
                             "field_status":{"identity":"FIELD_PRESENT_DIRECT","instruction_data":"FIELD_PRESENT_DIRECT",
                               "semantic_accounts":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY",
                               "market_identity":"FIELD_PRESENT_DERIVED_WITH_PINNED_AUTHORITY"}})
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1
    return rows,reqs,terms,anomalies

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args()
start=max(iso_dt(args.start),iso_dt(LOWER)).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(UPPER)).isoformat().replace("+00:00","Z")

baseline,files,manifests,banom=load_baseline(args.baseline,start,end)
enriched,reqs,terms,qanom=enrich(start,end)

emap={};duplicates=[];conflicts=[]
for r in enriched:
    k=key(r["class"],r["signature"],r["instructionAddress"])
    if k in emap:duplicates.append({"class":r["class"],"signature":r["signature"],"instructionAddress":r["instructionAddress"]})
    emap[k]=r
    cfg=CLASSES[r["class"]]
    if r["account_count"]<6:
        conflicts.append({"class":r["class"],"signature":r["signature"],"reason":"fixed_account_prefix_missing","account_count":r["account_count"]})
    if r["instruction_data_byte_length"] not in cfg["allowed_lengths"]:
        conflicts.append({"class":r["class"],"signature":r["signature"],"reason":"abi_length_not_allowed",
                          "observed":r["instruction_data_byte_length"],"allowed":cfg["allowed_lengths"]})
    if any(v is None for v in r["semantic_accounts"].values()):
        conflicts.append({"class":r["class"],"signature":r["signature"],"reason":"required_semantic_account_missing"})
    if not isinstance(r.get("market_identity"),dict) or not r["market_identity"]:
        conflicts.append({"class":r["class"],"signature":r["signature"],"reason":"market_identity_decode_failed"})

missing=sorted(set(baseline)-set(emap)); extra=sorted(set(emap)-set(baseline))
passed=not banom and not qanom and not duplicates and not conflicts and not missing and not extra
class_counts={cls:{"baseline":0,"enriched":0} for cls in CLASSES}
for k in baseline: class_counts[k[1]]["baseline"]+=1
for k in emap: class_counts[k[1]]["enriched"]+=1

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"drift",
 "partition_id":args.partition_id,"effective_start":start,"effective_end":end,
 "classification":"FIELD_ENRICHMENT_PARTITION_PASS" if passed else "FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED",
 "baseline_source_files":files,"baseline_manifests":manifests,
 "baseline_success_count":len(baseline),"enriched_success_count":len(emap),"class_counts":class_counts,
 "missing_count":len(missing),"extra_count":len(extra),"duplicate_count":len(duplicates),
 "semantic_conflict_count":len(conflicts),"baseline_anomaly_count":len(banom),"query_anomaly_count":len(qanom),
 "nonempty_accounts_count":sum(1 for r in emap.values() if r["account_count"]>0),
 "market_identity_count":sum(1 for r in emap.values() if r.get("market_identity")),
 "abi_shape_valid_count":sum(1 for r in emap.values() if r["instruction_data_byte_length"] in CLASSES[r["class"]]["allowed_lengths"]),
 "request_count":reqs,"termination_evidence":terms,
 "missing_keys":[list(x) for x in missing[:100]],"extra_keys":[list(x) for x in extra[:100]],
 "duplicate_keys":duplicates[:100],"semantic_conflicts":conflicts[:100],
 "enriched_rows":sorted(emap.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],addr_key(r["instructionAddress"]))),
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "token_balances":False,"token_amounts":False,"token_decimals":False,"limit_price_values":False,
             "requested_max_amount_values":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["partition_id","classification","baseline_success_count","enriched_success_count","missing_count","extra_count","semantic_conflict_count","class_counts"]},indent=2))
if not passed:raise SystemExit(2)

#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,os,time,urllib.error,urllib.request,sys
from collections import defaultdict
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"source"))
import run_alternative_source_equivalence_v0_1 as a2

LAB="DEFI-LIQUIDATION-SHOCK-001"
SOL="So11111111111111111111111111111111111111112"
MARKET="mint:"+SOL
OUT=Path("route_a5a_equivalence")
MAX_PROBE_PAGES=8
MAX_FULL_PAGES=10
MIN_SHARD_SECONDS=900
MAX_DEPTH=16

ROLE_ACCOUNTS={
 "marginfi":{"BpmLoZcyKJP9Jncq5TE7TTzxPV6PSbKNZkuvU1MB6t8e","CCKtUs6Cgwo4aaQUmBPmyoApH2gUDErxNZCAntD6LYGh"},
 "save0c":{"3WPYWiZtc2uJq1JiF3Z3KswicFAp5VrFgEHwP3CkuDUn","7trBAMkVU8dcPQVdScz7VNywZwqnD1rwXkwkVPQJ95bT",
           "8xogd14bBxBdGKDfkDciPPp6pZ3Cw4Yj5USRbGJDbZpA","UTABCRXirrbpCNDogCoqEECtM3V44jXGCsK23ZepV3Z"},
 "kamino":{"GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U"},
 "save11":{"8UviNr47S8eL6J3WfDxMRa3hvLta1VDJwNWqsDgtN3Cv","5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY",
           "8jVVXXxzC9N5FeHUxKBgXLM8xARzLpnzXz8dqZHzpykY","APJAFijv9XrtnrAvktzsqgJboq4Uhs3mu7YN7DQ5bFMH",
           "6ToFgS59GXhYMoHHL2GNPh5aNypxc1UAR1RYpfdHftBE","6s8hmMLgdhpffsL7H9neZBhFSxaQYTnQ1gkjaRN25GS7"}
}
CLASSES={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}

def unix(s): return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")
def digest(b): return hashlib.sha256(b).hexdigest()
def stable_hash(x): return digest(json.dumps(x,sort_keys=True,separators=(",",":")).encode())

def initial_shards():
    out=[("boundary-20231231",unix("2023-12-31T00:00:00Z"),unix("2024-01-01T00:00:00Z"))]
    for m in range(1,13):
        a=dt.datetime(2024,m,1,tzinfo=dt.timezone.utc)
        b=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(2024,m+1,1,tzinfo=dt.timezone.utc)
        out.append((f"2024-{m:02d}",int(a.timestamp()),int(b.timestamp())))
    return out

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY");url=os.environ.get("DLS_RPC_URL")
        if key:self.url="https://mainnet.helius-rpc.com/?api-key="+key
        elif url:self.url=url
        else:raise RuntimeError("credential_absent")
        self.calls=0
    def call(self,method,params):
        if method not in ("getTransactionsForAddress","getBlock"):
            raise RuntimeError("unauthorized_method")
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
        last=None
        for attempt in range(5):
            time.sleep(.27)
            try:
                req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-DLS-A5A/0.1"},method="POST")
                with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
                obj=json.loads(raw)
                if obj.get("error"):
                    code=(obj.get("error") or {}).get("code")
                    raise RuntimeError(f"rpc_error_code:{code}")
                self.calls+=1
                return obj.get("result"),digest(raw)
            except urllib.error.HTTPError as e:
                if e.code in (401,402,403):raise RuntimeError(f"capability_or_credential_rejected:{e.code}") from None
                last=f"http_{e.code}"
            except (urllib.error.URLError,TimeoutError,OSError) as e:last="transport"
            except RuntimeError as e:
                if "rpc_error_code:" in str(e):last=str(e)
                else:raise
            if attempt<4:time.sleep(min(12,2**attempt))
        raise RuntimeError("rpc_transport_exhausted:"+str(last))

    def _gtfa(self,address,start,end,details,page_cap):
        token=None;pages=0;count=0;items=[];seen_tokens=set();chain=b""
        while True:
            opts={"transactionDetails":details,"sortOrder":"asc","limit":1000,
                  "filters":{"blockTime":{"gte":start,"lt":end},"status":"succeeded"}}
            if token:opts["paginationToken"]=token
            res,h=self.call("getTransactionsForAddress",[address,opts])
            if not isinstance(res,dict) or not isinstance(res.get("data"),list):raise RuntimeError("gtfa_schema")
            data=res["data"];chain=hashlib.sha256(chain+bytes.fromhex(h)).digest()
            if not data:
                return {"complete":True,"pages":pages,"count":count,"items":items,
                        "hash_chain":chain.hex(),"terminal_empty_page":True}
            pages+=1;count+=len(data)
            if details=="full":items.extend(data)
            nxt=res.get("paginationToken")
            if nxt is None:
                return {"complete":True,"pages":pages,"count":count,"items":items,
                        "hash_chain":chain.hex(),"terminal_empty_page":False}
            if not isinstance(nxt,str) or not nxt or nxt==token or nxt in seen_tokens:
                raise RuntimeError("pagination_nonadvancing")
            if pages>=page_cap:
                return {"complete":False,"pages":pages,"count":count,"items":items,
                        "hash_chain":chain.hex(),"terminal_empty_page":False}
            seen_tokens.add(nxt);token=nxt

    def probe(self,address,start,end):
        return self._gtfa(address,start,end,"signatures",MAX_PROBE_PAGES)

    def full(self,address,start,end):
        return self._gtfa(address,start,end,"full",MAX_FULL_PAGES)

    def block_order(self,slot):
        res,_=self.call("getBlock",[slot,{"commitment":"finalized","transactionDetails":"signatures",
                                        "rewards":False,"maxSupportedTransactionVersion":0}])
        if not isinstance(res,dict):raise RuntimeError("getblock_null")
        sigs=res.get("signatures")
        if not isinstance(sigs,list):
            txs=res.get("transactions")
            if not isinstance(txs,list):raise RuntimeError("getblock_signature_schema")
            sigs=[]
            for x in txs:
                s=((x.get("transaction") or {}).get("signatures") or []) if isinstance(x,dict) else []
                if not s:raise RuntimeError("getblock_signature_schema")
                sigs.append(s[0])
        return {s:i for i,s in enumerate(sigs) if isinstance(s,str)}

def adaptive_leaves(rpc,address,start,end,depth=0,ledger=None):
    if ledger is None:ledger=[]
    p=rpc.probe(address,start,end)
    rec={"phase":"probe","address":address,"start":start,"end":end,"depth":depth,
         "pages":p["pages"],"count":p["count"],"complete":p["complete"],"hash_chain":p["hash_chain"]}
    ledger.append(rec)
    if p["complete"]:
        return [(start,end,p["count"],p["pages"])],ledger
    if depth>=MAX_DEPTH:raise RuntimeError("adaptive_max_depth")
    if end-start<=MIN_SHARD_SECONDS:raise RuntimeError("adaptive_min_shard_overflow")
    mid=(start+end)//2
    if mid<=start or mid>=end:raise RuntimeError("adaptive_midpoint_invalid")
    left,_=adaptive_leaves(rpc,address,start,mid,depth+1,ledger)
    right,_=adaptive_leaves(rpc,address,mid,end,depth+1,ledger)
    return left+right,ledger

def verify_partition(start,end,leaves):
    xs=sorted(leaves)
    if not xs or xs[0][0]!=start or xs[-1][1]!=end:raise RuntimeError("adaptive_partition_boundary")
    cur=start
    for a,b,_,_ in xs:
        if a!=cur or b<=a:raise RuntimeError("adaptive_partition_gap_or_overlap")
        cur=b
    if cur!=end:raise RuntimeError("adaptive_partition_terminal")
    return True

def item_sig(x):
    s=((x.get("transaction") or {}).get("signatures") or [])
    if not s or not isinstance(s[0],str):raise RuntimeError("signature_missing")
    return s[0]

def role_match(proto,ix):
    a=ix["accounts"]
    if proto=="marginfi":return len(a)>1 and a[1] in ROLE_ACCOUNTS[proto]
    if proto=="save0c":return len(a)>4 and a[4] in ROLE_ACCOUNTS[proto]
    if proto=="save11":return len(a)>8 and a[8] in ROLE_ACCOUNTS[proto]
    if proto=="kamino":
        idx=9 if len(a)==16 else 11 if len(a)>=20 else -1
        return idx>=0 and len(a)>idx and a[idx] in ROLE_ACCOUNTS[proto]
    return False

def cluster(events):
    groups=defaultdict(list)
    for e in events:groups[(e["protocol"],e["instruction_class"],MARKET)].append(e)
    out=[]
    lo=dt.datetime(2024,1,1,tzinfo=dt.timezone.utc);hi=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
    for (proto,cls,market),xs in groups.items():
        xs.sort(key=lambda e:(e["timestamp"],e["slot"],e["tx_index"],tuple(e["path"])))
        cur=None
        def finish(s):
            first=dt.datetime.fromtimestamp(s["first_ts"],dt.timezone.utc)
            last=dt.datetime.fromtimestamp(s["last_ts"],dt.timezone.utc)
            t0=last+dt.timedelta(seconds=60)
            if not(lo<=t0<hi):return
            raw="|".join([LAB,"cluster-v0.1","60",proto,cls,market,first.isoformat(),last.isoformat(),
                          s["first_signature"],s["last_signature"],str(s["event_count"])])
            out.append({"cluster_id":hashlib.sha256(raw.encode()).hexdigest(),"quiet_seconds":60,"split":"oos",
              "protocol":proto,"instruction_class":cls,"primary_market_identity":market,
              "first_event_timestamp":first.isoformat().replace("+00:00","Z"),
              "last_event_timestamp":last.isoformat().replace("+00:00","Z"),
              "t0":t0.isoformat().replace("+00:00","Z"),"event_count":s["event_count"],
              "distinct_transaction_signature_count":len(s["signatures"]),
              "first_signature":s["first_signature"],"last_signature":s["last_signature"],"source_only":True})
        for e in xs:
            if cur is None or e["timestamp"]-cur["last_ts"]>60:
                if cur is not None:finish(cur)
                cur={"first_ts":e["timestamp"],"last_ts":e["timestamp"],"event_count":1,
                     "first_signature":e["signature"],"last_signature":e["signature"],"signatures":{e["signature"]}}
            else:
                cur["last_ts"]=e["timestamp"];cur["event_count"]+=1;cur["last_signature"]=e["signature"];cur["signatures"].add(e["signature"])
        if cur is not None:finish(cur)
    return sorted(out,key=lambda x:(x["t0"],x["protocol"],x["cluster_id"]))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--canonical",required=True);args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    rpc=RPC();cfg=a2.cfg()
    tx_hash={};events_by_key={};tx_index_hint={};query_ledger=[];errors=[];dup_hits=0
    try:
      for shard,start,end in initial_shards():
        for proto in ("marginfi","save0c","kamino","save11"):
          for address in sorted(ROLE_ACCOUNTS[proto]):
            leaves,ledger=adaptive_leaves(rpc,address,start,end)
            verify_partition(start,end,leaves)
            for x in ledger:
                query_ledger.append({"shard":shard,"protocol":proto,**x})
            for a,b,probe_count,probe_pages in leaves:
                full=rpc.full(address,a,b)
                query_ledger.append({"shard":shard,"protocol":proto,"phase":"full","address":address,
                    "start":a,"end":b,"pages":full["pages"],"count":full["count"],"complete":full["complete"],
                    "probe_count":probe_count,"probe_pages":probe_pages,"hash_chain":full["hash_chain"]})
                if not full["complete"]:raise RuntimeError("full_leaf_page_ceiling")
                if full["count"]!=probe_count:raise RuntimeError("probe_full_count_mismatch")
                for item in full["items"]:
                    sig=item_sig(item);h=stable_hash(item)
                    prior=tx_hash.get(sig)
                    if prior is not None:
                        if prior!=h:raise RuntimeError("duplicate_signature_payload_conflict")
                        dup_hits+=1;continue
                    tx_hash[sig]=h
                    try:n=a2.normalize(item)
                    except Exception as exc:
                        rawtxt=json.dumps(item,separators=(",",":"))
                        if any(c["program"] in rawtxt for c in cfg.values()):
                            raise RuntimeError("target_program_normalize_error:"+type(exc).__name__)
                        continue
                    if n["err"] is not None:continue
                    ti=None
                    for key in ("transactionIndex","transactionIdx","index"):
                        if type(item.get(key)) is int:ti=item[key];break
                    if ti is not None:tx_index_hint[sig]=ti
                    for p,ix in a2.matches(n,cfg):
                        if p not in ROLE_ACCOUNTS:continue
                        if not a2.shape(p,ix):raise RuntimeError("relevant_shape_conflict")
                        if not role_match(p,ix):continue
                        if ix["path"] is None:raise RuntimeError("relevant_instruction_path_ambiguous")
                        k=(p,sig,tuple(ix["path"]))
                        ev={"protocol":p,"instruction_class":CLASSES[p],"signature":sig,"path":ix["path"],
                            "slot":n["slot"],"timestamp":n["timestamp"],"tx_index":tx_index_hint.get(sig)}
                        old=events_by_key.get(k)
                        if old is None:events_by_key[k]=ev
                        elif old!=ev:raise RuntimeError("canonical_instruction_duplicate_conflict")
    except Exception as exc:
      errors.append({"reason":str(exc)[:300]})

    events=list(events_by_key.values())
    if not errors:
      byslot=defaultdict(list)
      for e in events:byslot[(e["protocol"],e["slot"])].append(e)
      for (proto,slot),xs in byslot.items():
        sigs=sorted({e["signature"] for e in xs})
        if len(sigs)<=1 or all(e["tx_index"] is not None for e in xs):continue
        try:order=rpc.block_order(slot)
        except Exception as exc:
            errors.append({"protocol":proto,"slot":slot,"reason":"tie_order:"+str(exc)[:200]});continue
        for e in xs:
            if e["signature"] not in order:
                errors.append({"protocol":proto,"slot":slot,"signature":e["signature"],"reason":"signature_missing_from_getblock"})
            else:e["tx_index"]=order[e["signature"]]
      for e in events:
        if e["tx_index"] is None:e["tx_index"]=0

    reconstructed=cluster(events) if not errors else []
    canonical=[]
    for line in Path(args.canonical).read_text().splitlines():
        if not line.strip():continue
        x=json.loads(line)
        if x.get("split")=="oos" and x.get("primary_market_identity")==MARKET:canonical.append(x)
    cm={x["cluster_id"]:x for x in canonical};rm={x["cluster_id"]:x for x in reconstructed}
    missing=sorted(set(cm)-set(rm));extra=sorted(set(rm)-set(cm));mismatch=[]
    fields=["protocol","instruction_class","primary_market_identity","first_event_timestamp","last_event_timestamp",
            "t0","event_count","distinct_transaction_signature_count","first_signature","last_signature"]
    for k in sorted(set(cm)&set(rm)):
        bad={f:{"canonical":cm[k].get(f),"reconstructed":rm[k].get(f)} for f in fields if cm[k].get(f)!=rm[k].get(f)}
        if bad:mismatch.append({"cluster_id":k,"fields":bad})
    passed=(not errors and len(canonical)==9931 and len(reconstructed)==9931 and not missing and not extra and not mismatch)
    receipt={"schema_version":"0.1","lab_id":LAB,
      "classification":"ROUTE_A5A_SOL_ACCOUNT_EQUIVALENCE_PASS" if passed else "ROUTE_A5A_SOL_ACCOUNT_EQUIVALENCE_BLOCKED",
      "canonical_cluster_count":len(canonical),"reconstructed_cluster_count":len(reconstructed),
      "relevant_instruction_count":len(events),"queried_unique_transaction_count":len(tx_hash),
      "duplicate_query_transaction_hits":dup_hits,
      "missing_cluster_count":len(missing),"missing_cluster_ids":missing[:200],
      "extra_cluster_count":len(extra),"extra_cluster_ids":extra[:200],
      "field_mismatch_count":len(mismatch),"field_mismatches":mismatch[:100],
      "error_count":len(errors),"errors":errors[:100],"rpc_calls":rpc.calls,
      "adaptive_rules":{"max_probe_pages":MAX_PROBE_PAGES,"max_full_pages":MAX_FULL_PAGES,
                        "min_shard_seconds":MIN_SHARD_SECONDS,"max_depth":MAX_DEPTH},
      "query_ledger":query_ledger,
      "firewall":{"protected_2025_acquisition":False,"prices":False,"returns":False,"pnl":False,
                  "data_2026":False,"purchases":False,"trading":False,"orders":False,"wallets":False,
                  "exchange_mutation":False,"merge_main":False},"trading_authority":"NONE"}
    (OUT/"DLS_ROUTE_A5A_EQUIVALENCE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    with (OUT/"DLS_ROUTE_A5A_RECONSTRUCTED_2024_CLUSTERS_V0.1.ndjson").open("w") as fh:
        for x in reconstructed:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")
    print(json.dumps({k:receipt[k] for k in ["classification","canonical_cluster_count","reconstructed_cluster_count",
      "relevant_instruction_count","queried_unique_transaction_count","missing_cluster_count","extra_cluster_count",
      "field_mismatch_count","error_count","rpc_calls","duplicate_query_transaction_hits"]},indent=2),flush=True)
    if not passed:raise SystemExit(2)

if __name__=="__main__":main()

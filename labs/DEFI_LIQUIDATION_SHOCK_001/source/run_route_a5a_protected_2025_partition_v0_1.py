#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,os,time,urllib.error,urllib.request,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"source"))
import run_alternative_source_equivalence_v0_1 as a2

LAB="DEFI-LIQUIDATION-SHOCK-001"
SOL="So11111111111111111111111111111111111111112"
MAX_PROBE_PAGES=8
MAX_FULL_PAGES=10
MIN_SHARD_SECONDS=900
MAX_DEPTH=16

CLASSES={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}
ROLE_KEYS={
 "marginfi":"marginfi:asset_bank",
 "save0c":"save0c:withdraw_reserve",
 "kamino":"kamino:withdraw_reserve_liquidity_supply",
 "save11":"save11:withdraw_reserve_liquidity_supply"
}

def unix(s):return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def iso(ts):return dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")
def digest(b):return hashlib.sha256(b).hexdigest()
def stable_hash(x):return digest(json.dumps(x,sort_keys=True,separators=(",",":")).encode())

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY");url=os.environ.get("DLS_RPC_URL")
        if key:self.url="https://mainnet.helius-rpc.com/?api-key="+key
        elif url:self.url=url
        else:raise RuntimeError("credential_absent")
        self.calls=0
    def call(self,address,start,end,details,page_cap):
        token=None;pages=0;count=0;items=[];seen=set();chain=b""
        while True:
            opts={"transactionDetails":details,"sortOrder":"asc","limit":1000,
                  "filters":{"blockTime":{"gte":start,"lt":end},"status":"succeeded"}}
            if token:opts["paginationToken"]=token
            payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransactionsForAddress",
                                "params":[address,opts]},separators=(",",":")).encode()
            last=None
            for attempt in range(5):
                time.sleep(.27)
                try:
                    req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json",
                                               "User-Agent":"CryptoLab-DLS-A5A-2025/0.1"},method="POST")
                    with urllib.request.urlopen(req,timeout=90) as r:raw=r.read()
                    obj=json.loads(raw)
                    if obj.get("error"):raise RuntimeError("rpc_error_code:"+str((obj.get("error") or {}).get("code")))
                    res=obj.get("result")
                    if not isinstance(res,dict) or not isinstance(res.get("data"),list):raise RuntimeError("gtfa_schema")
                    self.calls+=1;chain=hashlib.sha256(chain+bytes.fromhex(digest(raw))).digest()
                    data=res["data"]
                    if not data:
                        return {"complete":True,"pages":pages,"count":count,"items":items,"hash_chain":chain.hex()}
                    pages+=1;count+=len(data)
                    if details=="full":items.extend(data)
                    nxt=res.get("paginationToken")
                    if nxt is None:
                        return {"complete":True,"pages":pages,"count":count,"items":items,"hash_chain":chain.hex()}
                    if not isinstance(nxt,str) or not nxt or nxt==token or nxt in seen:
                        raise RuntimeError("pagination_nonadvancing")
                    if pages>=page_cap:
                        return {"complete":False,"pages":pages,"count":count,"items":items,"hash_chain":chain.hex()}
                    seen.add(nxt);token=nxt;break
                except urllib.error.HTTPError as e:
                    if e.code in (401,402,403):raise RuntimeError(f"capability_or_credential_rejected:{e.code}") from None
                    last=f"http_{e.code}"
                except urllib.error.URLError:last="transport"
                except RuntimeError as e:
                    if "rpc_error_code:" in str(e):last=str(e)
                    else:raise
                if attempt<4:time.sleep(min(12,2**attempt))
            else:raise RuntimeError("transport_exhausted:"+str(last))

def leaves(rpc,address,start,end,depth=0,ledger=None):
    if ledger is None:ledger=[]
    p=rpc.call(address,start,end,"signatures",MAX_PROBE_PAGES)
    ledger.append({"phase":"probe","address":address,"start":start,"end":end,"depth":depth,
                   "pages":p["pages"],"count":p["count"],"complete":p["complete"],"hash_chain":p["hash_chain"]})
    if p["complete"]:return [(start,end,p["count"],p["pages"])],ledger
    if depth>=MAX_DEPTH:raise RuntimeError("adaptive_max_depth")
    if end-start<=MIN_SHARD_SECONDS:raise RuntimeError("adaptive_min_shard_overflow")
    mid=(start+end)//2
    if not(start<mid<end):raise RuntimeError("adaptive_midpoint_invalid")
    a,_=leaves(rpc,address,start,mid,depth+1,ledger)
    b,_=leaves(rpc,address,mid,end,depth+1,ledger)
    return a+b,ledger

def verify_partition(start,end,xs):
    xs=sorted(xs);cur=start
    if not xs or xs[0][0]!=start or xs[-1][1]!=end:raise RuntimeError("partition_boundary")
    for a,b,_,_ in xs:
        if a!=cur or b<=a:raise RuntimeError("partition_gap_overlap")
        cur=b
    if cur!=end:raise RuntimeError("partition_terminal")

def item_sig(x):
    s=((x.get("transaction") or {}).get("signatures") or [])
    if not s or not isinstance(s[0],str):raise RuntimeError("signature_missing")
    return s[0]

def role_account(proto,ix):
    a=ix["accounts"]
    if proto=="marginfi":
        if len(a)<=1:return None
        return a[1]
    if proto=="save0c":
        if len(a)<=4:return None
        return a[4]
    if proto=="save11":
        if len(a)<=8:return None
        return a[8]
    if proto=="kamino":
        idx=9 if len(a)==16 else 11 if len(a)>=20 else -1
        if idx<0 or len(a)<=idx:return None
        return a[idx]
    return None

def month_bounds(mm):
    m=int(mm)
    a=dt.datetime(2025,m,1,tzinfo=dt.timezone.utc)
    b=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(2025,m+1,1,tzinfo=dt.timezone.utc)
    return a,b

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--protocol",choices=sorted(CLASSES),required=True)
    ap.add_argument("--month",choices=[f"{m:02d}" for m in range(1,13)],required=True)
    ap.add_argument("--registry",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    reg=json.loads(Path(args.registry).read_text())
    assert reg["lab_id"]==LAB
    assert reg["classification"]=="SOL_ROLE_ACCOUNT_REGISTRY_2025_PASS"
    assert reg["trading_authority"]=="NONE"
    proto=args.protocol;role_key=ROLE_KEYS[proto]
    accounts=set(reg["final_registry"].get(role_key) or [])
    if not accounts:raise RuntimeError("empty_registry_role")

    a,b=month_bounds(args.month);start=int(a.timestamp());end=int(b.timestamp())
    rpc=RPC();cfg=a2.cfg();txhash={};rows_by_key={};errors=[];query_ledger=[];query_dups=0
    try:
      for address in sorted(accounts):
        ls,ledger=leaves(rpc,address,start,end)
        verify_partition(start,end,ls)
        query_ledger.extend({"protocol":proto,"month":args.month,**x} for x in ledger)
        for s,e,probe_count,probe_pages in ls:
            full=rpc.call(address,s,e,"full",MAX_FULL_PAGES)
            query_ledger.append({"phase":"full","protocol":proto,"month":args.month,"address":address,
              "start":s,"end":e,"pages":full["pages"],"count":full["count"],"complete":full["complete"],
              "probe_count":probe_count,"probe_pages":probe_pages,"hash_chain":full["hash_chain"]})
            if not full["complete"]:raise RuntimeError("full_leaf_page_ceiling")
            if full["count"]!=probe_count:raise RuntimeError("probe_full_count_mismatch")
            for item in full["items"]:
                sig=item_sig(item);h=stable_hash(item)
                if sig in txhash:
                    if txhash[sig]!=h:raise RuntimeError("duplicate_signature_payload_conflict")
                    query_dups+=1;continue
                txhash[sig]=h
                try:n=a2.normalize(item)
                except Exception as exc:
                    rawtxt=json.dumps(item,separators=(",",":"))
                    if cfg[proto]["program"] in rawtxt:raise RuntimeError("target_program_normalize_error:"+type(exc).__name__)
                    continue
                if n["err"] is not None:continue
                for p,ix in a2.matches(n,cfg):
                    if p!=proto:continue
                    if not a2.shape(p,ix):raise RuntimeError("relevant_shape_conflict")
                    ra=role_account(p,ix)
                    if ra is None:raise RuntimeError("relevant_role_shape_conflict")
                    if ra not in accounts:continue
                    if ix["path"] is None:raise RuntimeError("instruction_path_ambiguous")
                    key=(sig,tuple(ix["path"]))
                    row={"signature":sig,"instructionAddress":ix["path"],"timestamp":iso(n["timestamp"]),
                         "collateral_mint":SOL,"source_role_account":ra,"source_only":True}
                    old=rows_by_key.get(key)
                    if old is None:rows_by_key[key]=row
                    elif old!=row:raise RuntimeError("canonical_identity_conflict")
    except Exception as exc:
      errors.append({"reason":str(exc)[:300]})

    rows=sorted(rows_by_key.values(),key=lambda x:(x["timestamp"],x["signature"],json.dumps(x["instructionAddress"],separators=(",",":"))))
    receipt={
      "schema_version":"0.1","lab_id":LAB,"protocol":proto,"instruction_class":CLASSES[proto],
      "window_start":a.isoformat().replace("+00:00","Z"),"window_end":b.isoformat().replace("+00:00","Z"),
      "classification":"PROTECTED_2025_PROTOCOL_SOURCE_PASS" if not errors else "PROTECTED_2025_PROTOCOL_SOURCE_BLOCKED",
      "successful_instruction_count":len(rows),"sol_collateral_event_count":len(rows),
      "registry_role_key":role_key,"registry_account_count":len(accounts),
      "registry_identity_sha256":reg["registry_identity_sha256"],
      "duplicate_count":0,"query_duplicate_transaction_hits":query_dups,
      "error_count":len(errors),"errors":errors,"rows":rows,"rpc_calls":rpc.calls,
      "query_ledger":query_ledger,
      "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
                  "funding_2025_opened":False,"market_direction_2025_opened":False,
                  "prices_2026_opened":False,"returns_2026_opened":False,
                  "purchases":False,"trading":False,"orders":False,"wallets":False,
                  "exchange_mutation":False,"merge_main":False},
      "trading_authority":"NONE"
    }
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"protocol":proto,"month":args.month,
      "registry_account_count":len(accounts),"successful_instruction_count":len(rows),
      "error_count":len(errors),"rpc_calls":rpc.calls,"query_duplicate_transaction_hits":query_dups},indent=2),flush=True)
    if errors:raise SystemExit(2)

if __name__=="__main__":main()

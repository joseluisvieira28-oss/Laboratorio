#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,json,math,os,time,urllib.error,urllib.request,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/"source"
sys.path.insert(0,str(SRC))
import run_alternative_source_equivalence_v0_1 as a2

LAB="DEFI-LIQUIDATION-SHOCK-001"
TARGET="So11111111111111111111111111111111111111112"
TOKEN="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SYSVAR="Sysvar1nstructions1111111111111111111111111"
MAX_PROBE_PAGES=8
MAX_FULL_PAGES=10
MIN_SHARD_SECONDS=60
MAX_DEPTH=20

CLASSES={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral",
}
PROGRAM_GROUPS={
 "marginfi":["marginfi"],
 "kamino":["kamino"],
 "save":["save0c","save11"],
}

def iso_z(ts:int)->str:
    return dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")

def month_bounds(month:str):
    m=int(month)
    a=dt.datetime(2025,m,1,tzinfo=dt.timezone.utc)
    b=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(2025,m+1,1,tzinfo=dt.timezone.utc)
    return int(a.timestamp()),int(b.timestamp()),a.isoformat().replace("+00:00","Z"),b.isoformat().replace("+00:00","Z")

def stable_hash(x)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def b58e(b:bytes)->str:
    alph="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=alph[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY","").strip()
        url=os.environ.get("DLS_RPC_URL","").strip()
        if key:self.url="https://mainnet.helius-rpc.com/?api-key="+key
        elif url:self.url=url
        else:raise RuntimeError("credential_absent")
        self.calls=0

    def call(self,method,params):
        if method not in ("getTransactionsForAddress","getMultipleAccounts"):
            raise RuntimeError("unauthorized_rpc_method")
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
        last=None
        for attempt in range(6):
            time.sleep(.27)
            try:
                req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-DLS-A3A/0.1"},method="POST")
                with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
                obj=json.loads(raw)
                if obj.get("error"):
                    code=(obj.get("error") or {}).get("code")
                    msg=str((obj.get("error") or {}).get("message",""))[:160]
                    if code in (-32005,429) or "rate" in msg.lower():
                        last=f"rpc_rate_or_capacity:{code}";time.sleep(min(30,2**attempt));continue
                    raise RuntimeError(f"rpc_error_code:{code}")
                self.calls+=1
                return obj.get("result"),hashlib.sha256(raw).hexdigest()
            except urllib.error.HTTPError as e:
                if e.code in (401,402,403):raise RuntimeError(f"capability_or_credential_rejected:{e.code}") from None
                last=f"http_{e.code}"
            except (urllib.error.URLError,TimeoutError,OSError):
                last="transport"
            if attempt<5:time.sleep(min(30,2**attempt))
        raise RuntimeError("rpc_transport_exhausted:"+str(last))

    def gtfa(self,address,start,end,details,page_cap):
        token=None;seen=set();pages=0;count=0;items=[];chain=b""
        while True:
            opts={"transactionDetails":details,"sortOrder":"asc","limit":1000,
                  "filters":{"blockTime":{"gte":start,"lt":end},"status":"succeeded"}}
            if token:opts["paginationToken"]=token
            res,h=self.call("getTransactionsForAddress",[address,opts])
            if not isinstance(res,dict) or not isinstance(res.get("data"),list):
                raise RuntimeError("gtfa_schema")
            data=res["data"];chain=hashlib.sha256(chain+bytes.fromhex(h)).digest()
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
            seen.add(nxt);token=nxt

    def slices(self,keys,offset,length):
        out=[]
        for i in range(0,len(keys),100):
            chunk=keys[i:i+100]
            res,_=self.call("getMultipleAccounts",[chunk,{"encoding":"base64","commitment":"finalized","dataSlice":{"offset":offset,"length":length}}])
            if not isinstance(res,dict) or not isinstance(res.get("value"),list) or len(res["value"])!=len(chunk):
                raise RuntimeError("get_multiple_accounts_schema")
            out.extend(res["value"])
        return out

def adaptive_leaves(rpc,address,start,end,depth=0,ledger=None):
    if ledger is None:ledger=[]
    p=rpc.gtfa(address,start,end,"signatures",MAX_PROBE_PAGES)
    ledger.append({"phase":"probe","start":start,"end":end,"depth":depth,"pages":p["pages"],"count":p["count"],"complete":p["complete"],"hash_chain":p["hash_chain"]})
    if p["complete"]:return [(start,end,p["count"],p["pages"])],ledger
    if depth>=MAX_DEPTH:raise RuntimeError("adaptive_max_depth")
    if end-start<=MIN_SHARD_SECONDS:raise RuntimeError("adaptive_min_shard_overflow")
    mid=(start+end)//2
    if mid<=start or mid>=end:raise RuntimeError("adaptive_midpoint_invalid")
    left,_=adaptive_leaves(rpc,address,start,mid,depth+1,ledger)
    right,_=adaptive_leaves(rpc,address,mid,end,depth+1,ledger)
    return left+right,ledger

def verify_partition(start,end,leaves):
    xs=sorted(leaves)
    if not xs or xs[0][0]!=start or xs[-1][1]!=end:raise RuntimeError("partition_boundary")
    cur=start
    for a,b,_,_ in xs:
        if a!=cur or b<=a:raise RuntimeError("partition_gap_or_overlap")
        cur=b
    if cur!=end:raise RuntimeError("partition_terminal")

def item_sig(x):
    s=((x.get("transaction") or {}).get("signatures") or []) if isinstance(x,dict) else []
    if not s or not isinstance(s[0],str):raise RuntimeError("signature_missing")
    return s[0]

def canonical_2025_shape(proto,ix):
    a,d=ix["accounts"],ix["data"]
    if proto=="marginfi":return len(a)>=10
    if proto=="save0c":return len(a)==12 and len(d)==9
    if proto=="save11":return len(a)==15 and len(d) in (9,10)
    if proto=="kamino":
        return len(d)==32 and len(a)>=20 and a[16]==TOKEN and a[17]==TOKEN and a[18]==TOKEN and a[19]==SYSVAR
    return False

def resolve_marginfi(rows,rpc,cfg,errors):
    keys=sorted({r["_mapping_account"] for r in rows})
    if not keys:return
    vals=rpc.slices(keys,8,33);mp={}
    for key,val in zip(keys,vals):
        if val is None:errors.append({"reason":"marginfi_bank_missing","account":key});continue
        if val.get("owner")!=cfg["program"]:errors.append({"reason":"marginfi_bank_owner","account":key});continue
        try:data=base64.b64decode((val.get("data") or [""])[0])
        except Exception:errors.append({"reason":"marginfi_bank_decode","account":key});continue
        if len(data)!=33:errors.append({"reason":"marginfi_bank_slice_len","account":key,"observed":len(data)});continue
        mp[key]=(b58e(data[:32]),int(data[32]))
    for r in rows:
        x=mp.get(r["_mapping_account"])
        if x is None:continue
        r["collateral_mint"],r["collateral_decimals"]=x
        r["unit_resolution"]="FINALIZED_BANK_DATASLICE_8_33"

def resolve_save0c(rows,rpc,cfg,errors):
    keys=sorted({r["_mapping_account"] for r in rows})
    if not keys:return
    v1=rpc.slices(keys,42,33);v2=rpc.slices(keys,227,32);mp={}
    for key,a,b in zip(keys,v1,v2):
        if a is None or b is None:errors.append({"reason":"save0c_reserve_missing","account":key});continue
        if a.get("owner")!=cfg["program"] or b.get("owner")!=cfg["program"]:
            errors.append({"reason":"save0c_reserve_owner","account":key});continue
        try:da=base64.b64decode((a.get("data") or [""])[0]);db=base64.b64decode((b.get("data") or [""])[0])
        except Exception:errors.append({"reason":"save0c_reserve_decode","account":key});continue
        if len(da)!=33 or len(db)!=32:errors.append({"reason":"save0c_reserve_slice_len","account":key});continue
        mp[key]=(b58e(da[:32]),int(da[32]),b58e(db))
    for r in rows:
        x=mp.get(r["_mapping_account"])
        if x is None:continue
        r["collateral_mint"],r["collateral_decimals"]=x[0],x[1]
        r["collateral_token_mint"]=x[2];r["unit_resolution"]="FINALIZED_RESERVE_DATASLICE_42_33"

def blank_receipt(proto,start_iso,end_iso,transport):
    return {"schema_version":"0.1","lab_id":LAB,"protocol":proto,"instruction_class":CLASSES[proto],
      "window_start":start_iso,"window_end":end_iso,"classification":"PROTECTED_2025_PROTOCOL_SOURCE_PASS",
      "successful_instruction_count":0,"unique_collateral_mint_count":0,"sol_collateral_event_count":0,
      "duplicate_count":0,"error_count":0,"duplicates":[],"errors":[],"rows":[],
      "transport":transport,
      "firewall":{"prices_2025":False,"returns_2025":False,"pnl_2025":False,"funding_2025":False,
        "market_direction_2025":False,"prices_2026":False,"returns_2026":False,
        "token_amounts":False,"oracle_values":False,"post_outcome_tuning":False,
        "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--group",choices=sorted(PROGRAM_GROUPS),required=True)
    ap.add_argument("--month",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    if not (len(args.month)==2 and 1<=int(args.month)<=12):raise SystemExit("bad_month")
    start,end,start_iso,end_iso=month_bounds(args.month)
    outdir=Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    cfg=a2.cfg();members=PROGRAM_GROUPS[args.group]
    programs={cfg[p]["program"] for p in members}
    if len(programs)!=1:raise RuntimeError("group_program_mismatch")
    program=next(iter(programs));rpc=RPC();ledger=[];errors=[];transport_dups=0
    rows={p:[] for p in members};seen_ix=set();tx_hash={}
    try:
        leaves,ledger=adaptive_leaves(rpc,program,start,end)
        verify_partition(start,end,leaves)
        for a,b,probe_count,probe_pages in leaves:
            full=rpc.gtfa(program,a,b,"full",MAX_FULL_PAGES)
            ledger.append({"phase":"full","start":a,"end":b,"pages":full["pages"],"count":full["count"],"complete":full["complete"],
                           "probe_count":probe_count,"probe_pages":probe_pages,"hash_chain":full["hash_chain"]})
            if not full["complete"]:raise RuntimeError("full_leaf_page_ceiling")
            if full["count"]!=probe_count:raise RuntimeError("probe_full_count_mismatch")
            for item in full["items"]:
                sig=item_sig(item);h=stable_hash(item)
                if sig in tx_hash:
                    if tx_hash[sig]!=h:raise RuntimeError("duplicate_signature_payload_conflict")
                    transport_dups+=1;continue
                tx_hash[sig]=h
                try:n=a2.normalize(item)
                except Exception as exc:
                    raise RuntimeError("program_transaction_normalize_error:"+type(exc).__name__) from exc
                if n["err"] is not None:raise RuntimeError("status_filter_returned_failed_transaction")
                if not (start<=int(n["timestamp"])<end):raise RuntimeError("transaction_outside_partition")
                for proto,ix in a2.matches(n,cfg):
                    if proto not in members:continue
                    if not canonical_2025_shape(proto,ix):
                        raise RuntimeError("canonical_2025_shape_conflict:"+proto)
                    if ix["path"] is None:raise RuntimeError("relevant_instruction_path_ambiguous:"+proto)
                    ident=(proto,sig,tuple(ix["path"]))
                    if ident in seen_ix:raise RuntimeError("duplicate_canonical_instruction")
                    seen_ix.add(ident)
                    r={"protocol":proto,"instruction_class":CLASSES[proto],"signature":sig,
                       "instructionAddress":ix["path"],"slot":int(n["slot"]),"timestamp":iso_z(int(n["timestamp"])),
                       "account_count":len(ix["accounts"]),"data_length":len(ix["data"])}
                    if proto=="marginfi":
                        r["_mapping_account"]=ix["accounts"][1]
                    elif proto=="save0c":
                        r["_mapping_account"]=ix["accounts"][4]
                    elif proto=="kamino":
                        r["collateral_mint"]=ix["accounts"][8];r["unit_resolution"]="DIRECT_WITHDRAW_LIQUIDITY_MINT_ACCOUNT"
                    elif proto=="save11":
                        primary,optional=a2.unit(n,ix)
                        if len(primary)!=1:raise RuntimeError("save11_unit_primary_not_exact_one")
                        r["collateral_mint"],r["collateral_decimals"]=primary[0]
                        r["unit_resolution"]="PRIMARY_RESERVE_VAULT_TOKEN_BALANCE"
                        r["optional_unit_crosscheck_present"]=bool(optional)
                    rows[proto].append(r)
        if args.group=="marginfi":resolve_marginfi(rows["marginfi"],rpc,cfg["marginfi"],errors)
        if args.group=="save":resolve_save0c(rows["save0c"],rpc,cfg["save0c"],errors)
        for proto in members:
            unresolved=[r for r in rows[proto] if not r.get("collateral_mint")]
            if unresolved:errors.append({"reason":"unresolved_collateral_mint","protocol":proto,"count":len(unresolved)})
    except Exception as exc:
        errors.append({"reason":str(exc)[:300]})

    transport={"route":"A3A_GTFA_ADAPTIVE_PROGRAM_HISTORY","program":program,"rpc_calls":rpc.calls,
      "initial_window":{"start":start_iso,"end":end_iso},"leaf_count":len([x for x in ledger if x["phase"]=="full"]),
      "query_ledger":ledger,"transport_duplicate_signature_hits":transport_dups,
      "market_data_read":False,"economic_outcomes_opened":False,"trading_authority":"NONE"}

    any_block=False
    for proto in members:
        pr=blank_receipt(proto,start_iso,end_iso,transport)
        clean=[]
        for r in rows[proto]:
            x={k:v for k,v in r.items() if not k.startswith("_")}
            clean.append(x)
        clean.sort(key=lambda x:(x["timestamp"],x["signature"],json.dumps(x["instructionAddress"],separators=(",",":"))))
        proto_errors=list(errors)
        pr["rows"]=clean
        pr["successful_instruction_count"]=len(clean)
        pr["unique_collateral_mint_count"]=len({x["collateral_mint"] for x in clean})
        pr["sol_collateral_event_count"]=sum(x["collateral_mint"]==TARGET for x in clean)
        pr["error_count"]=len(proto_errors);pr["errors"]=proto_errors[:200]
        if proto_errors:
            pr["classification"]="PROTECTED_2025_PROTOCOL_SOURCE_BLOCKED";any_block=True
        path=outdir/f"{proto}-2025{args.month}.json"
        path.write_text(json.dumps(pr,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"protocol":proto,"month":args.month,"classification":pr["classification"],
          "successful_instruction_count":pr["successful_instruction_count"],
          "sol_collateral_event_count":pr["sol_collateral_event_count"],
          "error_count":pr["error_count"],"rpc_calls":rpc.calls,
          "adaptive_full_leaf_count":transport["leaf_count"]},sort_keys=True),flush=True)
    if any_block:raise SystemExit(2)

if __name__=="__main__":main()

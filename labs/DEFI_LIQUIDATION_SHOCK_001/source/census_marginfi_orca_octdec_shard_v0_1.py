#!/usr/bin/env python3
import argparse,base64,hashlib,json,struct,time,urllib.error,urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
RPC="https://api.mainnet-beta.solana.com"
MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
ORCA="whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
SOL="So11111111111111111111111111111111111111112"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}
DISC={
 bytes.fromhex("f8c69e91e17587c8"):"swap",
 bytes.fromhex("2b04ed0b1ac91e62"):"swap_v2",
 bytes.fromhex("c360ed6c44a2dbe6"):"two_hop_swap",
 bytes.fromhex("ba8fd11dfe02c275"):"two_hop_swap_v2",
}
POOL_DISC=bytes.fromhex("3f95d10ce1806309")

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--shard",type=int,required=True)
ap.add_argument("--workers",type=int,default=4)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
if not 0<=args.shard<16: raise SystemExit("shard must be 0..15")
SID=f"orca-{args.shard:02d}"
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/f"MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_{SID}_RECEIPT_V0.1.json"
ROWS=OUT/f"MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_{SID}_ROWS_V0.1.ndjson"

def addrkey(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])
def shard_of(r):return int(hashlib.sha256(ident(r).encode()).hexdigest(),16)%16

def b58d(s):
    n=0
    for ch in s:
        i=MAP.get(ch)
        if i is None:raise ValueError("invalid_base58")
        n=n*58+i
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def b58e(raw):
    n=int.from_bytes(raw,"big");out=""
    while n:
        n,r=divmod(n,58);out=ALPH[r]+out
    pad=0
    for b in raw:
        if b==0:pad+=1
        else:break
    return "1"*pad+(out or ("" if pad else "1"))

def data_candidates(s):
    if not isinstance(s,str) or not s:return []
    out=[]
    def add(kind,b):
        if b is not None and all(b!=x[1] for x in out):out.append((kind,b))
    t=s.strip()
    if t.startswith("0x"):
        try:add("hex0x",bytes.fromhex(t[2:]))
        except Exception:pass
    elif len(t)%2==0 and all(c in "0123456789abcdefABCDEF" for c in t):
        try:add("hex",bytes.fromhex(t))
        except Exception:pass
    try:add("base58",b58d(t))
    except Exception:pass
    try:add("base64",base64.b64decode(t,validate=True))
    except Exception:pass
    return out

def decode_orca_ix(ix):
    hits=[]
    for enc,b in data_candidates(ix.get("data")):
        if len(b)<8:continue
        typ=DISC.get(b[:8])
        if not typ:continue
        try:
            if typ in ("swap","swap_v2"):
                if len(b)<42:continue
                amount=struct.unpack("<Q",b[8:16])[0]
                amount_is_input=b[40];a_to_b=b[41]
                if amount_is_input not in (0,1) or a_to_b not in (0,1):continue
                hits.append({"encoding":enc,"type":typ,"amount":amount,
                             "amount_specified_is_input":bool(amount_is_input),
                             "a_to_b":bool(a_to_b)})
            else:
                if len(b)<59:continue
                amount=struct.unpack("<Q",b[8:16])[0]
                amount_is_input=b[24];a1=b[25];a2=b[26]
                if amount_is_input not in (0,1) or a1 not in (0,1) or a2 not in (0,1):continue
                hits.append({"encoding":enc,"type":typ,"amount":amount,
                             "amount_specified_is_input":bool(amount_is_input),
                             "a_to_b_one":bool(a1),"a_to_b_two":bool(a2)})
        except Exception:continue
    uniq=[]
    for h in hits:
        k=json.dumps(h,sort_keys=True)
        if all(json.dumps(x,sort_keys=True)!=k for x in uniq):uniq.append(h)
    return uniq[0] if len(uniq)==1 else None

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def req_slot(slot,retries=12):
    body={"type":"solana","fromBlock":int(slot),"toBlock":int(slot),
      "fields":{
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                       "instructionAddress":True,"isCommitted":True,"error":True}
      },
      "instructions":[{"programId":[MARGINFI,ORCA],"transaction":True}]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json","Content-Type":"application/json",
      "User-Agent":f"crypto-lab-marginfi-orca-octdec-{SID}/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(slot),int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(60,2**i));continue
            return int(slot),int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(60,2**i))
    raise RuntimeError(f"slot_{slot}_transport_exhausted:{last}")

def rpc_call(method,params,retries=12):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    last=None
    for i in range(retries):
        q=urllib.request.Request(RPC,data=payload,headers={
          "Content-Type":"application/json","User-Agent":f"crypto-lab-marginfi-orca-octdec-{SID}/0.1"},method="POST")
        try:
            with urllib.request.urlopen(q,timeout=60) as r:
                o=json.loads(r.read())
                if "error" in o:
                    last=o["error"];time.sleep(min(60,2**i));continue
                return o.get("result")
        except urllib.error.HTTPError as e:
            last={"http":e.code};time.sleep(min(60,2**i))
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(60,2**i))
    raise RuntimeError(f"rpc_exhausted:{last}")

def fetch_pool_mints(pools):
    out={};errs=[]
    pp=sorted(set(pools))
    for st in range(0,len(pp),40):
        batch=pp[st:st+40]
        try:res=rpc_call("getMultipleAccounts",[batch,{"encoding":"base64","commitment":"finalized"}])
        except Exception as e:
            errs.append({"batch_start":st,"error":type(e).__name__,"detail":str(e)[:300]});continue
        vals=(res or {}).get("value") if isinstance(res,dict) else None
        if not isinstance(vals,list) or len(vals)!=len(batch):
            errs.append({"batch_start":st,"reason":"rpc_schema_or_length"});continue
        for pk,v in zip(batch,vals):
            if not isinstance(v,dict):
                errs.append({"pool":pk,"reason":"account_missing"});continue
            if v.get("owner")!=ORCA:
                errs.append({"pool":pk,"reason":"owner_mismatch","owner":v.get("owner")});continue
            d=v.get("data")
            try:raw=base64.b64decode(d[0]) if isinstance(d,list) and d else b""
            except Exception:raw=b""
            if len(raw)<213 or raw[:8]!=POOL_DISC:
                errs.append({"pool":pk,"reason":"layout_or_discriminator_invalid","len":len(raw)});continue
            out[pk]={"mint_a":b58e(raw[101:133]),"mint_b":b58e(raw[181:213])}
    return out,errs

def blocked(stage,errors,**extra):
    rec={"schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-OCTDEC-SIGNED-FLOW-001",
         "classification":"MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_BLOCKED","shard_id":SID,
         "stage":stage,"errors":errors if isinstance(errors,list) else [str(errors)],
         "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
                     "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,
                     "market_2025_opened":False,"market_2026_opened":False,
                     "live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"merge_main":False,"post_decode_tuning":False},**extra}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    ROWS.write_text("")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

popfile=find_one(args.source_root,"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_V0.1.ndjson")
srfile=find_one(args.source_root,"MARGINFI_SOL_OCTDEC_POPULATION_RECEIPT_V0.1.json")
if popfile is None or srfile is None:blocked("authority","canonical_population_or_receipt_missing")
sr=json.loads(srfile.read_text())
if sr.get("classification")!="MARGINFI_SOL_OCTDEC_POPULATION_PASS":
    blocked("authority",f"source_not_pass:{sr.get('classification')}")
population=[json.loads(x) for x in popfile.read_text().splitlines() if x.strip()]
expected_count=int(sr.get("sol_population_count",-1))
if expected_count<=0 or len(population)!=expected_count:
    blocked("authority",f"canonical_population_count={len(population)} expected={expected_count}")
all_ids=[ident(r) for r in population]
if len(all_ids)!=len(set(all_ids)):blocked("authority","canonical_population_duplicate_identity")
assigned=[r for r in population if shard_of(r)==args.shard]
assigned.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
assigned_ids=[ident(r) for r in assigned]
if len(assigned_ids)!=len(set(assigned_ids)):blocked("shard_population","duplicate_assigned_identity")

slots=sorted({int(r["slot"]) for r in assigned})
slot_docs={};terr=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(req_slot,s):s for s in slots}
    for fut in as_completed(futs):
        s=futs[fut]
        try:
            sl,st,raw=fut.result()
            if st!=200:terr.append({"slot":sl,"http":st});continue
            slot_docs[sl]=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        except Exception as e:
            terr.append({"slot":s,"error":type(e).__name__,"detail":str(e)[:240]})
if terr:blocked("transaction_transport",terr[:200],assigned_count=len(assigned),unique_slot_count=len(slots))

prepared=[];legacy_pools=set();identity_conflicts=[]
for p in assigned:
    docs=slot_docs[int(p["slot"])];tx_matches=[];ins=[]
    for b in docs:
        for pos,tx in enumerate(b.get("transactions") or []):
            ti=tx.get("transactionIndex",tx.get("index",pos))
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs else None
            if sig==p["signature"] and ti==p.get("transactionIndex"):tx_matches.append((ti,tx))
        ins.extend(b.get("instructions") or [])
    if len(tx_matches)!=1:
        identity_conflicts.append({"identity":ident(p),"reason":"parent_match_count","count":len(tx_matches)});continue
    ti,tx=tx_matches[0]
    if tx.get("err") is not None:
        identity_conflicts.append({"identity":ident(p),"reason":"tx_not_successful"});continue
    txins=[x for x in ins if x.get("transactionIndex")==ti and x.get("isCommitted") is True and x.get("error") is None]
    canon=[x for x in txins if x.get("programId")==MARGINFI and x.get("instructionAddress")==p["instructionAddress"]]
    if len(canon)!=1:
        identity_conflicts.append({"identity":ident(p),"reason":"marginfi_match_count","count":len(canon)});continue
    after=[x for x in txins if x.get("programId")==ORCA and isinstance(x.get("instructionAddress"),list)
           and tuple(x["instructionAddress"])>tuple(p["instructionAddress"])]
    if not after:
        prepared.append({**p,"orca_after_count":0,"decoded":[],"decode_errors":[],"unsupported_orca_count":0})
        continue
    decoded=[];decode_errors=[];unsupported=0
    for x in sorted(after,key=lambda x:tuple(x["instructionAddress"])):
        d=decode_orca_ix(x)
        if d is None:
            known=False
            for _,raw in data_candidates(x.get("data")):
                if len(raw)>=8 and raw[:8] in DISC:known=True
            if known:decode_errors.append({"instructionAddress":x["instructionAddress"],"reason":"known_swap_decode_failure"})
            else:unsupported+=1
            continue
        ac=x.get("accounts") or []
        d["instructionAddress"]=x["instructionAddress"]
        if d["type"]=="swap":
            if len(ac)<11:decode_errors.append({"instructionAddress":x["instructionAddress"],"reason":"swap_accounts_lt_11"});continue
            d["pool"]=ac[2];legacy_pools.add(ac[2])
        elif d["type"]=="swap_v2":
            if len(ac)<15:decode_errors.append({"instructionAddress":x["instructionAddress"],"reason":"swap_v2_accounts_lt_15"});continue
            d["pool"]=ac[4];d["mint_a"]=ac[5];d["mint_b"]=ac[6]
        elif d["type"]=="two_hop_swap":
            if len(ac)<20:decode_errors.append({"instructionAddress":x["instructionAddress"],"reason":"two_hop_accounts_lt_20"});continue
            d["pool_one"]=ac[2];d["pool_two"]=ac[3];legacy_pools.add(ac[2]);legacy_pools.add(ac[3])
        else:
            if len(ac)<24:decode_errors.append({"instructionAddress":x["instructionAddress"],"reason":"two_hop_v2_accounts_lt_24"});continue
            d["pool_one"]=ac[0];d["pool_two"]=ac[1];d["mint_input"]=ac[2];d["mint_intermediate"]=ac[3];d["mint_output"]=ac[4]
        decoded.append(d)
    prepared.append({**p,"orca_after_count":len(after),"unsupported_orca_count":unsupported,
                     "decode_errors":decode_errors,"decoded":decoded})

if identity_conflicts:blocked("identity",identity_conflicts[:200],assigned_count=len(assigned))

pool_mints,pool_errors=fetch_pool_mints(legacy_pools)

rows=[];types=Counter();reasons=Counter();semantics=Counter()
for p in prepared:
    rr={k:p.get(k) for k in ("signature","slot","timestamp","transactionIndex","instructionAddress",
                              "asset_bank","liab_bank","asset_mint","liab_mint")}
    rr["shard_id"]=SID;rr["orca_after_count"]=p["orca_after_count"]
    rr["unsupported_orca_count"]=p["unsupported_orca_count"]
    if p["orca_after_count"]==0:
        rr["classification"]="NOT_ORCA_ROUTE";rows.append(rr);continue
    rr["classification"]="SOURCE_EVIDENCE_INCOMPLETE"
    rr["decoded_swap_count"]=len(p["decoded"]);rr["decode_errors"]=p["decode_errors"]
    if p["decode_errors"]:
        rr["reason"]="known_swap_decode_error";reasons[rr["reason"]]+=1;rows.append(rr);continue
    if not p["decoded"]:
        rr["reason"]="no_supported_orca_swap";reasons[rr["reason"]]+=1;rows.append(rr);continue
    route=[];failed=None
    for d in p["decoded"]:
        typ=d["type"];types[typ]+=1
        if typ=="swap":
            pm=pool_mints.get(d["pool"])
            if not pm:failed="legacy_pool_state_unavailable";break
            ma,mb=pm["mint_a"],pm["mint_b"]
            inp=ma if d["a_to_b"] else mb;out=mb if d["a_to_b"] else ma
        elif typ=="swap_v2":
            ma,mb=d["mint_a"],d["mint_b"]
            inp=ma if d["a_to_b"] else mb;out=mb if d["a_to_b"] else ma
        elif typ=="two_hop_swap":
            p1=pool_mints.get(d["pool_one"]);p2=pool_mints.get(d["pool_two"])
            if not p1 or not p2:failed="legacy_pool_state_unavailable";break
            in1=p1["mint_a"] if d["a_to_b_one"] else p1["mint_b"]
            out1=p1["mint_b"] if d["a_to_b_one"] else p1["mint_a"]
            in2=p2["mint_a"] if d["a_to_b_two"] else p2["mint_b"]
            out2=p2["mint_b"] if d["a_to_b_two"] else p2["mint_a"]
            if out1!=in2:failed="two_hop_mint_chain_mismatch";break
            inp,out=in1,out2
        else:
            inp=d["mint_input"];out=d["mint_output"]
        route.append({"instructionAddress":d["instructionAddress"],"type":typ,
                      "input_mint":inp,"output_mint":out,
                      "amount_specified_is_input":d["amount_specified_is_input"],
                      "amount_argument":d["amount"],
                      "exact_input_amount":d["amount"] if d["amount_specified_is_input"] else None})
    if failed:
        rr["reason"]=failed;reasons[failed]+=1;rows.append(rr);continue
    pairs=[(x["input_mint"],x["output_mint"]) for x in route]
    if len(set(pairs))!=len(pairs):
        rr["reason"]="duplicate_swap_pair";reasons[rr["reason"]]+=1;rows.append(rr);continue
    if not all(route[i]["output_mint"]==route[i+1]["input_mint"] for i in range(len(route)-1)):
        rr["reason"]="multi_swap_chain_mismatch";reasons[rr["reason"]]+=1;rows.append(rr);continue
    mints=[route[0]["input_mint"]]+[x["output_mint"] for x in route]
    if len(set(mints))!=len(mints):
        rr["reason"]="cycle_or_repeated_mint";reasons[rr["reason"]]+=1;rows.append(rr);continue
    I=route[0]["input_mint"];O=route[-1]["output_mint"]
    rr["decoded_route"]=route;rr["route_input_mint"]=I;rr["route_output_mint"]=O
    rr["exact_route_input_amount"]=route[0]["exact_input_amount"]
    if I==p["asset_mint"] and O==p["liab_mint"]:
        rr.update(classification="DIRECTION_PROVEN",route_semantic="COLLATERAL_TO_LIABILITY_ORCA_PROVEN",
                  asset_label="SIGNED_SELL_PRESSURE_PROVEN",liability_label="SIGNED_BUY_PRESSURE_PROVEN")
        semantics[rr["route_semantic"]]+=1
    elif I==p["liab_mint"] and O==p["asset_mint"]:
        rr.update(classification="DIRECTION_PROVEN",route_semantic="LIABILITY_TO_COLLATERAL_ORCA_PROVEN",
                  liability_label="SIGNED_SELL_PRESSURE_PROVEN",asset_label="SIGNED_BUY_PRESSURE_PROVEN")
        semantics[rr["route_semantic"]]+=1
    else:
        rr.update(classification="DIRECTION_AMBIGUOUS",reason="route_endpoints_not_equal_marginfi_pair")
        reasons[rr["reason"]]+=1
    rows.append(rr)

row_ids=[ident(r) for r in rows]
if len(rows)!=len(assigned) or len(row_ids)!=len(set(row_ids)):
    blocked("adjudication_integrity",["row_count_or_duplicate_mismatch"],assigned_count=len(assigned),row_count=len(rows))

with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

presence=sum(1 for r in rows if r.get("classification")!="NOT_ORCA_ROUTE")
I=sum(1 for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in rows if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in rows if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in rows if r.get("classification")=="CONTRADICTION")
exact=sum(1 for r in rows if r.get("classification")=="DIRECTION_PROVEN" and r.get("exact_route_input_amount") is not None)
rec={"schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-OCTDEC-SIGNED-FLOW-001",
 "classification":"MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_PASS","shard_id":SID,
 "authority":"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "canonical_population_count":len(population),"assigned_count":len(assigned),"adjudication_count":len(rows),
 "unique_slot_count":len(slots),"not_orca_route_count":len(rows)-presence,"orca_presence_count":presence,
 "source_evidence_incomplete":I,"direction_proven":D,"direction_ambiguous":A,"contradictions":C,
 "exact_input_amount_proven":exact,"instruction_type_counts":dict(types),
 "route_semantic_counts":dict(semantics),"incomplete_reason_counts":dict(reasons),
 "legacy_pool_count":len(legacy_pools),"legacy_pool_resolved_count":len(pool_mints),
 "legacy_pool_error_count":len(pool_errors),"legacy_pool_errors":pool_errors[:100],
 "rows_file":str(ROWS),"rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False,"post_decode_tuning":False}}
RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))

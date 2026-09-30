#!/usr/bin/env python3
import argparse,base64,hashlib,json,struct,time,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
MARGINFI_D8=bytes.fromhex("d6a997d5fba756db")
JUPITER="JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
SOL="So11111111111111111111111111111111111111112"
SWAP_DISC=hashlib.sha256(b"event:SwapEvent").digest()[:8]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

ap=argparse.ArgumentParser()
ap.add_argument("--field-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--month",choices=["202404","202405","202406"],required=True)
ap.add_argument("--workers",type=int,default=24)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
M=args.month
RECEIPT=OUT/f"MARGINFI_SOL_APRJUN_SOURCE_{M}_RECEIPT_V0.2.json"
ROWS=OUT/f"MARGINFI_SOL_APRJUN_SOURCE_{M}_ROWS_V0.2.ndjson"
POP=OUT/f"MARGINFI_SOL_APRJUN_POPULATION_{M}_V0.2.ndjson"

EXPECTED={
 "202404":{"partition_id":"marginfi-202404","start":"2024-04-01T00:00:00Z","end":"2024-05-01T00:00:00Z",
           "enriched":11738},
 "202405":{"partition_id":"marginfi-202405","start":"2024-05-01T00:00:00Z","end":"2024-06-01T00:00:00Z",
           "enriched":9197},
 "202406":{"partition_id":"marginfi-202406","start":"2024-06-01T00:00:00Z","end":"2024-07-01T00:00:00Z",
           "enriched":6215},
}[M]

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(sig,addr):return sig+"|"+addrkey(addr)

def b58d(s):
    n=0
    for ch in s:
        i=MAP.get(ch)
        if i is None:raise ValueError("invalid_base58")
        n=n*58+i
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def pk58(raw):
    n=int.from_bytes(raw,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for b in raw:
        if b==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

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

def decode_swap_event(data):
    valid=[]
    for enc,b in data_candidates(data):
        if len(b)<8+8+32+32+8+32+8:continue
        event=b[8:]
        if event[:8]!=SWAP_DISC:continue
        p=8
        amm=pk58(event[p:p+32]);p+=32
        inp=pk58(event[p:p+32]);p+=32
        ina=struct.unpack("<Q",event[p:p+8])[0];p+=8
        outm=pk58(event[p:p+32]);p+=32
        outa=struct.unpack("<Q",event[p:p+8])[0]
        valid.append({"encoding":enc,"amm":amm,"inputMint":inp,"inputAmount":ina,
                      "outputMint":outm,"outputAmount":outa})
    uniq=[]
    for x in valid:
        k=(x["amm"],x["inputMint"],x["inputAmount"],x["outputMint"],x["outputAmount"])
        if all((y["amm"],y["inputMint"],y["inputAmount"],y["outputMint"],y["outputAmount"])!=k for y in uniq):
            uniq.append(x)
    return uniq[0] if len(uniq)==1 else None

def find_json(root,predicate):
    hits=[]
    for p in Path(root).rglob("*.json"):
        try:o=json.loads(p.read_text())
        except Exception:continue
        if predicate(o):hits.append((p,o))
    return hits

def req_slot(slot,retries=9):
    body={"type":"solana","fromBlock":slot,"toBlock":slot,
      "fields":{
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "instruction":{"programId":True,"data":True,"transactionIndex":True,
                       "instructionAddress":True,"isCommitted":True,"error":True}
      },
      "instructions":[
        {"programId":[MARGINFI],"transaction":True},
        {"programId":[JUPITER],"transaction":True}
      ]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json","Content-Type":"application/json",
      "User-Agent":f"crypto-lab-marginfi-sol-source-{M}/0.2"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=90) as r:return slot,int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(30,2**i));continue
            return slot,int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(30,2**i))
    raise RuntimeError(f"slot_{slot}_transport_exhausted:{last}")

def blocked(stage,errors,**extra):
    rec={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"MARGINFI_SOL_APRJUN_SOURCE_MONTH_BLOCKED","month":M,"stage":stage,
      "errors":errors if isinstance(errors,list) else [str(errors)],
      "firewall":{"prices":False,"returns":False,"pnl":False,"apr_jun_market_outcomes_opened":False,
                  "apr_jun_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
                  "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False},
      **extra}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    ROWS.write_text("");POP.write_text("")
    print(json.dumps(rec,indent=2,sort_keys=True))
    raise SystemExit(2)

field_hits=find_json(args.field_root,lambda o:o.get("partition_id")==EXPECTED["partition_id"])
bank_hits=find_json(args.bank_registry_root,lambda o:o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS")
if len(field_hits)!=1 or len(bank_hits)!=1:
    blocked("authority",[f"field_hit_count={len(field_hits)}",f"bank_hit_count={len(bank_hits)}"])
fp,field=field_hits[0];bp,bank=bank_hits[0]
authority_errors=[]
if field.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":authority_errors.append("field_partition_not_pass")
if field.get("protocol")!="marginfi" or field.get("instruction_class")!="lending_account_liquidate":authority_errors.append("field_identity_mismatch")
if field.get("effective_start")!=EXPECTED["start"] or field.get("effective_end")!=EXPECTED["end"]:authority_errors.append("field_window_mismatch")
if int(field.get("baseline_success_count",-1))!=EXPECTED["enriched"] or int(field.get("enriched_success_count",-1))!=EXPECTED["enriched"]:
    authority_errors.append("field_population_count_mismatch")
for k in ("missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"):
    if int(field.get(k,-1))!=0:authority_errors.append(k+"_nonzero")
registry={x["bank"]:x["mint"] for x in bank.get("bank_registry") or []}
solbanks={b for b,m in registry.items() if m==SOL}
if not solbanks:authority_errors.append("no_sol_bank_mapping")
if authority_errors:blocked("authority",authority_errors)

population=[]
for r in field.get("enriched_rows") or []:
    sem=r.get("semantic_accounts") or {}
    if sem.get("asset_bank") not in solbanks:continue
    population.append({
      "signature":r["signature"],"slot":r["slot"],"timestamp":r["timestamp"],
      "transactionIndex":r.get("transactionIndex"),"instructionAddress":r["instructionAddress"],
      "asset_bank":sem.get("asset_bank"),"liab_bank":sem.get("liab_bank"),
      "asset_mint":SOL,"liab_mint":registry.get(sem.get("liab_bank"))
    })
population.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
ids=[ident(r["signature"],r["instructionAddress"]) for r in population]
if len(ids)!=len(set(ids)):blocked("population","duplicate_sol_population_identity")
with POP.open("w") as fh:
    for r in population:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

slots=sorted({int(r["slot"]) for r in population})
slot_docs={};fails=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(req_slot,s):s for s in slots}
    for fut in as_completed(futs):
        s=futs[fut]
        try:
            slot,st,raw=fut.result()
            if st!=200:fails.append({"slot":slot,"http":st});continue
            slot_docs[slot]=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        except Exception as e:
            fails.append({"slot":s,"error":type(e).__name__,"detail":str(e)[:240]})
if fails:blocked("exact_slot_transport",fails[:200],population_count=len(population),unique_slot_count=len(slots))

members=[];structural=[]
for p in population:
    docs=slot_docs[int(p["slot"])]
    txs=[];ins=[]
    for b in docs:
        for pos,tx in enumerate(b.get("transactions") or []):
            ti=tx.get("transactionIndex",tx.get("index",pos))
            sig=(tx.get("signatures") or [None])[0]
            if sig==p["signature"] and ti==p["transactionIndex"] and tx.get("err") is None:
                txs.append((ti,tx))
        ins.extend(b.get("instructions") or [])
    if len(txs)!=1:
        structural.append({"reason":"parent_tx_match_count","identity":ident(p["signature"],p["instructionAddress"]),"count":len(txs)})
        continue
    txi=p["transactionIndex"]
    txins=[x for x in ins if x.get("transactionIndex")==txi and x.get("isCommitted") is True and x.get("error") is None]
    canon=[]
    for x in txins:
        if x.get("programId")!=MARGINFI or x.get("instructionAddress")!=p["instructionAddress"]:continue
        try:d=b58d(x.get("data") or "")
        except Exception:continue
        if d.startswith(MARGINFI_D8):canon.append(x)
    if len(canon)!=1:
        structural.append({"reason":"canonical_marginfi_match_count","identity":ident(p["signature"],p["instructionAddress"]),"count":len(canon)})
        continue

    after=[x for x in txins if x.get("programId")==JUPITER and isinstance(x.get("instructionAddress"),list)
           and tuple(x["instructionAddress"])>tuple(p["instructionAddress"])]
    if not after:continue

    rr={**p,"classification":"SOURCE_EVIDENCE_INCOMPLETE",
        "class_id":"MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_V0_1","jupiter_after_count":len(after)}
    if not rr.get("liab_mint") or rr["liab_mint"]==SOL:
        rr["reason"]="liability_bank_mint_missing_or_same_as_sol";members.append(rr);continue
    roots=[]
    for a in sorted([x["instructionAddress"] for x in after],key=lambda x:(len(x),tuple(x))):
        if not any(len(root)<len(a) and a[:len(root)]==root for root in roots):roots.append(a)
    rr["jupiter_route_roots"]=roots
    if len(roots)!=1:
        rr["reason"]="jupiter_route_root_count_"+str(len(roots));members.append(rr);continue
    root=roots[0]
    events=[]
    for x in after:
        a=x["instructionAddress"]
        if not(len(a)>len(root) and a[:len(root)]==root):continue
        ev=decode_swap_event(x.get("data"))
        if ev is not None:events.append({"instructionAddress":a,**ev})
    events.sort(key=lambda x:tuple(x["instructionAddress"]))
    rr["decoded_swap_event_count"]=len(events);rr["decoded_swap_events"]=events
    if not events:
        rr["reason"]="swap_event_count_0";members.append(rr);continue
    if any(e["inputAmount"]<=0 or e["outputAmount"]<=0 or e["inputMint"]==e["outputMint"] for e in events):
        rr["reason"]="invalid_realized_swap_fields";members.append(rr);continue
    pairs=[(e["inputMint"],e["outputMint"]) for e in events]
    if len(set(pairs))!=len(pairs):
        rr["reason"]="duplicate_swap_pair";members.append(rr);continue
    if not all(events[i]["outputMint"]==events[i+1]["inputMint"] for i in range(len(events)-1)):
        rr["reason"]="non_chain_multi_event_route";members.append(rr);continue
    mints=[events[0]["inputMint"]]+[e["outputMint"] for e in events]
    if len(set(mints))!=len(mints):
        rr["reason"]="cycle_or_repeated_mint";members.append(rr);continue
    I=events[0]["inputMint"];O=events[-1]["outputMint"];L=rr["liab_mint"]
    rr["route_input_mint"]=I;rr["route_output_mint"]=O;rr["hop_count"]=len(events)
    if I==SOL and O==L:
        rr.update(classification="DIRECTION_PROVEN",route_semantic="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN",
                  asset_label="SIGNED_SELL_PRESSURE_PROVEN",liability_label="SIGNED_BUY_PRESSURE_PROVEN")
    elif I==L and O==SOL:
        rr.update(classification="DIRECTION_PROVEN",route_semantic="LIABILITY_TO_COLLATERAL_MULTI_HOP_PROVEN",
                  liability_label="SIGNED_SELL_PRESSURE_PROVEN",asset_label="SIGNED_BUY_PRESSURE_PROVEN")
    else:
        rr.update(classification="DIRECTION_AMBIGUOUS",reason="route_endpoints_not_equal_sol_liability_pair")
    members.append(rr)

if structural:
    blocked("source_identity",structural[:200],population_count=len(population),route_member_count=len(members))
members.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
with ROWS.open("w") as fh:
    for r in members:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

I=sum(1 for r in members if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in members if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in members if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in members if r.get("classification")=="CONTRADICTION")
complete=len(members)-I
rec={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"MARGINFI_SOL_APRJUN_SOURCE_MONTH_COMPLETE","month":M,
 "authority":"MARGINFI_SOL_FLOW_MAGNITUDE_REVERSION_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "field_partition":{"partition_id":field.get("partition_id"),"classification":field.get("classification"),
                    "baseline_success_count":field.get("baseline_success_count"),
                    "enriched_success_count":field.get("enriched_success_count")},
 "sol_bank_count":len(solbanks),"sol_population_count":len(population),"unique_slot_count":len(slots),
 "route_member_count":len(members),"not_route_count":len(population)-len(members),
 "source_evidence_incomplete":I,"source_complete_count":complete,
 "source_complete_rate":complete/len(members) if members else 0.0,
 "direction_proven":D,"direction_ambiguous":A,"contradictions":C,
 "direction_rate_complete":D/complete if complete else 0.0,
 "population_file":str(POP),"rows_file":str(ROWS),
 "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
 "rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"apr_jun_market_outcomes_opened":False,
             "apr_jun_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))

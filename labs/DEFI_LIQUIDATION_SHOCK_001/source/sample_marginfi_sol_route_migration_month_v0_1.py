#!/usr/bin/env python3
import argparse,hashlib,json,time,urllib.error,urllib.request
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
SOL="So11111111111111111111111111111111111111112"
N=128

EXPECTED={
 "202407":{"partition_id":"marginfi-202407","start":"2024-07-01T00:00:00Z","end":"2024-08-01T00:00:00Z","count":4907},
 "202408":{"partition_id":"marginfi-202408","start":"2024-08-01T00:00:00Z","end":"2024-09-01T00:00:00Z","count":13056},
 "202409":{"partition_id":"marginfi-202409","start":"2024-09-01T00:00:00Z","end":"2024-10-01T00:00:00Z","count":1558},
}

ap=argparse.ArgumentParser()
ap.add_argument("--field-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--month",choices=sorted(EXPECTED),required=True)
ap.add_argument("--workers",type=int,default=4)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
M=args.month;E=EXPECTED[M]
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/f"MARGINFI_SOL_ROUTE_MIGRATION_{M}_RECEIPT_V0.1.json"

def addrkey(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])
def rank(r):return hashlib.sha256(ident(r).encode()).hexdigest()

def find_json(root,pred):
    hits=[]
    for p in Path(root).rglob("*.json"):
        try:o=json.loads(p.read_text())
        except Exception:continue
        if pred(o):hits.append((p,o))
    return hits

def req_slot(slot,retries=12):
    body={"type":"solana","fromBlock":int(slot),"toBlock":int(slot),
      "fields":{
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "instruction":{"programId":True,"transactionIndex":True,"instructionAddress":True,
                       "isCommitted":True,"error":True}
      },
      "instructions":[{"transaction":True}]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json","Content-Type":"application/json",
      "User-Agent":f"crypto-lab-marginfi-route-migration-{M}/0.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(slot),int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":int(e.code)};time.sleep(min(60,2**i));continue
            return int(slot),int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(60,2**i))
    raise RuntimeError(f"slot_{slot}_transport_exhausted:{last}")

def blocked(stage,errors,**extra):
    rec={"schema_version":"0.1","classification":"MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_BLOCKED",
         "month":M,"stage":stage,"errors":errors if isinstance(errors,list) else [str(errors)],
         "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
                     "market_2024_outcomes_opened":False,"market_2025_opened":False,
                     "market_2026_opened":False,"live_trading":False,"orders":False,
                     "exchange_mutation":False,"merge_main":False},**extra}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

fh=find_json(args.field_root,lambda o:o.get("partition_id")==E["partition_id"])
bh=find_json(args.bank_registry_root,lambda o:o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS")
errs=[]
if len(fh)!=1:errs.append(f"field_hit_count:{len(fh)}")
if len(bh)!=1:errs.append(f"bank_hit_count:{len(bh)}")
if errs:blocked("authority",errs)
field=fh[0][1];bank=bh[0][1]
if field.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":errs.append("field_not_pass")
if field.get("protocol")!="marginfi" or field.get("instruction_class")!="lending_account_liquidate":errs.append("field_identity_mismatch")
if field.get("effective_start")!=E["start"] or field.get("effective_end")!=E["end"]:errs.append("field_window_mismatch")
if int(field.get("baseline_success_count",-1))!=E["count"] or int(field.get("enriched_success_count",-1))!=E["count"]:errs.append("field_count_mismatch")
for k in ("missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"):
    if int(field.get(k,-1))!=0:errs.append(k+"_nonzero")
registry={x["bank"]:x["mint"] for x in bank.get("bank_registry") or []}
solbanks={b for b,m in registry.items() if m==SOL}
if not solbanks:errs.append("no_sol_bank")
if errs:blocked("authority",errs)

pop=[]
for r in field.get("enriched_rows") or []:
    sem=r.get("semantic_accounts") or {}
    if sem.get("asset_bank") not in solbanks:continue
    pop.append({
      "signature":r["signature"],"slot":int(r["slot"]),"timestamp":r["timestamp"],
      "transactionIndex":r.get("transactionIndex"),"instructionAddress":r["instructionAddress"],
      "asset_bank":sem.get("asset_bank"),"liab_bank":sem.get("liab_bank")
    })
ids=[ident(r) for r in pop]
if len(ids)!=len(set(ids)):blocked("population","duplicate_sol_identity")
sample=sorted(pop,key=lambda r:(rank(r),r["signature"],addrkey(r["instructionAddress"])))[:min(N,len(pop))]
if len(sample)!=min(N,len(pop)):blocked("sample","sample_size_mismatch")

slots=sorted({r["slot"] for r in sample});slot_docs={};transport=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(req_slot,s):s for s in slots}
    for fut in as_completed(futs):
        s=futs[fut]
        try:
            slot,st,raw=fut.result()
            if st!=200:
                transport.append({"slot":slot,"http":st});continue
            slot_docs[slot]=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        except Exception as e:
            transport.append({"slot":s,"error":type(e).__name__,"detail":str(e)[:240]})
if transport:blocked("transport",transport[:200],sample_count=len(sample),unique_slot_count=len(slots))

results=[];all_after_instr=Counter();after_tx_presence=Counter();all_program=Counter();seqs=Counter()
identity_conflicts=0;incomplete=0;zero_after=0
for idx,e in enumerate(sample,1):
    docs=slot_docs[e["slot"]];tx_matches=[];ins=[]
    for b in docs:
        for pos,tx in enumerate(b.get("transactions") or []):
            ti=tx.get("transactionIndex",tx.get("index",pos))
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs else None
            if sig==e["signature"]:tx_matches.append((ti,tx))
        ins.extend(b.get("instructions") or [])
    rr={"sample_index":idx,"rank":rank(e),"signature":e["signature"],"slot":e["slot"],
        "timestamp":e["timestamp"],"instructionAddress":e["instructionAddress"],
        "classification":"SOURCE_EVIDENCE_INCOMPLETE","instructions":[]}
    if len(tx_matches)!=1:
        rr["identity_error"]="parent_transaction_match_count_"+str(len(tx_matches));identity_conflicts+=1;incomplete+=1;results.append(rr);continue
    ti,tx=tx_matches[0]
    if tx.get("err") is not None:
        rr["identity_error"]="canonical_transaction_not_successful";identity_conflicts+=1;incomplete+=1;results.append(rr);continue
    txins=[x for x in ins if x.get("transactionIndex")==ti and x.get("isCommitted") is True and x.get("error") is None]
    exact=[x for x in txins if x.get("programId")==MARGINFI and x.get("instructionAddress")==e["instructionAddress"]]
    if len(exact)!=1:
        rr["identity_error"]="canonical_instruction_match_count_"+str(len(exact));identity_conflicts+=1;incomplete+=1;results.append(rr);continue
    ca=e["instructionAddress"];ordered=sorted(txins,key=lambda x:tuple(x.get("instructionAddress") or []))
    after_unique=set()
    for x in ordered:
        addr=x.get("instructionAddress") or []
        rel="AT" if addr==ca else ("BEFORE" if tuple(addr)<tuple(ca) else "AFTER")
        pid=x.get("programId")
        rr["instructions"].append({"programId":pid,"instructionAddress":addr,"relation":rel})
        if pid:all_program[pid]+=1
        if rel=="AFTER" and pid:
            all_after_instr[pid]+=1;after_unique.add(pid)
    for pid in after_unique:after_tx_presence[pid]+=1
    if not after_unique:zero_after+=1
    seq=">".join((x.get("programId") or "NULL") for x in ordered)
    seqs[seq]+=1
    rr["after_unique_programs"]=sorted(after_unique)
    rr["after_instruction_count"]=sum(1 for x in rr["instructions"] if x["relation"]=="AFTER")
    rr["classification"]="SAME_TX_INSTRUCTION_CENSUS_COMPLETE"
    results.append(rr)

complete=sum(1 for r in results if r["classification"]=="SAME_TX_INSTRUCTION_CENSUS_COMPLETE")
classification="MARGINFI_SOL_ROUTE_MIGRATION_MONTH_PASS" if complete==len(sample) and identity_conflicts==0 and incomplete==0 else "MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DLS-MARGINFI-SOL-ROUTE-MIGRATION-001",
 "classification":classification,"authority":"MARGINFI_SOL_ROUTE_MIGRATION_V0_1_SOURCE_FREEZE_2026-09-30.md",
 "month":M,"population_count":len(pop),"sample_count":len(sample),"complete_count":complete,
 "identity_conflict_count":identity_conflicts,"source_evidence_incomplete":incomplete,
 "unique_slot_count":len(slots),"zero_after_transaction_count":zero_after,
 "after_program_instruction_frequency":[{"programId":p,"count":n} for p,n in all_after_instr.most_common()],
 "after_program_transaction_presence":[{"programId":p,"count":n,"share":n/len(sample)} for p,n in after_tx_presence.most_common()],
 "all_program_instruction_frequency":[{"programId":p,"count":n} for p,n in all_program.most_common()],
 "ordered_program_sequence_frequency":[{"sequence":s,"count":n} for s,n in seqs.most_common()],
 "results":results,"program_semantics_labeled":False,
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "market_2024_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"month":M,"population_count":len(pop),"sample_count":len(sample),
 "complete_count":complete,"identity_conflicts":identity_conflicts,"zero_after":zero_after,
 "top_after_presence":receipt["after_program_transaction_presence"][:15]},indent=2))
if classification!="MARGINFI_SOL_ROUTE_MIGRATION_MONTH_PASS":raise SystemExit(2)

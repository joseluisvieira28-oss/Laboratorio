#!/usr/bin/env python3
import argparse,base64,hashlib,json,struct,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
JUPITER="JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
SWAP_DISC=hashlib.sha256(b"event:SwapEvent").digest()[:8]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

ap=argparse.ArgumentParser()
ap.add_argument("--members-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--shard-index",required=True,type=int)
ap.add_argument("--shard-count",default=16,type=int)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
if args.shard_count != 16 or not (0 <= args.shard_index < args.shard_count):
    raise SystemExit("invalid frozen shard configuration")
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
TAG=f"{args.shard_index:02d}"
RECEIPT=OUT/f"MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_{TAG}_RECEIPT_V0.2.json"
ROWS=OUT/f"MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_{TAG}_ROWS_V0.2.ndjson"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def rank(x):return hashlib.sha256((x["signature"]+"|"+addrkey(x["instructionAddress"])).encode()).hexdigest()

def b58d(s):
    n=0
    for c in s:
        i=ALPH.find(c)
        if i<0:raise ValueError("not_base58")
        n=n*58+i
    h=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    pad=0
    for c in s:
        if c=="1":pad+=1
        else:break
    return b"\x00"*pad+h

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
        valid.append({"encoding":enc,"amm":amm,"inputMint":inp,"inputAmount":ina,"outputMint":outm,"outputAmount":outa})
    uniq=[]
    for x in valid:
        k=(x["amm"],x["inputMint"],x["inputAmount"],x["outputMint"],x["outputAmount"])
        if all((y["amm"],y["inputMint"],y["inputAmount"],y["outputMint"],y["outputAmount"])!=k for y in uniq):uniq.append(x)
    return uniq[0] if len(uniq)==1 else None

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def req(slot,retries=8):
    body={"type":"solana","fromBlock":slot,"toBlock":slot,
      "fields":{
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "instruction":{"programId":True,"transactionIndex":True,"instructionAddress":True,
                       "isCommitted":True,"error":True,"data":True}
      },
      "instructions":[{"transaction":True}]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json","Content-Type":"application/json",
      "User-Agent":"crypto-lab-marginfi-jupiter-multihop-cal/0.2"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(45,2**i));continue
            return int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

mrec=find_one(args.members_root,"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_RECEIPT_V0.2.json")
mfile=find_one(args.members_root,"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERS_V0.2.ndjson")
brec=find_one(args.bank_registry_root,"MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json")
crec=find_one(args.calibration_root,"MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_RECEIPT_V0.2.json")
errors=[]
if mrec is None or mfile is None:errors.append("membership_artifact_incomplete")
if brec is None:errors.append("bank_registry_receipt_missing")
if crec is None:errors.append("calibration_receipt_missing")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_BLOCKED","errors":errors},indent=2)+"\n")
    raise SystemExit(2)

mr=json.loads(mrec.read_text());br=json.loads(brec.read_text());cr=json.loads(crec.read_text())
if mr.get("classification")!="MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS":errors.append("membership_not_pass")
if br.get("classification")!="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS":errors.append("bank_registry_not_pass")
if cr.get("classification")!="MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_PASS":errors.append("calibration_not_pass")
registry={x["bank"]:x["mint"] for x in br.get("bank_registry") or []}
all_members=[json.loads(x) for x in mfile.read_text().splitlines() if x.strip()]
if len(all_members)!=int(mr.get("member_count",-1)):errors.append("member_count_mismatch")
ranked=sorted(all_members,key=lambda x:(rank(x),x["signature"],addrkey(x["instructionAddress"])))
sample=[x for x in ranked if int(rank(x)[:16],16)%args.shard_count==args.shard_index]
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_BLOCKED","errors":errors},indent=2)+"\n")
    raise SystemExit(2)

rows=[]
for i,e in enumerate(sample,1):
    sem=e.get("semantic_accounts") or {}
    A=registry.get(sem.get("asset_bank"));L=registry.get(sem.get("liab_bank"))
    rr={"shard_index":args.shard_index,"shard_row_index":i,"rank":rank(e),"signature":e["signature"],"slot":e["slot"],
        "instructionAddress":e["instructionAddress"],"asset_bank":sem.get("asset_bank"),"liab_bank":sem.get("liab_bank"),
        "asset_mint":A,"liab_mint":L,"classification":"SOURCE_EVIDENCE_INCOMPLETE"}
    if not A or not L or A==L:
        rr["reason"]="bank_mint_mapping_missing_or_same";rows.append(rr);continue
    try:st,raw=req(int(e["slot"]))
    except Exception as ex:
        rr["reason"]="transport_exhausted";rr["detail"]=str(ex)[:240];rows.append(rr);continue
    if st!=200:
        rr["reason"]="transport_http_"+str(st);rows.append(rr);continue

    txi=None;txerr=None;ins=[]
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip():continue
        b=json.loads(line)
        for pos,tx in enumerate(b.get("transactions") or []):
            sig=(tx.get("signatures") or [None])[0]
            if sig==e["signature"]:
                cur=tx.get("transactionIndex",tx.get("index",pos))
                if txi is not None and txi!=cur:rr["reason"]="signature_multiple_transaction_indices"
                txi=cur;txerr=tx.get("err")
        ins.extend(b.get("instructions") or [])
    if txi is None or txerr is not None:
        rr["reason"]="exact_success_transaction_not_found";rows.append(rr);continue

    txins=[x for x in ins if x.get("transactionIndex")==txi and x.get("isCommitted") is True and x.get("error") is None]
    canon=[x for x in txins if x.get("instructionAddress")==e["instructionAddress"]]
    if len(canon)!=1:
        rr["reason"]="canonical_instruction_match_count_"+str(len(canon));rows.append(rr);continue

    jaddrs=[x.get("instructionAddress") for x in txins if x.get("programId")==JUPITER and isinstance(x.get("instructionAddress"),list)
            and tuple(x.get("instructionAddress"))>tuple(e["instructionAddress"])]
    roots=[]
    for a in sorted(jaddrs,key=lambda x:(len(x),tuple(x))):
        if not any(len(r)<len(a) and a[:len(r)]==r for r in roots):roots.append(a)
    rr["jupiter_route_roots"]=roots
    if len(roots)!=1:
        rr["reason"]="jupiter_route_root_count_"+str(len(roots));rows.append(rr);continue
    root=roots[0]

    events=[]
    for x in txins:
        if x.get("programId")!=JUPITER or not isinstance(x.get("instructionAddress"),list):continue
        a=x["instructionAddress"]
        if not(len(a)>len(root) and a[:len(root)]==root):continue
        ev=decode_swap_event(x.get("data"))
        if ev is not None:events.append({"instructionAddress":a,**ev})
    events.sort(key=lambda x:tuple(x["instructionAddress"]))
    rr["decoded_swap_event_count"]=len(events);rr["decoded_swap_events"]=events
    if not events:
        rr["reason"]="swap_event_count_0";rows.append(rr);continue
    if any(ev["inputAmount"]<=0 or ev["outputAmount"]<=0 or ev["inputMint"]==ev["outputMint"] for ev in events):
        rr["reason"]="invalid_realized_swap_fields";rows.append(rr);continue

    pairs=[(ev["inputMint"],ev["outputMint"]) for ev in events]
    if len(set(pairs))!=len(pairs):
        rr["reason"]="duplicate_swap_pair";rows.append(rr);continue

    chain_ok=all(events[k]["outputMint"]==events[k+1]["inputMint"] for k in range(len(events)-1))
    if not chain_ok:
        rr["reason"]="non_chain_multi_event_route";rows.append(rr);continue

    mints=[events[0]["inputMint"]]+[ev["outputMint"] for ev in events]
    if len(set(mints))!=len(mints):
        rr["reason"]="cycle_or_repeated_mint";rows.append(rr);continue

    I=events[0]["inputMint"];O=events[-1]["outputMint"]
    rr["route_input_mint"]=I;rr["route_output_mint"]=O
    rr["hop_count"]=len(events)
    if I==A and O==L:
        rr.update(classification="DIRECTION_PROVEN",route_semantic="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN",
                  asset_label="SIGNED_SELL_PRESSURE_PROVEN",liability_label="SIGNED_BUY_PRESSURE_PROVEN")
    elif I==L and O==A:
        rr.update(classification="DIRECTION_PROVEN",route_semantic="LIABILITY_TO_COLLATERAL_MULTI_HOP_PROVEN",
                  liability_label="SIGNED_SELL_PRESSURE_PROVEN",asset_label="SIGNED_BUY_PRESSURE_PROVEN")
    else:
        rr.update(classification="DIRECTION_AMBIGUOUS",reason="route_endpoints_not_equal_asset_liability_pair")
    rows.append(rr)

with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

N=len(rows)
I=sum(1 for r in rows if r["classification"]=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in rows if r["classification"]=="DIRECTION_PROVEN")
A=sum(1 for r in rows if r["classification"]=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in rows if r["classification"]=="CONTRADICTION")
complete=N-I
incomplete_rate=I/N if N else 1.0
direction_rate=D/complete if complete else 0.0

classification="MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_COMPLETE" if N==len(sample) else "MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_BLOCKED"

receipt={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority":"MARGINFI_JUPITER_FULL_MULTI_HOP_SIGNED_FLOW_CENSUS_FREEZE_V0.2.md",
 "sharding_authority":"MARGINFI_JUPITER_FULL_MULTI_HOP_CENSUS_SHARDING_ADDENDUM_V0.2.md",
 "population_member_count":len(all_members),"shard_index":args.shard_index,"shard_count":args.shard_count,
 "assigned_count":len(sample),"sample_count":N,
 "source_evidence_incomplete":I,"direction_proven":D,"direction_ambiguous":A,"contradictions":C,
 "incomplete_rate":incomplete_rate,"direction_rate_complete":direction_rate,
 "hop_count_distribution":{str(k):sum(1 for r in rows if r.get("hop_count")==k) for k in sorted({r.get("hop_count") for r in rows if r.get("hop_count") is not None})},
 "incomplete_reason_counts":{reason:sum(1 for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE" and r.get("reason")==reason)
    for reason in sorted({r.get("reason") for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE" and r.get("reason")})},
 "rows_file":str(ROWS),"rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"usd_notional":False,
   "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,
   "wallets":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","population_member_count","shard_index","assigned_count","sample_count",
 "source_evidence_incomplete","direction_proven","direction_ambiguous","contradictions",
 "incomplete_rate","direction_rate_complete","hop_count_distribution","incomplete_reason_counts"]},indent=2))
if classification=="MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_BLOCKED":raise SystemExit(2)

#!/usr/bin/env python3
import argparse,base64,datetime as dt,hashlib,json,struct,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
MARGINFI_D8=bytes.fromhex("d6a997d5fba756db")
JUPITER="JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
SWAP_DISC=hashlib.sha256(b"event:SwapEvent").digest()[:8]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True)
ap.add_argument("--end",required=True)
ap.add_argument("--shard-id",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()

START=args.start;END=args.end;SID=args.shard_id
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/f"MARGINFI_FEBMAR_SOURCE_SHARD_{SID}_RECEIPT_V0.1.json"
POP=OUT/f"MARGINFI_FEBMAR_SOURCE_SHARD_{SID}_POPULATION_V0.1.ndjson"
MEM=OUT/f"MARGINFI_FEBMAR_SOURCE_SHARD_{SID}_MEMBERS_V0.1.ndjson"

def iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def norm_ts(v):
    if isinstance(v,str):return v
    if isinstance(v,(int,float)):
        return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def key(sig,addr):return sig+"|"+addrkey(addr)

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

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":f"crypto-lab-marginfi-febmar-source/{SID}"}
    if data is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(60,2**i));continue
            return int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    st,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

def blocked(stage,detail,**extra):
    rec={
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"MARGINFI_FEBMAR_SOURCE_SHARD_BLOCKED",
      "shard_id":SID,"start":START,"end":END,"stage":stage,"detail":str(detail)[:1200],
      "firewall":{"prices":False,"returns":False,"pnl":False,"market_outcomes_feb_mar_2024":False,
                  "apr_jun_2024_holdout_opened":False,"market_2025_opened":False,"market_2026_opened":False,
                  "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False},
      **extra
    }
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    POP.write_text("");MEM.write_text("")
    print(json.dumps(rec,indent=2,sort_keys=True))
    raise SystemExit(2)

try:
    brec=find_one(args.bank_registry_root,"MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json")
    if brec is None:blocked("authority","bank_registry_receipt_missing_or_duplicate")
    br=json.loads(brec.read_text())
    if br.get("classification")!="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS":
        blocked("authority","bank_registry_not_pass")
    registry={x["bank"]:x["mint"] for x in br.get("bank_registry") or []}

    lo=int(iso(START).timestamp());hi=int(iso(END).timestamp())
    current=ts_slot(START);to=ts_slot(END)+16
    population={};jup_by_tx={};requests=0;termination=[];anomalies=[]

    while current<=to:
        body={"type":"solana","fromBlock":current,"toBlock":to,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}
          },
          "instructions":[
            {"programId":[MARGINFI],"d8":["0x"+MARGINFI_D8.hex()],"isCommitted":True,"transaction":True},
            {"programId":[JUPITER],"isCommitted":True,"transaction":True}
          ]}
        st,raw=req(STREAM,body);requests+=1
        if st==204:
            termination.append({"http_status":204,"from_slot":current});break
        if st!=200:raise RuntimeError(f"stream_http_{st}")
        docs=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not docs:
            termination.append({"http_status":200,"from_slot":current,"reason":"empty_ndjson"});break
        last=None
        for b in docs:
            hdr=b.get("header") or {};slot=hdr.get("number");ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int):last=slot if last is None else max(last,slot)
            if not isinstance(ts,str):continue
            try:bt=int(iso(ts).timestamp())
            except Exception:continue
            if not(lo<=bt<hi):continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                ti=tx.get("transactionIndex",tx.get("index",pos));tx_by[ti]=tx
            for ix in b.get("instructions") or []:
                pid=ix.get("programId")
                if pid not in (MARGINFI,JUPITER):continue
                ti=ix.get("transactionIndex");tx=tx_by.get(ti)
                if not isinstance(tx,dict):
                    anomalies.append({"reason":"missing_parent_transaction","slot":slot,"programId":pid});continue
                if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:
                    continue
                sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                addr=ix.get("instructionAddress")
                if not sig or not isinstance(addr,list):
                    anomalies.append({"reason":"bad_identity","slot":slot,"programId":pid});continue
                if pid==JUPITER:
                    jup_by_tx.setdefault((sig,ti),[]).append({
                      "instructionAddress":addr,"data":ix.get("data"),"accounts":ix.get("accounts") or []
                    })
                    continue
                try:rawdata=b58d(ix.get("data") or "")
                except Exception:
                    anomalies.append({"reason":"marginfi_data_decode_failure","signature":sig,"instructionAddress":addr});continue
                if not rawdata.startswith(MARGINFI_D8):continue
                accounts=ix.get("accounts") or []
                if len(accounts)<10:
                    anomalies.append({"reason":"marginfi_account_count_lt_10","signature":sig,
                                      "instructionAddress":addr,"account_count":len(accounts)});continue
                row={
                  "signature":sig,"slot":slot,"timestamp":ts,"transactionIndex":ti,
                  "instructionAddress":addr,"asset_bank":accounts[1],"liab_bank":accounts[2],
                  "account_count":len(accounts),"programId":MARGINFI
                }
                k=key(sig,addr)
                if k in population and population[k]!=row:
                    anomalies.append({"reason":"marginfi_identity_conflict","identity":k})
                population[k]=row
        if last is None:raise RuntimeError("no_block_number")
        if last<current:raise RuntimeError("non_advancing_stream")
        current=last+1

    poprows=sorted(population.values(),key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
    with POP.open("w") as fh:
        for r in poprows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

    members=[]
    for p in poprows:
        jups=jup_by_tx.get((p["signature"],p["transactionIndex"]),[])
        after=[j for j in jups if tuple(j["instructionAddress"])>tuple(p["instructionAddress"])]
        if not after:continue

        rr={**p,"classification":"SOURCE_EVIDENCE_INCOMPLETE",
            "class_id":"MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_V0_1",
            "asset_mint":registry.get(p["asset_bank"]),"liab_mint":registry.get(p["liab_bank"]),
            "jupiter_after_count":len(after)}
        A=rr["asset_mint"];L=rr["liab_mint"]
        if not A or not L or A==L:
            rr["reason"]="bank_mint_mapping_missing_or_same";members.append(rr);continue

        addrs=[j["instructionAddress"] for j in after]
        roots=[]
        for a in sorted(addrs,key=lambda x:(len(x),tuple(x))):
            if not any(len(r)<len(a) and a[:len(r)]==r for r in roots):roots.append(a)
        rr["jupiter_route_roots"]=roots
        if len(roots)!=1:
            rr["reason"]="jupiter_route_root_count_"+str(len(roots));members.append(rr);continue
        root=roots[0]

        events=[]
        for j in after:
            a=j["instructionAddress"]
            if not(len(a)>len(root) and a[:len(root)]==root):continue
            ev=decode_swap_event(j.get("data"))
            if ev is not None:events.append({"instructionAddress":a,**ev})
        events.sort(key=lambda x:tuple(x["instructionAddress"]))
        rr["decoded_swap_event_count"]=len(events)
        rr["decoded_swap_events"]=events
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

        I=events[0]["inputMint"];O=events[-1]["outputMint"]
        rr["route_input_mint"]=I;rr["route_output_mint"]=O;rr["hop_count"]=len(events)
        if I==A and O==L:
            rr.update(classification="DIRECTION_PROVEN",
                      route_semantic="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN",
                      asset_label="SIGNED_SELL_PRESSURE_PROVEN",
                      liability_label="SIGNED_BUY_PRESSURE_PROVEN")
        elif I==L and O==A:
            rr.update(classification="DIRECTION_PROVEN",
                      route_semantic="LIABILITY_TO_COLLATERAL_MULTI_HOP_PROVEN",
                      liability_label="SIGNED_SELL_PRESSURE_PROVEN",
                      asset_label="SIGNED_BUY_PRESSURE_PROVEN")
        else:
            rr.update(classification="DIRECTION_AMBIGUOUS",
                      reason="route_endpoints_not_equal_asset_liability_pair")
        members.append(rr)

    members.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
    with MEM.open("w") as fh:
        for r in members:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

    duplicate_count=len(poprows)-len({key(r["signature"],r["instructionAddress"]) for r in poprows})
    contradiction_count=sum(1 for r in members if r.get("classification")=="CONTRADICTION")
    classification="MARGINFI_FEBMAR_SOURCE_SHARD_COMPLETE" if not anomalies and duplicate_count==0 else "MARGINFI_FEBMAR_SOURCE_SHARD_BLOCKED"
    rec={
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
      "authority":"MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_TEMPORAL_SOURCE_EXTENSION_FREEZE_V0.1.md",
      "shard_id":SID,"start":START,"end":END,
      "population_count":len(poprows),"route_member_count":len(members),
      "source_evidence_incomplete":sum(1 for r in members if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE"),
      "direction_proven":sum(1 for r in members if r.get("classification")=="DIRECTION_PROVEN"),
      "direction_ambiguous":sum(1 for r in members if r.get("classification")=="DIRECTION_AMBIGUOUS"),
      "contradictions":contradiction_count,"duplicate_identity_count":duplicate_count,
      "anomaly_count":len(anomalies),"anomalies":anomalies[:200],
      "request_count":requests,"termination_evidence":termination,
      "population_file":str(POP),"members_file":str(MEM),
      "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
      "members_sha256":hashlib.sha256(MEM.read_bytes()).hexdigest(),
      "firewall":{"prices":False,"returns":False,"pnl":False,"market_outcomes_feb_mar_2024":False,
                  "apr_jun_2024_holdout_opened":False,"market_2025_opened":False,"market_2026_opened":False,
                  "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
    }
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:rec[k] for k in ["classification","shard_id","population_count","route_member_count",
      "source_evidence_incomplete","direction_proven","direction_ambiguous","contradictions",
      "duplicate_identity_count","anomaly_count","request_count"]},indent=2))
    if classification!="MARGINFI_FEBMAR_SOURCE_SHARD_COMPLETE":raise SystemExit(2)
except SystemExit:
    raise
except Exception as e:
    blocked("exception",f"{type(e).__name__}:{e}")

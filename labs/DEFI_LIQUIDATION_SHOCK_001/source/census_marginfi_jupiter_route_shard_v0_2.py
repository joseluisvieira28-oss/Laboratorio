#!/usr/bin/env python3
import argparse,datetime as dt,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
MARGINFI_D8="d6a997d5fba756db"
JUPITER="JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True)
ap.add_argument("--end",required=True)
ap.add_argument("--shard-id",required=True)
ap.add_argument("--source",default="event_source/marginfi-202401.json")
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()

START=args.start;END=args.end;SID=args.shard_id
SRC=Path(args.source);OUTDIR=Path(args.outdir);OUTDIR.mkdir(parents=True,exist_ok=True)
OUT=OUTDIR/f"MARGINFI_JUPITER_ROUTE_SHARD_{SID}_RECEIPT_V0.1.json"
MEMBERS=OUTDIR/f"MARGINFI_JUPITER_ROUTE_SHARD_{SID}_MEMBERS_V0.1.ndjson"

def iso(s): return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def key(sig,addr): return sig+"|"+addr_key(addr)

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":f"crypto-lab-dls-marginfi-jupiter-shard/{SID}"}
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
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

def emit_blocked(stage,detail,canonical_count=0,**extra):
    rec={
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","shard_id":SID,
      "start":START,"end":END,"classification":"MARGINFI_JUPITER_ROUTE_SHARD_BLOCKED",
      "stage":stage,"detail":str(detail)[:1000],"canonical_population_count":canonical_count,
      "firewall":{"token_balances":False,"token_amounts":False,"prices":False,"returns":False,"pnl":False,
       "market_direction":False,"market_2025_opened":False,"market_2026_opened":False,
       "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False},
      **extra
    }
    OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    MEMBERS.write_text("")
    print(json.dumps(rec,indent=2,sort_keys=True))
    raise SystemExit(2)

try:
    src=json.loads(SRC.read_text())
    if src.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":
        emit_blocked("authority","field_enrichment_not_pass")
    lo=int(iso(START).timestamp());hi=int(iso(END).timestamp())
    canonical={}
    for r in src.get("enriched_rows") or []:
        if r.get("protocol")!="marginfi" or r.get("instruction_class")!="lending_account_liquidate":continue
        t=iso(r["timestamp"])
        if not(iso(START)<=t<iso(END)):continue
        canonical[key(r["signature"],r["instructionAddress"])]={
          "signature":r["signature"],"instructionAddress":r["instructionAddress"],"slot":r["slot"],
          "timestamp":r["timestamp"],"transactionIndex":r.get("transactionIndex"),
          "semantic_accounts":r.get("semantic_accounts") or {}
        }
    if not canonical:emit_blocked("population","empty_canonical_shard")

    current=ts_slot(START);to=ts_slot(END)+16
    seen={};jup_by_tx={};requests=0;terminations=[];anomalies=[]
    while current<=to:
        body={"type":"solana","fromBlock":current,"toBlock":to,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"transactionIndex":True,"instructionAddress":True,
                           "isCommitted":True,"error":True}
          },
          "instructions":[
            {"programId":[MARGINFI],"d8":["0x"+MARGINFI_D8],"isCommitted":True,"transaction":True},
            {"programId":[JUPITER],"isCommitted":True,"transaction":True}
          ]}
        st,raw=req(STREAM,body);requests+=1
        if st==204:
            terminations.append({"http_status":204,"from_slot":current});break
        if st!=200:raise RuntimeError(f"stream_http_{st}")
        docs=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not docs:
            terminations.append({"http_status":200,"from_slot":current,"reason":"empty_ndjson"});break
        last=None
        for b in docs:
            hdr=b.get("header") or {};slot=hdr.get("number");ts=hdr.get("timestamp")
            if isinstance(slot,int):last=slot if last is None else max(last,slot)
            if isinstance(ts,(int,float)):ts=dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")
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
                sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                addr=ix.get("instructionAddress")
                if not sig or not isinstance(addr,list):
                    anomalies.append({"reason":"bad_identity","slot":slot,"programId":pid});continue
                if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:
                    continue
                if pid==MARGINFI:
                    k=key(sig,addr)
                    row={"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,"transactionIndex":ti}
                    if k in seen and seen[k]!=row:anomalies.append({"reason":"marginfi_exact_identity_conflict","key":k})
                    seen[k]=row
                else:
                    jup_by_tx.setdefault((sig,ti),[]).append({"instructionAddress":addr,"slot":slot})
        if last is None:raise RuntimeError("no_block_number")
        if last<current:raise RuntimeError("non_advancing_stream")
        current=last+1

    canon_keys=set(canonical);seen_keys=set(seen)
    missing=sorted(canon_keys-seen_keys);extra=sorted(seen_keys-canon_keys)
    if extra:anomalies.append({"reason":"unexpected_marginfi_population_extra","count":len(extra),"sample":extra[:20]})
    if missing:anomalies.append({"reason":"canonical_marginfi_population_missing","count":len(missing),"sample":missing[:20]})

    members=[]
    for k,c in canonical.items():
        s=seen.get(k)
        if s is None:continue
        jups=jup_by_tx.get((c["signature"],s["transactionIndex"]),[])
        after=[j for j in jups if tuple(j["instructionAddress"])>tuple(c["instructionAddress"])]
        if after:
            members.append({
              **c,"source_transaction_index":s["transactionIndex"],"jupiter_after_count":len(after),
              "jupiter_after_instruction_addresses":[j["instructionAddress"] for j in sorted(after,key=lambda x:tuple(x["instructionAddress"]))],
              "class_id":"MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_V0_1","shard_id":SID
            })
    members=sorted(members,key=lambda r:(r["timestamp"],r["slot"],r["signature"],addr_key(r["instructionAddress"])))
    with MEMBERS.open("w") as f:
        for r in members:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")

    classification="MARGINFI_JUPITER_ROUTE_SHARD_PASS" if not anomalies else "MARGINFI_JUPITER_ROUTE_SHARD_BLOCKED"
    receipt={
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
      "shard_id":SID,"start":START,"end":END,"class_id":"MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_V0_1",
      "canonical_population_count":len(canonical),"recovered_population_count":len(seen),
      "member_count":len(members),"member_rate":len(members)/len(canonical),
      "request_count":requests,"termination_evidence":terminations,
      "missing_count":len(missing),"extra_count":len(extra),"anomaly_count":len(anomalies),
      "anomalies":anomalies[:200],"members_file":str(MEMBERS),
      "members_sha256":hashlib.sha256(MEMBERS.read_bytes()).hexdigest(),
      "firewall":{"token_balances":False,"token_amounts":False,"prices":False,"returns":False,"pnl":False,
       "market_direction":False,"market_2025_opened":False,"market_2026_opened":False,
       "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
    }
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:receipt[k] for k in ("classification","shard_id","canonical_population_count","recovered_population_count","member_count","missing_count","extra_count","anomaly_count","request_count")},indent=2))
    if classification!="MARGINFI_JUPITER_ROUTE_SHARD_PASS":raise SystemExit(2)
except SystemExit:
    raise
except Exception as e:
    emit_blocked("exception",f"{type(e).__name__}:{e}")

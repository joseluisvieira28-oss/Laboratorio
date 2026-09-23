#!/usr/bin/env python3
import datetime as dt, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

ROOT=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
CROOT=ROOT/"sqd_census_v0_4"
CENSUS=ROOT/"KAMINO_SAVE11_SQD_EVENT_CENSUS_RECEIPT_V0.4.2.json"
RAWREC=ROOT/"KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.5.json"
OUTROOT=CROOT/"field_enrichment_v0_6"
OUTROOT.mkdir(parents=True,exist_ok=True)
OUT=ROOT/"KAMINO_SAVE11_FIELD_ENRICHMENT_RECEIPT_V0.6.json"
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
SAVE_LAYOUT_TS=int(dt.datetime.fromisoformat("2024-08-06T11:54:18+00:00").timestamp())

P={
 "kamino":{"program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix":"b1479abce2854a37","fk":"d8","fv":"0xb1479abce2854a37"},
 "save11":{"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"11","fk":None,"fv":None}
}
K16=["liquidator","obligation","lending_market","lending_market_authority","repay_reserve",
"repay_reserve_liquidity_supply","withdraw_reserve","withdraw_reserve_collateral_mint",
"withdraw_reserve_collateral_supply","withdraw_reserve_liquidity_supply",
"withdraw_reserve_liquidity_fee_receiver","user_source_liquidity","user_destination_collateral",
"user_destination_liquidity","token_program","instruction_sysvar_account"]
K20=["liquidator","obligation","lending_market","lending_market_authority","repay_reserve",
"repay_reserve_liquidity_mint","repay_reserve_liquidity_supply","withdraw_reserve",
"withdraw_reserve_liquidity_mint","withdraw_reserve_collateral_mint",
"withdraw_reserve_collateral_supply","withdraw_reserve_liquidity_supply",
"withdraw_reserve_liquidity_fee_receiver","user_source_liquidity","user_destination_collateral",
"user_destination_liquidity","collateral_token_program","repay_liquidity_token_program",
"withdraw_liquidity_token_program","instruction_sysvar_account"]
S15=["source_liquidity","destination_collateral","destination_reward_liquidity","repay_reserve",
"repay_reserve_liquidity_supply","withdraw_reserve","withdraw_reserve_collateral_mint",
"withdraw_reserve_collateral_supply","withdraw_reserve_liquidity_supply",
"withdraw_reserve_fee_receiver","obligation","lending_market","lending_market_authority",
"transfer_authority","token_program"]

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("bad_base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def key(protocol,sig,address): return protocol+":"+sig+":"+canon(address)
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
def norm_ts(v):
    if isinstance(v,(int,float)): return int(v)
    if isinstance(v,str):
        try:return int(dt.datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
        except:return None
    return None

def post(body,retries=9):
    raw=json.dumps(body,separators=(",",":")).encode(); last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(STREAM,data=raw,method="POST",headers={
             "Content-Type":"application/json","Accept":"application/x-ndjson,application/json",
             "User-Agent":"crypto-lab-dls-field-enrichment/0.6"})
            with urllib.request.urlopen(req,timeout=90) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            txt=e.read().decode("utf-8","replace"); last={"http":e.code,"body":txt[:500]}
            if e.code in (429,529) or 500<=e.code<600:
                time.sleep(min(45,2**i)); continue
            return int(e.code),dict(e.headers),txt
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:400]}; time.sleep(min(45,2**i))
    raise RuntimeError(str(last))

def query_chunk(protocol,cfg,start,end):
    current=start; found={}; requests=0
    while current<=end:
        filt={"programId":[cfg["program"]],"transaction":True}
        if cfg["fk"]: filt[cfg["fk"]]=[cfg["fv"]]
        body={"type":"solana","fromBlock":current,"toBlock":end,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"data":True,"accounts":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True}},
          "instructions":[filt]}
        st,h,txt=post(body); requests+=1
        if st==204: return found,requests,None
        if st!=200: return found,requests,f"http_{st}:{txt[:400]}"
        lines=[x for x in txt.splitlines() if x.strip()]
        if not lines: return found,requests,"empty_200"
        batch=[json.loads(x) for x in lines]; last=None
        for b in batch:
            hdr=b.get("header") or {}; slot=hdr.get("number"); ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            txs=b.get("transactions") or []; txby={}
            for pos,tx in enumerate(txs):
                txby[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=cfg["program"]: continue
                try: data=b58decode(ix.get("data") or "")
                except: continue
                if not data.startswith(bytes.fromhex(cfg["prefix"])): continue
                tx=txby.get(ix.get("transactionIndex"),{})
                sigs=tx.get("signatures") or []
                addr=ix.get("instructionAddress")
                if not sigs or not isinstance(sigs[0],str) or not isinstance(addr,list): continue
                k=key(protocol,sigs[0],addr)
                row={"protocol":protocol,"signature":sigs[0],"instructionAddress":addr,
                     "slot":slot,"timestamp":ts,"transactionErr":tx.get("err"),
                     "isCommitted":ix.get("isCommitted"),"instructionError":ix.get("error"),
                     "accounts":ix.get("accounts"),"data_base58":ix.get("data"),"data_hex":data.hex()}
                if k in found and canon(found[k])!=canon(row): return found,requests,"conflicting_duplicate_source_key"
                found[k]=row
        if last is None:return found,requests,"non_advancing_no_block"
        current=last+1
        if last>=end:break
    return found,requests,None

census=json.loads(CENSUS.read_text())
rawrec=json.loads(RAWREC.read_text())
if census.get("classification")!="SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
    raise SystemExit("CENSUS_NOT_COMPLETE")
if rawrec.get("classification")!="RAW_SAMPLE_RECONCILIATION_PASS":
    raise SystemExit("RAW_SAMPLE_NOT_PASS")

global_rows=[]; anomalies=[]; pending_save=0; request_total=0
for protocol,cfg in P.items():
    cdir=CROOT/"chunks"/protocol
    outp=OUTROOT/f"{protocol}.jsonl"
    out_rows=[]
    for receipt_path in sorted(cdir.glob("*.receipt.json")):
        rec=json.loads(receipt_path.read_text())
        if rec.get("classification")!="SOURCE_CHUNK_COMPLETE":
            raise SystemExit(f"NON_COMPLETE_CHUNK {receipt_path}")
        ledger_path=Path(rec["ledger_path"])
        if not ledger_path.is_absolute():
            ledger_path=Path(ledger_path)
        expected={}
        for line in ledger_path.read_text().splitlines():
            if not line.strip(): continue
            x=json.loads(line); expected[key(protocol,x["signature"],x["instructionAddress"])]=x
        source,reqs,blocker=query_chunk(protocol,cfg,int(rec["start_slot"]),int(rec["end_slot"]))
        request_total+=reqs
        if blocker:
            anomalies.append({"protocol":protocol,"date":rec["date"],"type":"transport_blocker","detail":blocker})
            break
        expkeys=set(expected); srckeys=set(source)
        if expkeys!=srckeys:
            anomalies.append({"protocol":protocol,"date":rec["date"],"type":"source_key_set_mismatch",
                              "missing_count":len(expkeys-srckeys),"extra_count":len(srckeys-expkeys),
                              "missing_sample":sorted(expkeys-srckeys)[:5],"extra_sample":sorted(srckeys-expkeys)[:5]})
            break
        for k in sorted(expkeys):
            base=expected[k]; src=source[k]; accounts=src.get("accounts")
            try:data=bytes.fromhex(src["data_hex"])
            except:data=b""
            enriched={**base,"account_count":len(accounts) if isinstance(accounts,list) else None,
                      "raw_accounts":accounts,"raw_instruction_data_hex":src.get("data_hex"),
                      "raw_accounts_sha256":sha(canon(accounts).encode()) if isinstance(accounts,list) else None,
                      "raw_instruction_data_sha256":sha(data)}
            if protocol=="kamino":
                if len(data)<32 or not isinstance(accounts,list):
                    enriched["field_classification"]="KAMINO_FIELD_LAYOUT_UNRESOLVED_FAIL_CLOSED"
                    anomalies.append({"protocol":protocol,"key":k,"type":"kamino_short_data_or_accounts"})
                elif len(accounts)==16:
                    enriched["field_classification"]="KAMINO_LAYOUT_A_FIELDS_RESOLVED"
                    enriched["layout"]="A_16"
                    enriched["fields"]={n:accounts[i] for i,n in enumerate(K16)}
                    enriched["liquidity_amount_native"]=int.from_bytes(data[8:16],"little")
                    enriched["min_acceptable_received_collateral_amount_native"]=int.from_bytes(data[16:24],"little")
                    enriched["max_allowed_ltv_override_percent_raw"]=int.from_bytes(data[24:32],"little")
                elif len(accounts)==20:
                    enriched["field_classification"]="KAMINO_LAYOUT_B_FIELDS_RESOLVED"
                    enriched["layout"]="B_20"
                    enriched["fields"]={n:accounts[i] for i,n in enumerate(K20)}
                    enriched["liquidity_amount_native"]=int.from_bytes(data[8:16],"little")
                    enriched["min_acceptable_received_liquidity_amount_native"]=int.from_bytes(data[16:24],"little")
                    enriched["max_allowed_ltv_override_percent_raw"]=int.from_bytes(data[24:32],"little")
                else:
                    enriched["field_classification"]="KAMINO_FIELD_LAYOUT_UNRESOLVED_FAIL_CLOSED"
                    anomalies.append({"protocol":protocol,"key":k,"type":"kamino_unknown_account_count","count":len(accounts)})
            else:
                if not isinstance(accounts,list) or len(data)<9:
                    enriched["field_classification"]="SAVE11_FIELD_LAYOUT_UNRESOLVED_FAIL_CLOSED"
                    anomalies.append({"protocol":protocol,"key":k,"type":"save_short_data_or_accounts"})
                elif int(base["timestamp"])<SAVE_LAYOUT_TS:
                    enriched["field_classification"]="SAVE11_FIELD_LAYOUT_PENDING_RAW_RECONCILIATION"
                    enriched["raw_arg_u64_0"]=int.from_bytes(data[1:9],"little")
                    pending_save+=1
                elif len(accounts)==15:
                    enriched["field_classification"]="SAVE11_LAYOUT_PUBLIC_FIELDS_RESOLVED"
                    enriched["fields"]={n:accounts[i] for i,n in enumerate(S15)}
                    enriched["liquidity_amount_native"]=int.from_bytes(data[1:9],"little")
                else:
                    enriched["field_classification"]="SAVE11_FIELD_LAYOUT_UNRESOLVED_FAIL_CLOSED"
                    anomalies.append({"protocol":protocol,"key":k,"type":"save_unknown_account_count","count":len(accounts)})
            out_rows.append(enriched)
        time.sleep(0.02)
    outp.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in out_rows))
    global_rows.extend(out_rows)

hard=[a for a in anomalies if a.get("type")!="allowed_save_prelayout"]
if hard:
    classification="FIELD_ENRICHMENT_FAIL_CLOSED"
elif pending_save:
    classification="FIELD_ENRICHMENT_COMPLETE_WITH_SAVE11_PRELAYOUT_PENDING"
else:
    classification="FIELD_ENRICHMENT_COMPLETE"

counts={}
for p in P:
    rr=[x for x in global_rows if x["protocol"]==p]
    counts[p]={"rows":len(rr),"field_classes":{}}
    for x in rr:
        fc=x.get("field_classification")
        counts[p]["field_classes"][fc]=counts[p]["field_classes"].get(fc,0)+1

receipt={"schema_version":"0.6","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,"request_count":request_total,"protocol_counts":counts,
 "save11_prelayout_pending_count":pending_save,"anomalies":anomalies,
 "output_files":{p:str(OUTROOT/f"{p}.jsonl") for p in P},
 "firewall":{"prices":False,"usd_values":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}}
write_json(OUT,receipt)
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="FIELD_ENRICHMENT_FAIL_CLOSED": raise SystemExit(2)

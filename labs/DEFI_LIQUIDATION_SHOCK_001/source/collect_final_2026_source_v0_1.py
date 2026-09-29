#!/usr/bin/env python3
import argparse,base64,datetime as dt,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
RPC="https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SYSVAR_INSTRUCTIONS="Sysvar1nstructions1111111111111111111111111"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

CFG={
 "marginfi":{"program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
   "prefix":"d6a997d5fba756db","filter_key":"d8","filter_value":"0xd6a997d5fba756db",
   "class":"lending_account_liquidate"},
 "save0c":{"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix":"0c","filter_key":"d1","filter_value":"0x0c","class":"LiquidateObligation"},
 "kamino":{"program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
   "prefix":"b1479abce2854a37","filter_key":"d8","filter_value":"0xb1479abce2854a37",
   "class":"liquidate_obligation_and_redeem_reserve_collateral"},
 "save11":{"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix":"11","filter_key":"d1","filter_value":"0x11","class":"LiquidateObligationAndRedeemReserveCollateral"}
}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

def iso(s): return dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
def norm(v):
    if isinstance(v,str):return v
    if isinstance(v,(int,float)):return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def addrkey(v): return json.dumps(v,separators=(",",":"),sort_keys=True)

def req(url,body=None,retries=12):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-final2026-source/0.1"}
    if data is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":raw[:240].decode("utf-8","replace")};time.sleep(min(90,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(90,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    st,h,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

def rpc_slices(keys,offset,length,retries=8):
    out=[]
    for i in range(0,len(keys),100):
        chunk=keys[i:i+100]
        body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
              "params":[chunk,{"encoding":"base64","commitment":"finalized","dataSlice":{"offset":offset,"length":length}}]}
        raw=json.dumps(body,separators=(",",":")).encode()
        q=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json",
          "User-Agent":"crypto-lab-dls-final2026-source/0.1"},method="POST")
        last=None
        for n in range(retries):
            try:
                with urllib.request.urlopen(q,timeout=90) as r:
                    o=json.loads(r.read())
                    if o.get("error"):raise RuntimeError(str(o["error"]))
                    vals=o["result"]["value"]
                    out.extend(vals)
                    break
            except Exception as e:
                last=str(e)[:240];time.sleep(min(30,2**n))
        else: raise RuntimeError(f"rpc_exhausted:{last}")
    return out

def token_pairs(tb):
    s=set()
    if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
        s.add((tb["preMint"],int(tb["preDecimals"])))
    if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
        s.add((tb["postMint"],int(tb["postDecimals"])))
    return s

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=sorted(CFG),required=True)
ap.add_argument("--start",default="2025-01-01T00:00:00Z")
ap.add_argument("--end",default="2026-01-01T00:00:00Z")
ap.add_argument("--out",required=True)
args=ap.parse_args();c=CFG[args.protocol]
lo,hi=iso(args.start),iso(args.end);current=ts_slot(args.start);to_slot=ts_slot(args.end)+16
rows=[];errors=[];duplicates=[];seen=set();reqs=0;terms=[]

while current<=to_slot:
    filt={"programId":[c["program"]],c["filter_key"]:[c["filter_value"]],
          "isCommitted":True,"transaction":True}
    if args.protocol=="save11":filt["transactionTokenBalances"]=True
    fields={"block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}}
    if args.protocol=="save11":
        fields["tokenBalance"]={"transactionIndex":True,"account":True,"preMint":True,"postMint":True,
                                "preDecimals":True,"postDecimals":True}
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,"fields":fields,"instructions":[filt]}
    st,h,raw=req(STREAM,body);reqs+=1
    if st==204:
        terms.append({"http_status":204,"from_slot":current,"reason":"NO_CONTENT_TERMINATION"});break
    if st!=200:raise RuntimeError(f"stream_http_{st}")
    lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    if not lines:
        terms.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON_TERMINATION"});break
    batch=[json.loads(x) for x in lines];last=None
    for b in batch:
        hdr=b.get("header") or {};slot=hdr.get("number");ts=norm(hdr.get("timestamp"))
        if isinstance(slot,int):last=slot if last is None else max(last,slot)
        if ts is None:continue
        try:t=iso(ts)
        except Exception:continue
        if not(lo<=t<hi):continue
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        tb_by_tx={}
        if args.protocol=="save11":
            for tb in b.get("tokenBalances") or []:
                ti=tb.get("transactionIndex");acct=tb.get("account")
                if ti is None or not acct:continue
                tb_by_tx.setdefault(ti,{}).setdefault(acct,set()).update(token_pairs(tb))
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=c["program"]:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(bytes.fromhex(c["prefix"])):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict):errors.append({"reason":"missing_parent_transaction","slot":slot});continue
            if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list):
                errors.append({"reason":"bad_identity","slot":slot});continue
            k=(sig,addrkey(addr))
            if k in seen:
                duplicates.append({"signature":sig,"instructionAddress":addr});continue
            seen.add(k)
            rec={"protocol":args.protocol,"instruction_class":c["class"],"signature":sig,
                 "instructionAddress":addr,"slot":slot,"timestamp":ts,
                 "account_count":len(accounts),"data_length":len(dec)}
            if args.protocol=="marginfi":
                if len(accounts)<10:
                    errors.append({"reason":"marginfi_account_shape","signature":sig,"observed":len(accounts)});continue
                rec["mapping_account"]=accounts[1]
            elif args.protocol=="save0c":
                if len(accounts)!=12 or len(dec)!=9:
                    errors.append({"reason":"save0c_shape","signature":sig,"account_count":len(accounts),"data_length":len(dec)});continue
                rec["mapping_account"]=accounts[4]
            elif args.protocol=="kamino":
                if len(accounts)<20:
                    errors.append({"reason":"kamino_v16_prefix_missing","signature":sig,"observed":len(accounts)});continue
                if accounts[16]!=TOKEN_PROGRAM or accounts[19]!=SYSVAR_INSTRUCTIONS or not accounts[17] or not accounts[18]:
                    errors.append({"reason":"kamino_fixed_layout_conflict","signature":sig});continue
                rec["collateral_mint"]=accounts[8]
                rec["unit_resolution"]="DIRECT_WITHDRAW_LIQUIDITY_MINT_ACCOUNT"
            else:
                if len(accounts)!=15 or len(dec) not in (9,10):
                    errors.append({"reason":"save11_shape","signature":sig,"account_count":len(accounts),"data_length":len(dec)});continue
                primary=accounts[8];optional=accounts[2];tbmap=tb_by_tx.get(ti,{})
                pp=sorted(tbmap.get(primary,set()));op=sorted(tbmap.get(optional,set()))
                if len(pp)!=1 or len(op)>1 or (len(op)==1 and op[0]!=pp[0]):
                    errors.append({"reason":"save11_unit_resolution","signature":sig,
                                   "primary_pairs":[list(x) for x in pp],"optional_pairs":[list(x) for x in op]});continue
                rec["collateral_mint"]=pp[0][0];rec["collateral_decimals"]=pp[0][1]
                rec["unit_resolution"]="PRIMARY_RESERVE_VAULT_TOKEN_BALANCE"
            rows.append(rec)
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1

# Resolve protocol state accounts after complete source scan.
if args.protocol=="marginfi":
    keys=sorted({r["mapping_account"] for r in rows})
    vals=rpc_slices(keys,8,33)
    mp={}
    for key,val in zip(keys,vals):
        if val is None:
            errors.append({"reason":"marginfi_bank_missing","bank":key});continue
        if val.get("owner")!=c["program"]:
            errors.append({"reason":"marginfi_bank_owner","bank":key,"owner":val.get("owner")});continue
        try:data=base64.b64decode((val.get("data") or [""])[0])
        except Exception:errors.append({"reason":"marginfi_bank_decode","bank":key});continue
        if len(data)!=33:
            errors.append({"reason":"marginfi_bank_slice_len","bank":key,"observed":len(data)});continue
        mp[key]=(b58e(data[:32]),int(data[32]))
    for r in rows:
        pair=mp.get(r["mapping_account"])
        if pair is None:continue
        r["collateral_mint"],r["collateral_decimals"]=pair
        r["unit_resolution"]="FINALIZED_BANK_DATASLICE_8_33"

if args.protocol=="save0c":
    keys=sorted({r["mapping_account"] for r in rows})
    vals1=rpc_slices(keys,42,33);vals2=rpc_slices(keys,227,32)
    mp={}
    for key,a,b in zip(keys,vals1,vals2):
        if a is None or b is None:
            errors.append({"reason":"save0c_reserve_missing","reserve":key});continue
        if a.get("owner")!=c["program"] or b.get("owner")!=c["program"]:
            errors.append({"reason":"save0c_reserve_owner","reserve":key});continue
        try:da=base64.b64decode((a.get("data") or [""])[0]);db=base64.b64decode((b.get("data") or [""])[0])
        except Exception:errors.append({"reason":"save0c_reserve_decode","reserve":key});continue
        if len(da)!=33 or len(db)!=32:
            errors.append({"reason":"save0c_reserve_slice_len","reserve":key});continue
        mp[key]=(b58e(da[:32]),int(da[32]),b58e(db))
    for r in rows:
        pair=mp.get(r["mapping_account"])
        if pair is None:continue
        r["collateral_mint"],r["collateral_decimals"]=pair[0],pair[1]
        r["collateral_token_mint"]=pair[2]
        r["unit_resolution"]="FINALIZED_RESERVE_DATASLICE_42_33"

unresolved=sum(1 for r in rows if not r.get("collateral_mint"))
if unresolved:errors.append({"reason":"unresolved_collateral_mint","count":unresolved})
classification="FINAL_2026_PROTOCOL_SOURCE_PASS" if not errors and not duplicates else "FINAL_2026_PROTOCOL_SOURCE_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":args.protocol,
 "instruction_class":c["class"],"window_start":args.start,"window_end":args.end,
 "classification":classification,"successful_instruction_count":len(rows),
 "unique_collateral_mint_count":len({r.get("collateral_mint") for r in rows if r.get("collateral_mint")}),
 "sol_collateral_event_count":sum(1 for r in rows if r.get("collateral_mint")=="So11111111111111111111111111111111111111112"),
 "duplicate_count":len(duplicates),"error_count":len(errors),
 "duplicates":duplicates[:100],"errors":errors[:200],"request_count":reqs,
 "termination_evidence":terms,"rows":rows,
 "firewall":{"prices_2025":False,"returns_2025":False,"pnl_2025":False,"funding_2025":False,
             "market_direction_2025":False,"prices_2026":False,"returns_2026":False,
             "token_amounts":False,"oracle_values":False,"post_outcome_tuning":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["protocol","classification","successful_instruction_count",
 "unique_collateral_mint_count","sol_collateral_event_count","duplicate_count","error_count","request_count"]},indent=2))
if classification!="FINAL_2026_PROTOCOL_SOURCE_PASS":raise SystemExit(2)

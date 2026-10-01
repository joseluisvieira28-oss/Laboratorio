#!/usr/bin/env python3
import argparse,base64,datetime as dt,json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
RPC="https://api.mainnet-beta.solana.com"
PROGRAM="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
DISC="d6a997d5fba756db"
SOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
SPAN=10000
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

ap=argparse.ArgumentParser()
ap.add_argument("--month",choices=["202501","202502","202503"],required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
M=args.month
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
START={
 "202501":"2025-01-01T00:00:00Z","202502":"2025-02-01T00:00:00Z","202503":"2025-03-01T00:00:00Z"}[M]
END={
 "202501":"2025-02-01T00:00:00Z","202502":"2025-03-01T00:00:00Z","202503":"2025-04-01T00:00:00Z"}[M]
RECEIPT=OUT/f"MARGINFI_2025_Q1_LIABILITY_REGIME_{M}_RECEIPT_V0.1.json"
ROWS=OUT/f"MARGINFI_2025_Q1_LIABILITY_REGIME_{M}_ROWS_V0.1.ndjson"

def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

def iso(s): return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)
def norm(v):
    if isinstance(v,str):return v
    if isinstance(v,(int,float)):return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def addrkey(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])

def req(url,body=None,retries=10,timeout=90):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":f"crypto-lab-marginfi-q1-2025-{M}/0.1"}
    if data is not None:h["Content-Type"]="application/json"
    last=None
    for i in range(retries):
        q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
        try:
            with urllib.request.urlopen(q,timeout=timeout) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":raw[:200].decode("utf-8","replace")}
                ra=e.headers.get("Retry-After")
                try:delay=float(ra) if ra else min(60,2**i)
                except Exception:delay=min(60,2**i)
                time.sleep(max(0,min(120,delay)));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]}
            time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    st,_,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    if isinstance(o,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

def rpc_banks(keys,retries=10):
    out={}
    kk=sorted(set(keys))
    for st in range(0,len(kk),100):
        batch=kk[st:st+100]
        body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
              "params":[batch,{"encoding":"base64","commitment":"finalized",
                               "dataSlice":{"offset":8,"length":33}}]}
        data=json.dumps(body,separators=(",",":")).encode()
        last=None
        for i in range(retries):
            q=urllib.request.Request(RPC,data=data,headers={
              "Content-Type":"application/json","User-Agent":f"crypto-lab-marginfi-q1-2025-{M}/0.1"},method="POST")
            try:
                with urllib.request.urlopen(q,timeout=90) as r:
                    o=json.loads(r.read())
                    if o.get("error"):raise RuntimeError(str(o["error"]))
                    vals=o["result"]["value"]
                    if len(vals)!=len(batch):raise RuntimeError("rpc_length_mismatch")
                    for key,val in zip(batch,vals):
                        if val is None:raise RuntimeError(f"missing_bank:{key}")
                        if val.get("owner")!=PROGRAM:raise RuntimeError(f"owner_mismatch:{key}:{val.get('owner')}")
                        raw=base64.b64decode((val.get("data") or [""])[0])
                        if len(raw)!=33:raise RuntimeError(f"slice_len:{key}:{len(raw)}")
                        out[key]={"mint":b58e(raw[:32]),"decimals":int(raw[32])}
                    break
            except Exception as e:
                last=str(e)[:300];time.sleep(min(60,2**i))
        else:raise RuntimeError(f"rpc_exhausted:{last}")
    return out

def blocked(stage,detail,**extra):
    rec={"schema_version":"0.1","classification":"MARGINFI_2025_Q1_LIABILITY_REGIME_MONTH_BLOCKED",
         "month":M,"window_start":START,"window_end":END,"stage":stage,"detail":str(detail)[:2000],
         "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
                     "funding_2025_opened":False,"market_direction_2025_opened":False,
                     "prices_2026_opened":False,"returns_2026_opened":False,"token_amounts":False,
                     "oracle_values":False,"live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"merge_main":False},**extra}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");ROWS.write_text("")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

try:
    lo,hi=iso(START),iso(END);current=ts_slot(START);to=ts_slot(END)+16
    rows=[];seen=set();errors=[];requests=0;termination=[]
    while current<=to:
        request_to=min(to,current+SPAN-1)
        body={"type":"solana","fromBlock":current,"toBlock":request_to,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"accounts":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}
          },
          "instructions":[{"programId":[PROGRAM],"d8":["0x"+DISC],"isCommitted":True,"transaction":True}]
        }
        st,_,raw=req(STREAM,body);requests+=1
        if st==204:
            termination.append({"http_status":204,"from_slot":current,"to_slot":request_to})
            current=request_to+1;continue
        if st!=200:raise RuntimeError(f"stream_http_{st}")
        docs=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not docs:
            termination.append({"http_status":200,"from_slot":current,"to_slot":request_to,"reason":"empty_ndjson"})
            current=request_to+1;continue
        last=None
        for b in docs:
            hdr=b.get("header") or {};slot=hdr.get("number");ts=norm(hdr.get("timestamp"))
            if isinstance(slot,int):last=slot if last is None else max(last,slot)
            if not ts:continue
            try:t=iso(ts)
            except Exception:continue
            if not(lo<=t<hi):continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=PROGRAM:continue
                ti=ix.get("transactionIndex");tx=tx_by.get(ti)
                if not isinstance(tx,dict):errors.append({"reason":"missing_parent_transaction","slot":slot});continue
                if tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
                sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                addr=ix.get("instructionAddress");accounts=ix.get("accounts") or []
                if not sig or not isinstance(addr,list):
                    errors.append({"reason":"bad_identity","slot":slot});continue
                if len(accounts)<10:
                    errors.append({"reason":"account_shape","signature":sig,"count":len(accounts)});continue
                r={"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,
                   "transactionIndex":ti,"asset_bank":accounts[1],"liab_bank":accounts[2]}
                k=ident(r)
                if k in seen:
                    errors.append({"reason":"duplicate_identity","identity":k});continue
                seen.add(k);rows.append(r)
        if last is None:
            current=request_to+1
        else:
            if last<current:raise RuntimeError("non_advancing_stream")
            current=max(last+1,request_to+1)

    if errors:blocked("scan_integrity",errors[:200],error_count=len(errors),request_count=requests)

    banks=rpc_banks([r["asset_bank"] for r in rows]+[r["liab_bank"] for r in rows])
    for r in rows:
        a=banks.get(r["asset_bank"]);l=banks.get(r["liab_bank"])
        if not a or not l:blocked("bank_mapping",ident(r))
        r["asset_mint"]=a["mint"];r["asset_decimals"]=a["decimals"]
        r["liab_mint"]=l["mint"];r["liab_decimals"]=l["decimals"]

    rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
    with ROWS.open("w") as fh:
        for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

    sol=[r for r in rows if r["asset_mint"]==SOL]
    lc={}
    for r in sol:lc[r["liab_mint"]]=lc.get(r["liab_mint"],0)+1
    top=sorted(lc.items(),key=lambda kv:(-kv[1],kv[0]))
    usdc=sum(1 for r in sol if r["liab_mint"]==USDC);usdt=sum(1 for r in sol if r["liab_mint"]==USDT)
    rec={"schema_version":"0.1","classification":"MARGINFI_2025_Q1_LIABILITY_REGIME_MONTH_PASS",
      "authority":"MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_FREEZE_V0.1.md","month":M,
      "window_start":START,"window_end":END,"successful_marginfi_liquidation_count":len(rows),
      "sol_collateral_event_count":len(sol),"distinct_liability_mint_count":len(lc),
      "usdc_liability_count":usdc,"usdc_liability_share":usdc/len(sol) if sol else None,
      "usdt_liability_count":usdt,"usdt_liability_share":usdt/len(sol) if sol else None,
      "usdc_usdt_combined_count":usdc+usdt,"usdc_usdt_combined_share":(usdc+usdt)/len(sol) if sol else None,
      "liability_top10":top[:10],
      "liability_top1_share":top[0][1]/len(sol) if sol and top else None,
      "liability_top3_share":sum(n for _,n in top[:3])/len(sol) if sol else None,
      "duplicate_identity_count":0,"error_count":0,"request_count":requests,
      "termination_evidence":termination,"rows_file":str(ROWS),
      "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
                  "funding_2025_opened":False,"market_direction_2025_opened":False,
                  "prices_2026_opened":False,"returns_2026_opened":False,"token_amounts":False,
                  "oracle_values":False,"live_trading":False,"orders":False,"wallets":False,
                  "exchange_mutation":False,"merge_main":False}}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True))
except SystemExit:raise
except Exception as e:
    blocked("exception",f"{type(e).__name__}:{e}")

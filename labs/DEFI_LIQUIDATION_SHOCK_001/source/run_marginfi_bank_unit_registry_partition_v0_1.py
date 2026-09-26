#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
D8="0xd6a997d5fba756db"
PREFIX="d6a997d5fba756db"
LOWER="2023-02-07T15:47:04Z"
UPPER="2025-01-01T00:00:00Z"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw
def iso_dt(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm_ts(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def addr_key(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def key(sig,addr): return ("marginfi","lending_account_liquidate",sig,addr_key(addr))

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-marginfi-bank-unit/0.1"}
    if data is not None: headers["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code}; time.sleep(min(60,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}; time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    st,h,raw=req(f"{TSROOT}/{int(iso_dt(s).timestamp())}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}")
    obj=json.loads(raw)
    if isinstance(obj,int): return obj
    if isinstance(obj,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(obj.get(k),int): return obj[k]
    raise RuntimeError("timestamp_resolver_schema")

def load_baseline(root,start,end):
    lo=iso_dt(start); hi=iso_dt(end); out={}; anomalies=[]
    for p in sorted(Path(root).rglob("*.json")):
        try:
            with p.open("r",encoding="utf-8") as fh:o=json.load(fh)
        except Exception: continue
        rows=o.get("rows")
        if not isinstance(rows,list): continue
        for r in rows:
            if r.get("protocol")!="marginfi": continue
            if r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION": continue
            try:t=iso_dt(r.get("timestamp"))
            except Exception:
                anomalies.append({"reason":"baseline_bad_timestamp","signature":r.get("signature")}); continue
            if not (lo<=t<hi): continue
            sig=r.get("signature"); addr=r.get("instructionAddress")
            if not isinstance(sig,str) or not sig or not isinstance(addr,list):
                anomalies.append({"reason":"baseline_bad_identity","signature":sig}); continue
            k=key(sig,addr)
            if k in out and out[k]!=r: anomalies.append({"reason":"baseline_duplicate_conflict","signature":sig,"instructionAddress":addr})
            out[k]=r
    return out,anomalies

def pair_from_tb(tb):
    pairs=set()
    if isinstance(tb.get("preMint"),str) and isinstance(tb.get("preDecimals"),int):
        pairs.add((tb["preMint"],int(tb["preDecimals"])))
    if isinstance(tb.get("postMint"),str) and isinstance(tb.get("postDecimals"),int):
        pairs.add((tb["postMint"],int(tb["postDecimals"])))
    return pairs

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True)
ap.add_argument("--baseline",required=True);ap.add_argument("--partition-id",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args()
start=max(iso_dt(args.start),iso_dt(LOWER)).isoformat().replace("+00:00","Z")
end=min(iso_dt(args.end),iso_dt(UPPER)).isoformat().replace("+00:00","Z")
baseline,banom=load_baseline(args.baseline,start,end)

lo=iso_dt(start); hi=iso_dt(end); lo_ts=int(lo.timestamp()); hi_ts=int(hi.timestamp())
current=ts_slot(start); to_slot=ts_slot(end)+16
seen={}; obs={}; asset_banks=set(); liab_banks=set(); metadata_missing=[]; conflicts=[]; reqs=0; terms=[]
while current<=to_slot:
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True},
                    "tokenBalance":{"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True}},
          "instructions":[{"programId":[PROGRAM],"d8":[D8],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}]}
    st,h,raw=req(STREAM,body);reqs+=1
    if st==204:
        terms.append({"http_status":204,"from_slot":current});break
    if st!=200:raise RuntimeError(f"stream_http_{st}")
    lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    if not lines:
        terms.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON"});break
    batch=[json.loads(x) for x in lines]; last=None
    for b in batch:
        hdr=b.get("header") or {};slot=hdr.get("number");ts=norm_ts(hdr.get("timestamp"))
        if isinstance(slot,int): last=slot if last is None else max(last,slot)
        if ts is None:continue
        try:bt=int(iso_dt(ts).timestamp())
        except Exception:continue
        if not (lo_ts<=bt<hi_ts):continue
        tbmap={}
        for tb in b.get("tokenBalances") or []:
            a=tb.get("account")
            if a:tbmap.setdefault(a,set()).update(pair_from_tb(tb))
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:continue
            if not dec.startswith(bytes.fromhex(PREFIX)):continue
            tx=tx_by.get(ix.get("transactionIndex"))
            if not isinstance(tx,dict) or tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            addr=ix.get("instructionAddress");accts=ix.get("accounts") or []
            if not sig or not isinstance(addr,list) or len(accts)<10:
                conflicts.append({"reason":"bad_identity_or_accounts","signature":sig,"account_count":len(accts)});continue
            k=key(sig,addr)
            if k in seen:conflicts.append({"reason":"duplicate_enriched_key","signature":sig,"instructionAddress":addr})
            seen[k]={"signature":sig,"instructionAddress":addr}
            asset=accts[1];liab=accts[2];vault=accts[7]
            asset_banks.add(asset);liab_banks.add(liab)
            pairs=sorted(tbmap.get(vault,set()))
            if len(pairs)!=1:
                metadata_missing.append({"signature":sig,"instructionAddress":addr,"liab_bank":liab,"liquidity_vault":vault,
                                         "observed_pairs":[{"mint":m,"decimals":d} for m,d in pairs]})
            else:
                pair=pairs[0]
                prev=obs.get(liab)
                if prev is not None and prev!=pair:
                    conflicts.append({"reason":"bank_unit_conflict","liab_bank":liab,"prior":{"mint":prev[0],"decimals":prev[1]},
                                      "new":{"mint":pair[0],"decimals":pair[1]}})
                obs[liab]=pair
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1

missing=sorted(set(baseline)-set(seen));extra=sorted(set(seen)-set(baseline))
passed=(not banom and not conflicts and not metadata_missing and not missing and not extra)

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"marginfi",
 "partition_id":args.partition_id,"effective_start":start,"effective_end":end,
 "classification":"MARGINFI_BANK_UNIT_REGISTRY_PARTITION_PASS" if passed else "MARGINFI_BANK_UNIT_REGISTRY_PARTITION_FAIL_CLOSED",
 "baseline_success_count":len(baseline),"enriched_success_count":len(seen),
 "missing_count":len(missing),"extra_count":len(extra),"baseline_anomaly_count":len(banom),
 "metadata_missing_event_count":len(metadata_missing),"conflict_count":len(conflicts),
 "asset_banks":sorted(asset_banks),"liab_banks":sorted(liab_banks),
 "liability_bank_unit_observations":[{"bank":b,"mint":p[0],"decimals":p[1]} for b,p in sorted(obs.items())],
 "metadata_missing_examples":metadata_missing[:100],"conflict_examples":conflicts[:100],
 "request_count":reqs,"termination_evidence":terms,
 "amount_fields_requested":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["partition_id","classification","baseline_success_count","enriched_success_count",
 "missing_count","extra_count","metadata_missing_event_count","conflict_count"]},indent=2))
if not passed:raise SystemExit(2)

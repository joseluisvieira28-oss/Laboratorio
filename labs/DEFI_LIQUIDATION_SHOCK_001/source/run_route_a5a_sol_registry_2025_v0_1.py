#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, time, urllib.request, urllib.error
from collections import defaultdict
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
SOL="So11111111111111111111111111111111111111112"
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
OUT=Path("route_a5a_registry")

MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
KAMINO="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
SOLEND="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"

HIST={
 "marginfi:asset_bank":{
   "BpmLoZcyKJP9Jncq5TE7TTzxPV6PSbKNZkuvU1MB6t8e",
   "CCKtUs6Cgwo4aaQUmBPmyoApH2gUDErxNZCAntD6LYGh"},
 "save0c:withdraw_reserve":{
   "3WPYWiZtc2uJq1JiF3Z3KswicFAp5VrFgEHwP3CkuDUn",
   "7trBAMkVU8dcPQVdScz7VNywZwqnD1rwXkwkVPQJ95bT",
   "8xogd14bBxBdGKDfkDciPPp6pZ3Cw4Yj5USRbGJDbZpA",
   "UTABCRXirrbpCNDogCoqEECtM3V44jXGCsK23ZepV3Z"},
 "kamino:withdraw_reserve_liquidity_supply":{
   "GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U"},
 "save11:withdraw_reserve_liquidity_supply":{
   "8UviNr47S8eLJ3WfDxMRa3hvLta1VDJwNWqsDgtN3Cv".replace("LJ3","L6J3"),
   "5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY",
   "8jVVXXxzC9N5FeHUxKBgXLM8xARzLpnzXz8dqZHzpykY",
   "APJAFijv9XrtnrAvktzsqgJboq4Uhs3mu7YN7DQ5bFMH",
   "6ToFgS59GXhYMoHHL2GNPh5aNypxc1UAR1RYpfdHftBE",
   "6s8hmMLgdhpffsL7H9neZBhFSxaQYTnQ1gkjaRN25GS7"}
}

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def iso(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-a5a-registry/0.1"}
    if data is not None:h["Content-Type"]="application/json"
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last=f"http_{e.code}";time.sleep(min(60,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last=f"{type(e).__name__}:{str(e)[:160]}";time.sleep(min(60,2**i))
    raise RuntimeError("transport_exhausted:"+str(last))

def ts_slot(s):
    st,h,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    x=json.loads(raw)
    if isinstance(x,int):return x
    if isinstance(x,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(x.get(k),int):return x[k]
    raise RuntimeError("timestamp_resolver_schema")

def scan(name,program,start_s,end_s,filter_extra,decoder):
    lo,hi=iso(start_s),iso(end_s)
    current=ts_slot(start_s);to=ts_slot(end_s)+16
    rows=[];requests=0;terms=[];errors=[];seen=set()
    while current<=to:
        filt={"programId":[program],"isCommitted":True,"transaction":True,**filter_extra}
        body={"type":"solana","fromBlock":current,"toBlock":to,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True}},
          "instructions":[filt]}
        st,h,raw=req(STREAM,body);requests+=1
        if st==204:
            terms.append({"http_status":204,"from_slot":current});break
        if st!=200:
            errors.append({"reason":"stream_http","status":st,"body_sha256":hashlib.sha256(raw).hexdigest()});break
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines:
            terms.append({"http_status":200,"from_slot":current,"reason":"EMPTY_NDJSON"});break
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
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=program:continue
                ti=ix.get("transactionIndex");tx=tx_by.get(ti)
                if not isinstance(tx,dict) or tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
                sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                addr=ix.get("instructionAddress");accounts=ix.get("accounts") or [];data=ix.get("data") or ""
                if not sig or not isinstance(addr,list):
                    errors.append({"reason":"bad_identity","slot":slot});continue
                ident=(sig,tuple(addr))
                if ident in seen:continue
                seen.add(ident)
                try:r=decoder(accounts,data,ts,sig,addr,slot)
                except Exception as e:
                    errors.append({"reason":"decoder_error","signature":sig,"slot":slot,"detail":str(e)[:200]});continue
                if r is not None:rows.append(r)
        if last is None:
            errors.append({"reason":"no_block_number","from_slot":current});break
        if last<current:
            errors.append({"reason":"non_advancing_stream","current":current,"last":last});break
        current=last+1
    return {"name":name,"start":start_s,"end":end_s,"request_count":requests,
            "termination":terms,"rows":rows,"errors":errors}

def anchor_decoder(expected_hex,mint_i,role_outputs):
    exp=bytes.fromhex(expected_hex)
    def dec(accounts,data,ts,sig,addr,slot):
        raw=b58decode(data)
        if not raw.startswith(exp):return None
        need=max([mint_i]+[i for _,_,i in role_outputs])
        if len(accounts)<=need:raise RuntimeError(f"account_shape:{len(accounts)}<={need}")
        mint=accounts[mint_i]
        return {"timestamp":ts,"signature":sig,"instructionAddress":addr,"slot":slot,
                "mint":mint,"is_sol":mint==SOL,
                "roles":[{"protocol":p,"role":r,"account":accounts[i]} for p,r,i in role_outputs]}
    return dec

def solend_decoder(accounts,data,ts,sig,addr,slot):
    raw=b58decode(data)
    if not raw or raw[0]!=2:return None
    if len(accounts)<17:raise RuntimeError(f"account_shape:{len(accounts)}<17")
    mint=accounts[3]
    return {"timestamp":ts,"signature":sig,"instructionAddress":addr,"slot":slot,
            "mint":mint,"is_sol":mint==SOL,
            "roles":[
              {"protocol":"save0c","role":"withdraw_reserve","account":accounts[2]},
              {"protocol":"save11","role":"withdraw_reserve_liquidity_supply","account":accounts[4]}]}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    scans=[]
    # Marginfi exact creation instructions.
    scans.append(scan("marginfi_add_bank",MARGINFI,"2023-02-07T15:47:04Z","2026-01-01T00:00:00Z",
      {"d8":["0xd744484ed0da67b6"]},anchor_decoder("d744484ed0da67b6",5,[("marginfi","asset_bank",6)])))
    scans.append(scan("marginfi_add_bank_with_seed",MARGINFI,"2023-02-07T15:47:04Z","2026-01-01T00:00:00Z",
      {"d8":["0x4cd3d5ab754e9e4c"]},anchor_decoder("4cd3d5ab754e9e4c",5,[("marginfi","asset_bank",6)])))
    scans.append(scan("marginfi_add_bank_permissionless",MARGINFI,"2023-02-07T15:47:04Z","2026-01-01T00:00:00Z",
      {"d8":["0x7fbb7922bba7ee66"]},anchor_decoder("7fbb7922bba7ee66",3,[("marginfi","asset_bank",8)])))
    # Kamino reserve creation.
    scans.append(scan("kamino_init_reserve",KAMINO,"2023-11-17T14:48:24Z","2026-01-01T00:00:00Z",
      {"d8":["0x8af547e19904032b"]},anchor_decoder("8af547e19904032b",4,[("kamino","withdraw_reserve_liquidity_supply",5)])))
    # Solend/Save reserve creation. SQD byte-1 data filter is frozen as d1.
    scans.append(scan("solend_init_reserve",SOLEND,"2021-12-08T00:00:00Z","2026-01-01T00:00:00Z",
      {"d1":["0x02"]},solend_decoder))

    errors=[]
    for s in scans:
        if s["errors"]:errors.extend([{"scan":s["name"],**e} for e in s["errors"]])
        if not s["termination"]:errors.append({"scan":s["name"],"reason":"missing_termination_evidence"})

    discovered=defaultdict(set);provenance=[]
    for s in scans:
        for r in s["rows"]:
            if not r["is_sol"]:continue
            for z in r["roles"]:
                k=f'{z["protocol"]}:{z["role"]}'
                discovered[k].add(z["account"])
                provenance.append({"scan":s["name"],"timestamp":r["timestamp"],"signature":r["signature"],
                                   "slot":r["slot"],"protocol":z["protocol"],"role":z["role"],
                                   "account":z["account"],"mint":r["mint"]})

    final={}
    historical_retained=True
    for k,hset in HIST.items():
        union=set(hset)|set(discovered.get(k,set()))
        final[k]=sorted(union)
        if not set(hset).issubset(union):historical_retained=False

    required=[
      "marginfi:asset_bank","save0c:withdraw_reserve",
      "kamino:withdraw_reserve_liquidity_supply","save11:withdraw_reserve_liquidity_supply"]
    gates={
      "all_scans_terminated_without_errors":not errors,
      "all_13_historical_accounts_retained":historical_retained and sum(len(v) for v in HIST.values())==13,
      "all_required_roles_nonempty":all(len(final.get(k,[]))>0 for k in required),
      "upper_boundary_2026_01_01":all(s["end"]=="2026-01-01T00:00:00Z" for s in scans)
    }
    classification="SOL_ROLE_ACCOUNT_REGISTRY_2025_PASS" if all(gates.values()) else "SOL_ROLE_ACCOUNT_REGISTRY_2025_BLOCKED"
    stable={"final_registry":final,"provenance":sorted(provenance,key=lambda x:(x["protocol"],x["role"],x["account"],x["timestamp"],x["signature"]))}
    receipt={"schema_version":"0.1","lab_id":LAB,"classification":classification,
      "sol_mint":SOL,"scans":[{k:v for k,v in s.items() if k!="rows"}|{"matching_creation_count":len(s["rows"]),"sol_creation_count":sum(1 for r in s["rows"] if r["is_sol"])} for s in scans],
      "historical_registry":{k:sorted(v) for k,v in HIST.items()},
      "discovered_registry":{k:sorted(v) for k,v in discovered.items()},
      "final_registry":final,"final_unique_account_count":len(set(a for xs in final.values() for a in xs)),
      "provenance":provenance,"error_count":len(errors),"errors":errors,"gates":gates,
      "registry_identity_sha256":hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
      "firewall":{"protected_2025_prices_opened":False,"protected_2025_returns_opened":False,
                  "protected_2025_pnl_opened":False,"protected_2026_outcomes_opened":False,
                  "market_data_read":False,"prices_read":False,"purchases":False,"trading":False,
                  "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False},
      "trading_authority":"NONE"}
    (OUT/"DLS_ROUTE_A5A_SOL_ROLE_ACCOUNT_REGISTRY_2025_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,
      "final_registry_counts":{k:len(v) for k,v in final.items()},
      "discovered_registry_counts":{k:len(v) for k,v in discovered.items()},
      "final_unique_account_count":receipt["final_unique_account_count"],
      "error_count":len(errors),"gates":gates,"registry_identity_sha256":receipt["registry_identity_sha256"]},indent=2,sort_keys=True),flush=True)
    if classification!="SOL_ROLE_ACCOUNT_REGISTRY_2025_PASS":raise SystemExit(2)

if __name__=="__main__":main()

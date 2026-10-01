#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,datetime as dt,hashlib,json,os,time,urllib.request,urllib.error,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_alternative_source_equivalence_v0_1 as eq

LAB="DEFI-LIQUIDATION-SHOCK-001"
START=1735689600  # 2025-01-01T00:00:00Z
END=1767225600    # 2026-01-01T00:00:00Z
SOL="So11111111111111111111111111111111111111112"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
CFG=eq.cfg()
GROUPS={"marginfi":["marginfi"],"solend":["save0c","save11"],"kamino":["kamino"]}

def b58e(b):
    n=int.from_bytes(b,"big");s=""
    while n:
        n,r=divmod(n,58);s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0:pad+=1
        else:break
    return "1"*pad+(s or ("" if pad else "1"))

class RPC:
    def __init__(self):
        key=os.environ.get("HELIUS_API_KEY")
        if not key: raise RuntimeError("HELIUS_API_KEY_ABSENT")
        self.url="https://mainnet.helius-rpc.com/?api-key="+key
        self.calls=0
    def call(self,method,params,retries=6):
        if method not in ("getSignaturesForAddress","getTransaction","getMultipleAccounts"):
            raise RuntimeError("unauthorized_method")
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
        last=None
        for i in range(retries):
            try:
                req=urllib.request.Request(self.url,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-DLS-A2-2025/0.1"})
                with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
                self.calls+=1
                o=json.loads(raw)
                if o.get("error"): raise RuntimeError("rpc_error:"+str(o["error"].get("code")))
                return o.get("result")
            except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,RuntimeError) as e:
                last=type(e).__name__
                time.sleep(min(20,1.5*(i+1)))
        raise RuntimeError("rpc_exhausted:"+str(last))
    def batch_transactions(self,sigs,batch=40):
        out={}
        for i in range(0,len(sigs),batch):
            chunk=sigs[i:i+batch]
            payload=[{"jsonrpc":"2.0","id":j+1,"method":"getTransaction",
                      "params":[sig,{"encoding":"json","commitment":"finalized","maxSupportedTransactionVersion":0}]}
                     for j,sig in enumerate(chunk)]
            raw=json.dumps(payload,separators=(",",":")).encode()
            last=None
            for k in range(6):
                try:
                    req=urllib.request.Request(self.url,data=raw,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-DLS-A2-2025/0.1"})
                    with urllib.request.urlopen(req,timeout=90) as r: body=r.read()
                    self.calls+=1
                    arr=json.loads(body)
                    byid={int(x["id"]):x for x in arr}
                    for j,sig in enumerate(chunk):
                        x=byid.get(j+1,{})
                        if x.get("error"): raise RuntimeError("batch_rpc_error")
                        out[sig]=x.get("result")
                    break
                except Exception as e:
                    last=type(e).__name__;time.sleep(min(20,1.5*(k+1)))
            else: raise RuntimeError("batch_rpc_exhausted:"+str(last))
        return out

def scan_signatures(rpc,program):
    cursor=None;seen=set();candidates=[];pages=[];lower=False
    while True:
        opts={"limit":1000,"commitment":"finalized"}
        if cursor:opts["before"]=cursor
        rows=rpc.call("getSignaturesForAddress",[program,opts])
        if not isinstance(rows,list):raise RuntimeError("signature_page_schema")
        if not rows: raise RuntimeError("empty_page_before_lower_boundary")
        if any(type(x.get("blockTime")) is not int or not isinstance(x.get("signature"),str) or "err" not in x for x in rows):
            raise RuntimeError("signature_metadata_missing")
        if any(rows[i]["slot"]<rows[i+1]["slot"] for i in range(len(rows)-1)):
            raise RuntimeError("signature_page_order")
        dup=sum(1 for x in rows if x["signature"] in seen)
        if dup:raise RuntimeError("duplicate_signature_pagination")
        for x in rows:seen.add(x["signature"])
        inwin=[x for x in rows if START<=x["blockTime"]<END and x["err"] is None]
        candidates.extend(inwin)
        pages.append({"count":len(rows),"first_slot":rows[0]["slot"],"last_slot":rows[-1]["slot"],
                      "first_time":rows[0]["blockTime"],"last_time":rows[-1]["blockTime"]})
        if rows[-1]["blockTime"]<START:
            lower=True;break
        nxt=rows[-1]["signature"]
        if nxt==cursor:raise RuntimeError("nonadvancing_cursor")
        cursor=nxt
        if len(pages)>500:raise RuntimeError("signature_page_safety_cap_500")
    return candidates,pages,lower

def get_multiple(rpc,keys,offset,length):
    out=[]
    for i in range(0,len(keys),100):
        vals=rpc.call("getMultipleAccounts",[keys[i:i+100],{"encoding":"base64","commitment":"finalized","dataSlice":{"offset":offset,"length":length}}])
        out.extend(vals["value"])
    return out

def month_bounds(m):
    a=dt.datetime(2025,m,1,tzinfo=dt.timezone.utc)
    b=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(2025,m+1,1,tzinfo=dt.timezone.utc)
    return a,b

def ts_iso(sec):return dt.datetime.fromtimestamp(sec,dt.timezone.utc).isoformat().replace("+00:00","Z")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--group",choices=sorted(GROUPS),required=True);ap.add_argument("--outdir",required=True)
    a=ap.parse_args();protos=GROUPS[a.group];outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True)
    program=CFG[protos[0]]["program"]
    if any(CFG[p]["program"]!=program for p in protos):raise RuntimeError("group_program_mismatch")
    rpc=RPC()
    sigmeta,pages,lower=scan_signatures(rpc,program)
    txmap=rpc.batch_transactions([x["signature"] for x in sigmeta])
    meta={x["signature"]:x for x in sigmeta}
    rows={p:[] for p in protos};errors={p:[] for p in protos};seen={p:set() for p in protos}
    normalized=0
    for sig in [x["signature"] for x in sigmeta]:
        raw=txmap.get(sig)
        if raw is None:
            for p in protos:errors[p].append({"reason":"transaction_missing","signature":sig})
            continue
        try:n=eq.normalize(raw);normalized+=1
        except Exception as e:
            # Cannot know relevance if normalization itself fails; fail all protocols sharing the program.
            for p in protos:errors[p].append({"reason":"raw_normalization","signature":sig,"error":type(e).__name__})
            continue
        if n["err"] is not None or n["timestamp"]!=meta[sig]["blockTime"] or n["slot"]!=meta[sig]["slot"]:
            for p in protos:errors[p].append({"reason":"transaction_metadata_conflict","signature":sig})
            continue
        for p,ix in eq.matches(n,CFG):
            if p not in protos:continue
            if ix["path"] is None:
                errors[p].append({"reason":"cpi_path_ambiguous","signature":sig});continue
            if not eq.shape(p,ix):
                errors[p].append({"reason":"canonical_shape","signature":sig,"path":ix["path"]});continue
            key=(sig,json.dumps(ix["path"],separators=(",",":")))
            if key in seen[p]:
                errors[p].append({"reason":"duplicate_identity","signature":sig,"path":ix["path"]});continue
            seen[p].add(key)
            rec={"protocol":p,"instruction_class":CFG[p]["class"],"signature":sig,"instructionAddress":ix["path"],
                 "slot":n["slot"],"timestamp":ts_iso(n["timestamp"]),"account_count":len(ix["accounts"]),"data_length":len(ix["data"])}
            if p=="marginfi":rec["mapping_account"]=ix["accounts"][1]
            elif p=="save0c":rec["mapping_account"]=ix["accounts"][4]
            elif p=="kamino":
                rec["collateral_mint"]=ix["accounts"][8];rec["unit_resolution"]="DIRECT_WITHDRAW_LIQUIDITY_MINT_ACCOUNT"
            elif p=="save11":
                try:pair,opt=eq.unit(n,ix)
                except Exception as e:
                    errors[p].append({"reason":"save11_unit_resolution","signature":sig,"error":type(e).__name__});continue
                if len(pair)!=1:
                    errors[p].append({"reason":"save11_primary_unit_count","signature":sig,"observed":len(pair)});continue
                rec["collateral_mint"],rec["collateral_decimals"]=pair[0]
                rec["unit_resolution"]="PRIMARY_RESERVE_VAULT_TOKEN_BALANCE"
            rows[p].append(rec)
    # Current finalized state mapping is the already-frozen canonical 2025 mapping route.
    if "marginfi" in protos:
        keys=sorted({r["mapping_account"] for r in rows["marginfi"]})
        vals=get_multiple(rpc,keys,8,33);mp={}
        for k,v in zip(keys,vals):
            if v is None or v.get("owner")!=CFG["marginfi"]["program"]:
                errors["marginfi"].append({"reason":"marginfi_bank_missing_or_owner","bank":k});continue
            try:d=base64.b64decode((v.get("data") or [""])[0])
            except Exception:errors["marginfi"].append({"reason":"marginfi_bank_decode","bank":k});continue
            if len(d)!=33:errors["marginfi"].append({"reason":"marginfi_bank_slice_len","bank":k});continue
            mp[k]=(b58e(d[:32]),int(d[32]))
        for r in rows["marginfi"]:
            if r["mapping_account"] in mp:
                r["collateral_mint"],r["collateral_decimals"]=mp[r["mapping_account"]]
                r["unit_resolution"]="FINALIZED_BANK_DATASLICE_8_33"
    if "save0c" in protos:
        keys=sorted({r["mapping_account"] for r in rows["save0c"]})
        vals1=get_multiple(rpc,keys,42,33);vals2=get_multiple(rpc,keys,227,32);mp={}
        for k,v1,v2 in zip(keys,vals1,vals2):
            if v1 is None or v2 is None or v1.get("owner")!=CFG["save0c"]["program"] or v2.get("owner")!=CFG["save0c"]["program"]:
                errors["save0c"].append({"reason":"save0c_reserve_missing_or_owner","reserve":k});continue
            try:d1=base64.b64decode((v1.get("data") or [""])[0]);d2=base64.b64decode((v2.get("data") or [""])[0])
            except Exception:errors["save0c"].append({"reason":"save0c_reserve_decode","reserve":k});continue
            if len(d1)!=33 or len(d2)!=32:errors["save0c"].append({"reason":"save0c_reserve_slice_len","reserve":k});continue
            mp[k]=(b58e(d1[:32]),int(d1[32]),b58e(d2))
        for r in rows["save0c"]:
            if r["mapping_account"] in mp:
                r["collateral_mint"],r["collateral_decimals"],r["collateral_token_mint"]=mp[r["mapping_account"]]
                r["unit_resolution"]="FINALIZED_RESERVE_DATASLICE_42_33"
    for p in protos:
        unresolved=sum(1 for r in rows[p] if not r.get("collateral_mint"))
        if unresolved:errors[p].append({"reason":"unresolved_collateral_mint","count":unresolved})
        for m in range(1,13):
            lo,hi=month_bounds(m)
            rr=[r for r in rows[p] if lo.timestamp()<=dt.datetime.fromisoformat(r["timestamp"].replace("Z","+00:00")).timestamp()<hi.timestamp()]
            classification="PROTECTED_2025_PROTOCOL_SOURCE_PASS" if lower and not errors[p] else "PROTECTED_2025_PROTOCOL_SOURCE_BLOCKED"
            receipt={"schema_version":"0.1","lab_id":LAB,"protocol":p,"instruction_class":CFG[p]["class"],
              "window_start":lo.isoformat().replace("+00:00","Z"),"window_end":hi.isoformat().replace("+00:00","Z"),
              "classification":classification,"successful_instruction_count":len(rr),
              "unique_collateral_mint_count":len({x.get("collateral_mint") for x in rr if x.get("collateral_mint")}),
              "sol_collateral_event_count":sum(1 for x in rr if x.get("collateral_mint")==SOL),
              "duplicate_count":0,"error_count":len(errors[p]),"duplicates":[],"errors":errors[p][:200],
              "request_count":rpc.calls,"termination_evidence":{"lower_2025_boundary_reached":lower,"signature_pages":len(pages),
                "annual_successful_program_signatures":len(sigmeta),"annual_normalized_transactions":normalized},
              "rows":rr,"source_route":"HELIUS_ARCHIVAL_RAW_A2_EQUIVALENT",
              "equivalence_run_id":36900517788,"equivalence_artifact_id":11181427969,
              "firewall":{"prices_2025":False,"returns_2025":False,"pnl_2025":False,"funding_2025":False,
                "market_direction_2025":False,"prices_2026":False,"returns_2026":False,"token_amounts":False,
                "oracle_values":False,"post_outcome_tuning":False,"live_trading":False,"orders":False,"wallets":False,
                "exchange_mutation":False,"merge_main":False}}
            (outdir/f"{p}-2025{m:02d}.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    summary={"group":a.group,"protocols":protos,"signature_pages":len(pages),"successful_2025_program_signatures":len(sigmeta),
             "normalized_transactions":normalized,"rpc_http_calls":rpc.calls,
             "rows":{p:len(rows[p]) for p in protos},"errors":{p:len(errors[p]) for p in protos},
             "lower_boundary_reached":lower,"trading_authority":"NONE"}
    (outdir/f"A2_{a.group.upper()}_SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    if not lower or any(errors[p] for p in protos):raise SystemExit(2)

if __name__=="__main__":main()
